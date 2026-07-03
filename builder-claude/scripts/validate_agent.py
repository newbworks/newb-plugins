#!/usr/bin/env python3
"""Validate an expert-agent bundle and print its derived A2A Agent Card.

Uses the real loader (newb.marketplace.bundle) so validation matches what
the executor enforces at publish time. Also flags leftover [TODO …]
placeholders.

    python3 validate_agent.py <bundle-dir>
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Bootstrap sys.path to the repo root so `newb` imports resolve when this
# is run from anywhere.
REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def find_todos(root: Path) -> list[str]:
    hits: list[str] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in {".md", ".json"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for i, line in enumerate(text.splitlines(), 1):
            if "[TODO" in line or "TODO-tool-name" in line or "TODO_API_KEY" in line:
                hits.append(f"{path.relative_to(root)}:{i}: {line.strip()}")
    return hits


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: validate_agent.py <bundle-dir>", file=sys.stderr)
        return 2

    root = Path(sys.argv[1])

    try:
        from newb.marketplace.bundle import BundleError, load_bundle
    except ImportError as exc:  # pragma: no cover - environment issue
        print(f"error: could not import newb.marketplace.bundle: {exc}", file=sys.stderr)
        print("Run from the newb repo (or ensure it is on PYTHONPATH).", file=sys.stderr)
        return 2

    try:
        bundle = load_bundle(root)
    except BundleError as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        return 1

    todos = find_todos(root)
    if todos:
        print("INVALID: unfilled placeholders remain:", file=sys.stderr)
        for t in todos:
            print(f"  {t}", file=sys.stderr)
        return 1

    m = bundle.manifest
    print(f"OK: {m.display_name} ({m.name}) v{m.version}")
    print(f"  skills: {', '.join(s.id for s in m.skills) or '(none)'}")
    print(f"  mcp servers: {', '.join(bundle.mcp_servers) or '(none)'}")
    print(f"  price: {m.price_credits} credits/run  ·  free grant: {m.free_credits_grant}")
    print("\nDerived A2A Agent Card:")
    print(json.dumps(
        bundle.agent_card(url="https://gateway.newb.works/a2a/" + m.name), indent=2
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
