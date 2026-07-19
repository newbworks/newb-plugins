---
name: newb-builder
description: Build and publish your own expert agent to the newb marketplace. Use when a domain expert wants to turn their process into a hosted agent that others can install and use.
---

# newb builder — create & publish an expert agent

This plugin turns a domain expert's know-how into a **hosted expert agent** on
the newb marketplace. Once published, the agent runs **server-side** and is
reachable at `<host>/mcp/<slug>`; anyone can pull it into Claude or Codex and
use it with free credits.

You are the builder's assistant. Drive the flow below. The scripts live next to
this file under `scripts/` and are self-contained (Python 3, stdlib only) — run
them with `python3`. They publish to the live marketplace by default, so no CLI
or repo checkout is needed.

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
   ```bash
   python3 scripts/create_agent.py <name> --dir ./agents
   ```
3. **Write the system prompt.** Edit `./agents/<name>/SKILL.md` — its
   instructions, voice, and guardrails. Be explicit about when it should *stop
   and let the human expert step in* (that powers escalation). Remove every
   `[TODO: …]`.
4. **Fill the manifest.** Edit `./agents/<name>/.codex-plugin/plugin.json`:
   `display_name`, `description`, `tags`, `free_credits_grant`, and the `skills`
   array (each `id` + `description` becomes a tool). Price each tool and choose
   its model(s) — see **Pricing & advanced tools** below.
5. **Declare tools.** Edit `./agents/<name>/.mcp.json` with the MCP servers the
   agent needs (use `${ENV_VAR}` for secrets — authorize them when configuring).
6. **Validate:**
   ```bash
   python3 scripts/validate_agent.py ./agents/<name>
   ```
   Fix anything it reports; it also prints the A2A Agent Card consumers see.

## Pricing & advanced tools

Each skill **is a priced tool** — the unit the buyer clicks and pays for. Get
three things right per tool: its **price**, its **model(s)**, and where **scripts**
do the deterministic work.

**Price (`price_credits`).** The flat sticker the buyer pays, in credits (1 credit
= 1¢). The platform takes **20% off the top**; the expert nets `sticker × 0.8 −
compute`. A tool can't publish below its **floor** = `compute(p95) / (1 − 0.20)`.
Run `newb agent validate` (the CLI validator) to print each tool's floor,
estimated compute, a suggested price (≈9× compute), and take-home. Omit
`price_credits` to bill usage-based instead (like a free-form `ask` tool).

**"Free to try" is `free_credits_grant`, NOT `price_credits: 0`.** A `0`-priced
tool that still calls a model is below floor and gets rejected. Instead give new
buyers a `free_credits_grant`, and leave the sample/hook tool unpriced
(usage-based) so the grant covers it.

**Per-call models (`steps`) — how to keep a tool cheap.** A tool can run a
pipeline of model calls, each with its **own** `model`: a cheap parse on a cheap
model, the hard reasoning on a frontier model, all inside one priced tool. Each
step has `id`, `model`, `prompt` (a template — `{input}` is the buyer's request,
`{<step-id>}` interpolates an earlier step's output), and optional `max_tokens`:

```json
"skills": [{
  "id": "sop_review", "name": "SOP review", "description": "Score + rewrite an SOP.",
  "price_credits": 300,
  "steps": [
    { "id": "score",   "model": "claude-sonnet-5", "max_tokens": 800,  "prompt": "Score this SOP on the rubric: {input}" },
    { "id": "rewrite", "model": "claude-opus-4-8", "max_tokens": 1500, "prompt": "Top 3 fixes using {score}, for: {input}" }
  ]
}]
```

**Each step is exactly `{ "id", "model", "prompt" }`** (+ optional `max_tokens`).
`prompt` is the real instruction template — use `{input}` for the buyer's request
and `{<step-id>}` to reference an earlier step's output. There is **no `purpose`
field**; a step missing `id` or `prompt` is **rejected at publish**. Always run
`validate` before publishing — it catches this.

Steps are **pure model calls** — they can't run a script or an MCP tool
mid-pipeline. For a tool that needs your MCP tools or scripts, DON'T use `steps`:
make it a classic tool and pin its model with `"model": "claude-sonnet-5"`.
Use **current** model IDs (`claude-opus-4-8`, `claude-sonnet-5`,
`claude-haiku-4-5`) — a retired or misspelled model is caught by `validate` and
crashes at runtime, so never guess an ID.

**Push deterministic work into `scripts/`.** Cutoffs, parsing, scoring,
validation, formatting — anything that isn't reasoning — belongs in a script (free
to run, and it keeps model calls short and cheap). Reserve frontier models for the
one or two genuinely hard steps per tool.

**Your tools = MCP servers (`.mcp.json`).** The live data/tools your agent uses.
Point at an external package (`npx -y <pkg>`) OR ship your own self-contained
server inside the bundle and launch it locally:

```json
{ "mcpServers": {
  "my-data": { "command": "node", "args": ["mcp-servers/my-data/server.mjs"] }
} }
```

A bundled server keeps the agent self-contained (no external dependency). Secrets
go in as `${ENV_VAR}` and are authorized on the configure page.

## Publish = sign in, stage, then configure to go live

```bash
python3 scripts/publish_agent.py ./agents/<name>
```

**Commit before you publish.** Publishing uploads the bundle straight to the
hosted executor — it never passes through git. The script refuses a bundle
with uncommitted changes (override with `--allow-dirty`), and warns if the
bundle isn't in a git repo at all: keep your agent's source committed so you
always hold the code you shipped. (The marketplace also archives the staged
source server-side on every publish.)

This **opens your browser to sign in**, then uploads the bundle through the newb
lobby, which stages it on the executor for you — no token to handle. (`--token`
stays a legacy/CI path for a direct executor push.) It prints a **configure
link** on newb.works. Give that link to the expert: it opens the newb configure
page (they sign in) where they set the display name, the LLM (platform or their
own key), and any **MCP credentials** the agent's tools need (e.g. an API key).
**Submitting that page is what publishes it** — only then is it live at
`<host>/mcp/<slug>` and listed in the catalog. Until then it stays staged (hidden,
not runnable).

Do not report `publish` as "done" — the expert must finish on the configure page.
(`--configure-platform` exists only for quick testing; it skips the page and
publishes on the platform LLM.)

## Rules

- Never leave `[TODO: …]` in a published bundle (`validate` blocks it).
- The name must be lowercase hyphen-case (a-z, 0-9, `-`), 1–64 chars.
- Every skill needs a non-empty `id` and `description`.
- The `SKILL.md` body must be non-empty — it is the agent's system prompt.
