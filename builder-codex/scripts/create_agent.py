#!/usr/bin/env python3
"""Scaffold a new expert-agent bundle for the newb marketplace.

Standalone (no newb import) so experts can run it anywhere. Writes a
bundle skeleton conforming to docs/marketplace/bundle-spec.md; validate it
afterwards with validate_agent.py.

    python3 create_agent.py <name> [--dir DIR] [--force]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SLUG_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?$")


def titleize(slug: str) -> str:
    return " ".join(w.capitalize() for w in slug.replace("-", " ").split())


def plugin_json(name: str) -> dict:
    return {
        "name": name,
        "category": "[TODO: category, e.g. Career]",
        "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
        "newb": {
            "display_name": titleize(name),
            "description": "[TODO: one sentence — what this agent does for the user]",
            "version": "0.1.0",
            "tags": ["[TODO: tag]"],
            "price_credits": 0,
            "free_credits_grant": 100,
            "skills": [
                {
                    "id": "do_thing",
                    "name": "[TODO: skill name]",
                    "description": "[TODO: what this skill does]",
                    "tags": [],
                }
            ],
        },
    }


SKILL_MD = """\
---
name: {name}
description: [TODO: one-line description]
---

You are **{display}**, an expert agent. [TODO: describe who you are and the
value you provide.]

## What you do

1. [TODO: step one — understand the request; ask a clarifying question if a
   key detail is missing rather than guessing.]
2. [TODO: step two — use your tools to do the work.]
3. [TODO: step three — return a clear, honest result.]

## Style

- Be specific and honest; the user's trust is the product.
- Never invent facts, sources, or results.
- If you cannot complete the request confidently, say what is blocking you
  so the human expert can step in (this powers escalation).
"""

MCP_JSON = {
    "mcpServers": {
        "[TODO-tool-name]": {
            "command": "npx",
            "args": ["-y", "[TODO: mcp package]"],
            "env": {"[TODO_API_KEY]": "${[TODO_API_KEY]}"},
        }
    }
}

EXAMPLE_JSON = [
    {
        "title": "[TODO: example title]",
        "input": "[TODO: a realistic user request]",
        "output": "[TODO: a short summary of what the agent returned]",
    }
]

ASSETS_README = """\
# assets/

Static files shipped inside the bundle and served by the executor.

## Logo (optional)

Drop a logo here (`.png .jpg .jpeg .svg .webp .gif`) and point the manifest at
it:

    "newb": { "logo": "assets/logo.png", ... }

Omit `newb.logo` entirely to use the auto-generated initials mark. You can also
set/replace the logo after publishing on the configure page.
"""


def write(path: Path, content: str, force: bool) -> None:
    if path.exists() and not force:
        print(f"  skip (exists): {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"  wrote: {path}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("name", help="agent slug (lowercase hyphen-case)")
    ap.add_argument("--dir", default=".", help="parent directory (default: .)")
    ap.add_argument("--force", action="store_true", help="overwrite existing files")
    args = ap.parse_args()

    name = args.name.strip().lower()
    if not SLUG_RE.match(name):
        print(
            f"error: name {name!r} must be lowercase hyphen-case (a-z, 0-9, -), "
            "1-64 chars",
            file=sys.stderr,
        )
        return 2

    root = Path(args.dir) / name
    print(f"Scaffolding bundle at {root}/")
    write(root / ".codex-plugin" / "plugin.json",
          json.dumps(plugin_json(name), indent=2) + "\n", args.force)
    write(root / "SKILL.md",
          SKILL_MD.format(name=name, display=titleize(name)), args.force)
    write(root / ".mcp.json", json.dumps(MCP_JSON, indent=2) + "\n", args.force)
    write(root / "examples" / "example-run.json",
          json.dumps(EXAMPLE_JSON, indent=2) + "\n", args.force)
    # Where a shipped logo goes. Optional — omit newb.logo to use the generated
    # mark. To use your own, drop the image here and set
    # "newb": { "logo": "assets/logo.png" } in plugin.json.
    write(root / "assets" / "README.md", ASSETS_README, args.force)

    print(
        "\nNext: edit SKILL.md (system prompt), fill plugin.json + .mcp.json, "
        "remove every [TODO], then run:\n"
        f"  python3 scripts/validate_agent.py {root}\n"
        "Optional: add a logo — drop an image in assets/ and set "
        '"newb": {"logo": "assets/logo.png"} in plugin.json (or omit it to use '
        "the auto-generated mark)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
