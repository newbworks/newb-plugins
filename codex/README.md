# newb (Codex plugin)

Talk to your newbs from Codex. After install you sign in once with your lobby account and the plugin auto-discovers every newb you have access to.

## Install

```bash
# 1. Register the marketplace (clones the repo into ~/.codex/.tmp/marketplaces/newb)
codex plugin marketplace add newbworks/newb-plugins

# 2. Install + enable the plugin
bash ~/.codex/.tmp/marketplaces/newb/codex/install.sh

# 3. (Recommended) Generate one $<slug> skill per newb you have access to.
#    Opens a browser tab for OAuth, fetches your newbs, writes SKILL.md files.
bash ~/.codex/.tmp/marketplaces/newb/codex/sync-newbs.sh

# 4. Launch the interactive TUI
codex
```

After sync you get one Codex skill per newb, mentionable directly:

```
$shalin-newb summarize my latest memory entry
$sv-newb what's on my calendar today?
```

The skill mention names are kebab-case forms of the newb display name (e.g. "Shalin's newb" → `$shalin-newb`). In the Codex picker the skills render with their **human-readable display name** ("Shalin's newb") — the `$shalin-newb` mention slug is just the typing handle. The sync script writes both:

- `SKILL.md` with `name: shalin-newb` (= the `$<slug>` mention; portable across agents that follow the SKILL.md spec)
- `agents/openai.yaml` with `interface.display_name: "Shalin's newb"` (Codex-specific UI override so the picker shows the natural name with apostrophe + capitalization)

The underlying MCP tools stay `mcp__newb__delegate_start__<slug>` (underscored — same `skillName()` slugifier the legacy install path uses) so we don't break any existing tool wiring.

If you skip step 3, the plugin still works — you'll have a single generic `$newb` skill that uses `mcp__newb__list_newbs` to enumerate and picks one by tool name. Step 3 is what makes the `$<slug>` mentions appear.

**Re-run `sync-newbs.sh` when your newb access changes.** It clears the old per-newb skills (keeps the generic `newb` skill) and rewrites from the current `list_newbs` response.

The first time any newb tool is called, Codex opens a browser tab for sign-in (OAuth 2.1 + PKCE against `lobby.newb.works`) — the sync script already triggered this for the CLI flow, but Codex has its own separate token storage so it does its own (silent) OAuth on first invocation.

**Why a separate install script?** Codex 0.130 has `codex plugin marketplace add` but no `codex plugin install` — plugins have to be copied into `~/.codex/plugins/cache/<marketplace>/<plugin>/<version>/` and enabled via `~/.codex/config.toml` before the loader picks them up. The desktop app handles this through its UI; the script does the same for CLI users. Idempotent — safe to re-run after `codex plugin marketplace upgrade newb`.

**`codex exec` won't trigger OAuth.** The OAuth challenge from the gateway only completes through the interactive TUI's browser hand-off. Once auth is cached, subsequent runs (including `codex exec`) can use the tools.

## Usage

Once installed, the plugin exposes:

- `list_newbs` — enumerate the newbs you have access to.
- For each newb `<slug>` you can reach: `delegate_start__<slug>`, `delegate_status__<slug>`, `delegate_cancel__<slug>`, `delegate_continue__<slug>`, `describe__<slug>`.

The `newb` skill auto-routes when you say things like:

- "ask my acme newb to summarize my latest memory entry"
- "have my work newb check if I have any open Linear tickets"

## Access changes

The tool list refreshes when you start a new MCP session. If someone grants or revokes your access to a newb, restart Codex to pick up the change.

## Issues

Report issues at https://github.com/newbworks/newb-plugins/issues.
