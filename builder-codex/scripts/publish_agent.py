#!/usr/bin/env python3
"""Publish an expert-agent bundle to the newb marketplace.

Building is local and needs no auth. Publishing signs you in (OAuth, in your
browser) and uploads the bundle through the newb lobby, which stages it on the
executor for you — so you never hold a shared token. Finish on the configure
page it prints to go live.

  python3 publish_agent.py ./agents/<name>             # sign in + upload (default)
  python3 publish_agent.py ./agents/<name> --token T   # legacy: direct executor push (CI)

Stdlib only, so it runs from an installed plugin with no repo or CLI.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
import os
import secrets
import sys
import tarfile
import tempfile
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

DEFAULT_HOST = "https://agents.newb.works"
DEFAULT_LOBBY = "https://marketplace.newb.works"


def _tar_bundle(d: Path) -> bytes:
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tf:
        tf.add(str(d), arcname=".")
    return buf.getvalue()


def _post(url: str, data: bytes, content_type: str, token: str | None = None) -> dict:
    headers = {"content-type": content_type}
    if token:
        headers["authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            return json.loads(r.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")[:400]
        sys.exit(f"request failed: HTTP {e.code} {body}  ({url})")
    except urllib.error.URLError as e:
        sys.exit(f"request failed: could not reach {url} ({e.reason})")


def _b64url(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()


# ── OAuth sign-in (RFC 8252 loopback + PKCE) ──────────────────────────

class _CallbackHandler(BaseHTTPRequestHandler):
    result: dict = {}

    def do_GET(self):  # noqa: N802
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path != "/callback":
            self.send_response(404)
            self.end_headers()
            return
        _CallbackHandler.result = {
            k: v[0] for k, v in urllib.parse.parse_qs(parsed.query).items()
        }
        self.send_response(200)
        self.send_header("content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"<html><body><h3>Signed in to newb.</h3>"
                         b"You can close this tab and return to your terminal.</body></html>")

    def log_message(self, *_a):  # silence the default request logging
        return


def _oauth_login(lobby: str) -> str:
    """Run the browser OAuth loopback flow; return an access token."""
    server = HTTPServer(("127.0.0.1", 0), _CallbackHandler)
    redirect_uri = f"http://127.0.0.1:{server.server_address[1]}/callback"

    # 1) Dynamic client registration (public client, loopback redirect).
    reg = _post(
        f"{lobby}/api/oauth/register",
        json.dumps({"redirect_uris": [redirect_uri], "client_name": "newb-builder"}).encode(),
        "application/json",
    )
    client_id = reg["client_id"]

    # 2) PKCE + state.
    verifier = _b64url(secrets.token_bytes(48))
    challenge = _b64url(hashlib.sha256(verifier.encode()).digest())
    state = secrets.token_urlsafe(16)
    authorize_url = f"{lobby}/api/oauth/authorize?" + urllib.parse.urlencode({
        "response_type": "code", "client_id": client_id, "redirect_uri": redirect_uri,
        "code_challenge": challenge, "code_challenge_method": "S256",
        "state": state, "scope": "",
    })

    # 3) Open the browser; serve loopback requests until the callback arrives.
    _CallbackHandler.result = {}

    def _serve():
        while not _CallbackHandler.result:
            server.handle_request()  # blocks per request; favicon/etc. loop back

    threading.Thread(target=_serve, daemon=True).start()
    print("Sign in to publish — opening your browser:")
    print(f"  {authorize_url}\n")
    try:
        webbrowser.open(authorize_url)
    except Exception:  # noqa: BLE001 — headless: the URL above is the fallback
        pass

    deadline = time.time() + 300
    while not _CallbackHandler.result and time.time() < deadline:
        time.sleep(0.3)
    res = _CallbackHandler.result
    try:
        server.server_close()
    except Exception:  # noqa: BLE001
        pass

    if not res:
        sys.exit("sign-in timed out. Re-run and complete the browser sign-in.")
    if res.get("error"):
        sys.exit(f"sign-in failed: {res['error']}")
    if res.get("state") != state:
        sys.exit("sign-in failed: state mismatch (possible tampering).")
    if not res.get("code"):
        sys.exit("sign-in failed: no authorization code returned.")

    # 4) Exchange the code for an access token.
    tok = _post(
        f"{lobby}/api/oauth/token",
        json.dumps({
            "grant_type": "authorization_code", "code": res["code"],
            "redirect_uri": redirect_uri, "client_id": client_id,
            "code_verifier": verifier,
        }).encode(),
        "application/json",
    )
    if not tok.get("access_token"):
        sys.exit(f"sign-in failed: no access token ({tok})")
    return tok["access_token"]


# ── version-control guard ─────────────────────────────────────────────
# Publishing uploads the bundle straight to the hosted executor — it does NOT
# go through git. A bundle with uncommitted changes would ship code that has
# no version-controlled source on YOUR side. (The marketplace also archives
# the exact staged source server-side, but your own repo is the copy you
# control.) So: commit first, or pass --allow-dirty to override.

def _git_state(d: Path) -> tuple:
    """(in_git, dirty_paths) for the bundle dir. Never raises — no git binary
    or not-a-repo just yields (False, [])."""
    import subprocess
    try:
        r = subprocess.run(["git", "-C", str(d), "rev-parse", "--is-inside-work-tree"],
                           capture_output=True, text=True, timeout=10)
        if r.returncode != 0 or r.stdout.strip() != "true":
            return (False, [])
        s = subprocess.run(["git", "-C", str(d), "status", "--porcelain", "--", "."],
                           capture_output=True, text=True, timeout=10)
        return (True, [ln[3:] for ln in s.stdout.splitlines() if ln.strip()])
    except Exception:
        return (False, [])


def main() -> None:
    ap = argparse.ArgumentParser(description="Publish a bundle to the newb marketplace.")
    ap.add_argument("bundle_dir", nargs="?", help="path to the agent bundle directory")
    ap.add_argument("--lobby", default=DEFAULT_LOBBY,
                    help="newb lobby base URL (default: marketplace.newb.works)")
    ap.add_argument("--token", default=os.environ.get("NEWB_MARKETPLACE_PUBLISH_TOKEN"),
                    help="(legacy/CI) publish token to push straight to the executor, "
                         "skipping sign-in")
    ap.add_argument("--host", default=DEFAULT_HOST,
                    help="executor host for the --token path")
    ap.add_argument("--allow-dirty", action="store_true",
                    help="publish even if the bundle has uncommitted changes "
                         "(not recommended)")
    # Ticketed publish (works headless — Cowork, SSH, CI). Identity comes from
    # the newb-marketplace MCP connector's OAuth, NOT from this script:
    #   1. --prepare        tar the bundle, print its sha256 + tarball path
    #   2. call the connector tool `request_publish(sha256)` → upload_url
    #      (first use prompts you to connect/sign in — that's the only auth)
    #   3. --upload T URL   POST the saved tarball to the ticket URL
    ap.add_argument("--prepare", action="store_true",
                    help="tar the bundle and print sha256 + tarball path, then stop; "
                         "next: call the connector's request_publish tool")
    ap.add_argument("--upload", nargs=2, metavar=("TARBALL", "UPLOAD_URL"),
                    help="POST a --prepare'd tarball to a request_publish upload URL")
    args = ap.parse_args()

    if args.upload:
        tar_path, url = args.upload
        if not Path(tar_path).is_file():
            sys.exit(f"tarball not found: {tar_path}\n"
                     "run `publish_agent.py <bundle> --prepare` first — the ticket "
                     "binds to those exact bytes, so re-tarring won't match.")
        data = Path(tar_path).read_bytes()
        sha = hashlib.sha256(data).hexdigest()
        result = _post(url, data, "application/gzip")
        slug = result.get("slug", "?")
        print(f"\n✓ staged '{slug}' (hidden — not live yet)  [sha256 {sha[:12]}]")
        if result.get("archived"):
            print(f"  ✓ source archived server-side ({result.get('archive_path', '')})")
        cfg = result.get("configure_url", "")
        print("  Finish on the configure page to publish — set the LLM + pricing:")
        print(f"\n    {cfg}\n")
        return

    if not args.bundle_dir:
        ap.error("bundle_dir is required (except with --upload)")
    d = Path(args.bundle_dir)
    manifest = d / ".codex-plugin" / "plugin.json"
    if not (d / "SKILL.md").is_file() or not manifest.is_file():
        sys.exit(f"not a bundle: {d}\n  need SKILL.md + .codex-plugin/plugin.json")

    in_git, dirty = _git_state(d)
    if not in_git:
        print("warning: this bundle is not in a git repository — its source is not\n"
              "version-controlled on your side. Consider `git init` + commit before\n"
              "publishing, so you always hold the code you shipped.", file=sys.stderr)
    elif dirty and not args.allow_dirty:
        listing = "\n".join(f"  {p}" for p in dirty[:20])
        more = f"\n  … and {len(dirty) - 20} more" if len(dirty) > 20 else ""
        sys.exit("this bundle has uncommitted changes:\n"
                 f"{listing}{more}\n"
                 "commit them first (publishing bypasses git, so uncommitted code would\n"
                 "have no version-controlled source), or re-run with --allow-dirty.")
    slug = json.loads(manifest.read_text(encoding="utf-8"))["name"]
    tar = _tar_bundle(d)
    lobby = args.lobby.rstrip("/")

    if args.prepare:
        # Save the exact bytes (re-tarring later would change the gzip mtime
        # and break the sha the ticket binds to), print what the connector
        # tool needs, and stop.
        out = Path(tempfile.gettempdir()) / f"{slug}-bundle.tar.gz"
        out.write_bytes(tar)
        sha = hashlib.sha256(tar).hexdigest()
        print(f"tarball: {out}")
        print(f"sha256:  {sha}")
        print(f"size:    {len(tar)} bytes")
        print("\nNext: call the newb-marketplace tool  request_publish(sha256=…)")
        print("(first use will prompt you to connect/sign in — that's the only auth)")
        print(f"then:  python3 scripts/publish_agent.py --upload {out} \"<upload_url>\"")
        return

    if args.token:
        # Legacy/CI: push straight to the executor with the shared token.
        host = args.host.rstrip("/")
        result = _post(f"{host}/agents", tar, "application/gzip", token=args.token)
        slug = result.get("agent_id", slug)
        configure_url = f"{lobby}/marketplace/experts/agents/{slug}/configure"
    else:
        # Default: sign in, then upload through the lobby (it stages for you).
        token = _oauth_login(lobby)
        result = _post(f"{lobby}/api/marketplace/agents/upload", tar,
                       "application/gzip", token=token)
        slug = result.get("slug", slug)
        configure_url = (result.get("configure_url")
                         or f"{lobby}/marketplace/experts/agents/{slug}/configure")

    print(f"\n✓ staged '{slug}' (hidden — not live yet)")
    if result.get("archived"):
        where = result.get("archive_path", "the marketplace archive")
        print(f"  ✓ source archived server-side ({where})")
    print("  Finish on the configure page to publish — set the LLM + pricing, then submit:")
    print(f"\n    {configure_url}\n")


if __name__ == "__main__":
    main()
