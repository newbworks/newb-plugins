---
name: newb-builder
description: Build and publish your own expert agent to the newb marketplace. Use when a domain expert wants to turn their process into a hosted agent that others can install and use.
---

# newb builder — create & publish an expert agent

This plugin turns a domain expert's know-how into a **hosted expert agent** on
the newb marketplace. Once published, the agent runs **server-side** and is
reachable at `<host>/mcp/<slug>`; anyone can pull it into Claude or Codex and
use it with free credits.

You are the builder's assistant — drive the flow below. The helper scripts are
bundled with this plugin under `scripts/` and are self-contained (Python 3,
stdlib only). Run them with `python3` (in Claude Code they are at
`${CLAUDE_PLUGIN_ROOT}/scripts/`). They publish to the live marketplace by
default — no CLI or repo checkout needed.

## Browse what already exists

Use the `newb-marketplace` MCP tools before building:
- `search_agents(query?)` — list agents already on the marketplace.
- `get_agent(agent_id)` — details + skills for one agent.

## Build a new agent

An agent is a **bundle**: `SKILL.md` (its instructions/system prompt),
`.mcp.json` (its tools), and `.codex-plugin/plugin.json` (metadata + skills).

1. **Interview the expert.** Nail down: a short slug name, one sentence on what
   it does, its 2–4 concrete skills, and which external tools/data it needs
   (each becomes an MCP server).
2. **Scaffold** (writes `./agents/<name>/`):
   `python3 scripts/create_agent.py <name> --dir ./agents`
3. **Write the system prompt.** Edit `./agents/<name>/SKILL.md` — the agent's
   instructions, voice, and guardrails. Be explicit about when it should *stop
   and let the human expert step in* (that powers escalation). Remove every
   `[TODO: …]`.
4. **Fill the manifest.** Edit `./agents/<name>/.codex-plugin/plugin.json`:
   `display_name`, `description`, `tags`, `price_credits` (keep `0` for free),
   `free_credits_grant`, and the `skills` array (each `id` + `description`
   becomes a tool on the published agent).
5. **Declare tools.** Edit `./agents/<name>/.mcp.json` with the MCP servers the
   agent needs (use `${ENV_VAR}` for secrets — authorized when configuring).
6. **Validate:** `python3 scripts/validate_agent.py ./agents/<name>`
   Fix anything it reports; it prints the A2A Agent Card consumers will see.

## Publish (runs hosted, pullable by anyone)

`python3 scripts/publish_agent.py ./agents/<name> --configure-platform`

This tars the bundle, uploads it to the hosted executor, installs it, and (with
`--configure-platform`) points it at the platform LLM so it runs immediately.
It prints the agent's hosted MCP endpoint `<host>/mcp/<slug>` — pull that into
Claude or Codex to use the agent. Drop `--configure-platform` if the expert
will bring their own LLM key/model on the newb configure page instead.

## Rules

- Never leave `[TODO: …]` in a published bundle (`validate` blocks it).
- The name must be lowercase hyphen-case (a-z, 0-9, `-`), 1–64 chars.
- Every skill needs a non-empty `id` and `description`.
- The `SKILL.md` body must be non-empty — it is the agent's system prompt.
