#!/usr/bin/env bash
#
# One-shot installer for the newb Codex plugin.
#
# Codex 0.130 has `codex plugin marketplace add` but no CLI-side
# `plugin install`. Plugins need to be copied into
#   ~/.codex/plugins/cache/<marketplace>/<plugin>/<version>/
# before the plugin loader will pick them up. The Codex desktop app
# handles this through its UI; this script does the same for CLI users.
#
# Usage (after `codex plugin marketplace add newbworks/newb-plugins`):
#   bash ~/.codex/.tmp/marketplaces/newb/codex/install.sh
#
# Idempotent — safe to re-run after the marketplace upgrades.

set -euo pipefail

# Resolve the marketplace clone path (script lives inside it).
MARKETPLACE_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
MANIFEST="$MARKETPLACE_ROOT/codex/.codex-plugin/plugin.json"

if [[ ! -f "$MANIFEST" ]]; then
  echo "error: expected plugin manifest at $MANIFEST" >&2
  echo "       run this script from inside the newbworks/newb-plugins checkout" >&2
  exit 1
fi

# Pull name + version straight out of the manifest (no jq dep — just python3).
PLUGIN_NAME=$(python3 -c "import json,sys; print(json.load(open('$MANIFEST'))['name'])")
PLUGIN_VERSION=$(python3 -c "import json,sys; print(json.load(open('$MANIFEST'))['version'])")
MARKETPLACE_NAME=newb   # matches `name` field in .agents/plugins/marketplace.json

CACHE_DIR="$CODEX_HOME/plugins/cache/$MARKETPLACE_NAME/$PLUGIN_NAME/$PLUGIN_VERSION"
CONFIG_FILE="$CODEX_HOME/config.toml"

echo "Installing $PLUGIN_NAME@$PLUGIN_VERSION → $CACHE_DIR"
mkdir -p "$CACHE_DIR"
# Use `-a` so symlinks/perms survive; `--delete` would be cleaner with rsync
# but cp keeps the deps minimal.
cp -R "$MARKETPLACE_ROOT/codex/." "$CACHE_DIR/"

# Enable in config.toml if not already present.
PLUGIN_KEY="plugins.\"$PLUGIN_NAME@$MARKETPLACE_NAME\""
if [[ -f "$CONFIG_FILE" ]] && grep -qF "[$PLUGIN_KEY]" "$CONFIG_FILE"; then
  echo "Plugin already enabled in $CONFIG_FILE"
else
  echo "Enabling plugin in $CONFIG_FILE"
  mkdir -p "$(dirname "$CONFIG_FILE")"
  {
    printf '\n[%s]\n' "$PLUGIN_KEY"
    printf 'enabled = true\n'
  } >> "$CONFIG_FILE"
fi

cat <<EOF

Plugin files in place. Two more optional steps:

1. (Recommended) Generate one \$<slug> skill per newb you have access to:

    bash "$MARKETPLACE_ROOT/codex/sync-newbs.sh"

   This opens a browser to lobby.newb.works (OAuth), fetches your
   accessible newbs, and writes per-newb SKILL.md files so you can
   mention them directly in Codex like \$shal-newb or \$sv-newb.

2. Launch Codex:

    codex

Then ask: "list my newbs"

If you skipped step 1 above, Codex will still work — you'll just have
the single generic \`newb\` skill and the agent will pick newbs by
tool name (mcp__newb__delegate_start__<slug>). On the first newb tool
invocation Codex opens a browser for sign-in.

NOTE: \`codex exec\` (non-interactive) does NOT walk the OAuth challenge.
Use the interactive TUI for first-time auth; subsequent runs (any mode)
reuse the cached token.
EOF
