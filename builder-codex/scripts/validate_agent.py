#!/usr/bin/env python3
"""Validate an expert-agent bundle and print its derived A2A Agent Card.

Runs the SAME checks `newb agent validate` and the `dev_use` MCP tool run —
not a lighter local-only pass. Beyond loading the bundle (the real loader, so
this matches what the executor enforces at publish), that means: leftover
[TODO …] placeholders, SKILL.md compactness, skill id/description coherence,
the v3 publish floor, the v2 service template (intake/duration/rubric/
billing on every skill), rubric compactness, and every pinned model —
`model`, `steps[].model`, `grader_model` — checked against the AI Gateway's
live catalog (retired, unknown, non-language, or missing tool-use support
for a classic tool in an MCP-bearing bundle).

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


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: validate_agent.py <bundle-dir>", file=sys.stderr)
        return 2

    root = Path(sys.argv[1])

    try:
        from newb.marketplace.scaffold import validate_bundle
    except ImportError as exc:  # pragma: no cover - environment issue
        print(f"error: could not import newb.marketplace.scaffold: {exc}", file=sys.stderr)
        print("Run from the newb repo (or ensure it is on PYTHONPATH).", file=sys.stderr)
        return 2

    ok, problems, bundle = validate_bundle(root)
    for p in problems:  # errors + warning:-prefixed advisories, same order validate_bundle found them
        print(p, file=sys.stderr)
    if not ok:
        print("INVALID: bundle is not valid — fix the errors above.", file=sys.stderr)
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
