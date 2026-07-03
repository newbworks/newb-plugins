#!/usr/bin/env python3
"""Stage an expert-agent bundle on the newb marketplace.

Standalone (stdlib only, no ``newb`` import) so an expert can run it from an
installed plugin without the newb repo or CLI. Tars the bundle directory and
POSTs it to the hosted executor's ``/agents`` ingest — which **stages** it
(uploaded but not live). Publishing happens on the **configure page** this
script prints: the expert sets the name, LLM, and any MCP credentials there,
and submitting makes the agent live at ``<host>/mcp/<slug>``.

  python3 publish_agent.py ./agents/<name> [--host URL] [--configure-platform]
"""
from __future__ import annotations

import argparse
import io
import json
import sys
import tarfile
import urllib.error
import urllib.request
from pathlib import Path

DEFAULT_HOST = "https://46-224-211-61.sslip.io"
DEFAULT_CONFIGURE_BASE = "https://lobby.newb.works"


def _post(url: str, data: bytes, content_type: str) -> dict:
    req = urllib.request.Request(
        url, data=data, headers={"content-type": content_type}, method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")[:400]
        sys.exit(f"upload failed: HTTP {e.code} {body}")
    except urllib.error.URLError as e:
        sys.exit(f"upload failed: could not reach {url} ({e.reason})")


def main() -> None:
    ap = argparse.ArgumentParser(description="Stage a bundle on the newb marketplace.")
    ap.add_argument("bundle_dir", help="path to the agent bundle directory")
    ap.add_argument("--host", default=DEFAULT_HOST, help="marketplace host (default: hosted executor)")
    ap.add_argument("--configure-base", default=DEFAULT_CONFIGURE_BASE,
                    help="lobby base URL for the configure page (default: lobby.newb.works)")
    ap.add_argument(
        "--configure-platform",
        action="store_true",
        help="(testing only) skip the configure page and publish now on the platform LLM",
    )
    ap.add_argument("--model", default="claude-opus-4-8", help="model when --configure-platform")
    args = ap.parse_args()

    d = Path(args.bundle_dir)
    manifest = d / ".codex-plugin" / "plugin.json"
    if not (d / "SKILL.md").is_file() or not manifest.is_file():
        sys.exit(f"not a bundle: {d}\n  need SKILL.md + .codex-plugin/plugin.json (run create_agent.py first)")
    slug = json.loads(manifest.read_text(encoding="utf-8"))["name"]

    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tf:
        tf.add(str(d), arcname=".")

    host = args.host.rstrip("/")
    result = _post(f"{host}/agents", buf.getvalue(), "application/gzip")
    configure_url = f"{args.configure_base.rstrip('/')}/marketplace/experts/agents/{slug}/configure"
    print(f"✓ staged '{slug}'  ->  {json.dumps(result)}")

    if args.configure_platform:
        cfg = json.dumps({"llm_provider": "platform", "llm_model": args.model}).encode()
        conf = _post(f"{host}/agents/{slug}/config", cfg, "application/json")
        print(f"  (test) configured platform / {args.model}: {json.dumps(conf)}")
        print(f"  published — live at {host}/mcp/{slug}")
        return

    print("\n  It is STAGED, not live yet.")
    print("  Open the configure page to publish it — sign in, set the name, LLM,")
    print("  and any MCP credentials, then submit. That makes it live:")
    print(f"\n    {configure_url}\n")


if __name__ == "__main__":
    main()
