#!/usr/bin/env python3
"""Publish an expert-agent bundle to the newb marketplace.

Standalone (stdlib only, no ``newb`` import) so an expert can run it from an
installed plugin without the newb repo or CLI. Tars the bundle directory and
POSTs it to the hosted executor's ``/agents`` ingest endpoint, where it is
installed and served at ``<host>/mcp/<slug>``.

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


def _post(url: str, data: bytes, content_type: str) -> dict:
    req = urllib.request.Request(
        url, data=data, headers={"content-type": content_type}, method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:  # surface the server's message
        body = e.read().decode(errors="replace")[:400]
        sys.exit(f"publish failed: HTTP {e.code} {body}")
    except urllib.error.URLError as e:
        sys.exit(f"publish failed: could not reach {url} ({e.reason})")


def main() -> None:
    ap = argparse.ArgumentParser(description="Publish a bundle to the newb marketplace.")
    ap.add_argument("bundle_dir", help="path to the agent bundle directory")
    ap.add_argument("--host", default=DEFAULT_HOST, help="marketplace host (default: hosted executor)")
    ap.add_argument(
        "--configure-platform",
        action="store_true",
        help="also configure the agent to run on the platform LLM (for an immediate test)",
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
    print(f"✓ published '{slug}'  ->  {json.dumps(result)}")
    print(f"  hosted MCP endpoint: {host}/mcp/{slug}")

    if args.configure_platform:
        cfg = json.dumps({"llm_provider": "platform", "llm_model": args.model}).encode()
        conf = _post(f"{host}/agents/{slug}/config", cfg, "application/json")
        print(f"  configured (platform / {args.model}): {json.dumps(conf)}")
        print(f"  ready — pull it from Claude/Codex at {host}/mcp/{slug}")
    else:
        print("  next: configure its LLM (provider/model/key) before it can run —")
        print("  either re-run with --configure-platform, or set it on the newb configure page.")


if __name__ == "__main__":
    main()
