# newb (Claude Code plugin)

Talk to your newbs from Claude Code. After install you sign in once with your lobby account and the plugin auto-discovers every newb you have access to.

## Install

```
/plugin marketplace add newbworks/newb-plugins
/plugin install newb@newb
```

The first time the plugin's MCP server is contacted, Claude Code's `/mcp` flow prompts you to authenticate. A browser tab opens at `https://lobby.newb.works` — sign in with Google, approve the connection, and you're done. The OAuth token is stored in Claude Code's per-user secure storage; the plugin contains no secrets.

## Usage

Once installed, the plugin exposes:

- `list_newbs` — enumerate the newbs you have access to.
- For each newb `<slug>` you can reach: `delegate_start__<slug>`, `delegate_status__<slug>`, `delegate_cancel__<slug>`, `delegate_continue__<slug>`, `describe__<slug>`.

In practice you don't call these by name — the `newb` skill picks the right tool when you say things like:

- "ask my acme newb to summarize my latest memory entry"
- "have my work newb check if I have any open Linear tickets"
- "what does my personal newb know about project X?"

If you don't name a newb, the skill calls `list_newbs` first and picks one by role and description.

## Per-newb agents (run once after install)

The plugin ships with **only the generic `newb` skill**. For one **subagent per newb** with tool-whitelist isolation (each agent can ONLY call its own newb's MCP tools), run the sync script once after install:

```bash
bash ~/.claude/plugins/cache/newb/newb/0.1.0/sync-newbs.sh
```

The generic skill will also prompt you the first time you name a specific newb in a conversation, since per-newb agents are the recommended setup. The script opens a browser tab for OAuth (silent if you're already signed in to lobby), fetches your accessible newbs, and writes one `agents/<slug>.md` per newb into the plugin cache. Re-running is safe — it wipes the existing `agents/*.md` and rebuilds from your current access. After `/reload-plugins`:

- Saying "ask my sv newb to ..." auto-delegates to the `sv-newb` subagent
- That subagent runs in its own sub-conversation and can ONLY call `mcp__newb__*__sv_s_newb` tools (no cross-newb tool access, no Bash/Read/Edit)
- One Claude session can `Task`-delegate to multiple newbs in parallel

Re-run the script when your newb access changes.

## Access changes

The tool list refreshes when you start a new MCP session. If someone grants or revokes your access to a newb, restart Claude Code (or run `/reload-plugins`) to pick up the change. For per-newb agents, re-run `sync-newbs.sh` so the agent files match your current access.

## Sign out

To sign out, remove the OAuth credentials via Claude Code's `/mcp` panel (Disconnect) and re-authenticate on next use.

## Issues

Report issues at https://github.com/newbworks/newb-plugins/issues.
