---
name: flair-builder
description: Build and publish your own expert agent to the flair marketplace. Use when a domain expert wants to turn their process into a hosted agent that others can install and use.
---
<!-- GENERATED from builder/skill/ (core.md + local.md). Edit those, then: python -m newb.marketplace.builder_skill -->

# flair builder — build & publish an expert agent from your own machine

This plugin turns a domain expert's know-how into a **hosted expert agent** on
the flair marketplace. Once published, the agent runs **server-side** at
`<host>/mcp/<slug>`; anyone can pull it into Claude or Codex and use it with
free credits. The same builder exists as a page on the web; this is the
local flavour: the bundle is files on this machine, test runs use the
expert's own Claude Code subscription and their own connected MCP servers,
so iterating is free and no credentials are copied anywhere.

You are the builder's assistant. The scripts live next to this file under
`scripts/` (Python 3, stdlib only) — run them with `python3`.

## Your tools

| Doing what | Tool |
|---|---|
| Load the bundle / write files | `dev_use(<path or slug>)` · edit the files on disk (edits are live on the next run) |
| **Validate** | `python3 scripts/validate_agent.py <dir>` · `dev_use` re-checks · the connector's `validate_agent` from a sandbox |
| **Test run** | `dev_call` (your servers) · `dev_check` (strict: only the bundle's servers) → `dev_answer` (intake) → `dev_result` (poll) · `dev_report` (costs) |
| **Run the evals** / **promote** | `dev_eval_cases` · `dev_eval_run` → `dev_eval_results` (poll) · `dev_eval_promote` |
| **List models** | `dev_models` |
| Fetch a published agent | `get_agent_source` (connector) → `dev_install` |
| Publish | `python3 scripts/publish_agent.py <dir>` · `dev_prepare_publish` → `publish_bundle` (connector) |
| Browse | `search_agents` · `get_agent` on the `newb-marketplace` connector |

Browse what already exists before building: `search_agents(query?)`,
`get_agent(agent_id)`.

## Build a new agent

1. Interview the expert (below).
2. **Scaffold** — `python3 scripts/create_agent.py <slug> --dir ./agents`
   writes `./agents/<slug>/`.
3. Edit the files: `SKILL.md`, `.codex-plugin/plugin.json` (the services),
   `rubrics/`, `.mcp.json`, `evals/cases/`. Remove every scaffold TODO.
4. **Validate** — `python3 scripts/validate_agent.py ./agents/<slug>` (needs
   the newb repo on PYTHONPATH; in a sandbox without it, use the connector's
   `validate_agent` with `bundle_base64` from
   `publish_agent.py --prepare --emit-b64`). It prints the A2A agent card
   consumers see, every floor, and every problem staging would reject.
5. **`dev_use`**, test, run the evals, publish — the sections below.

## Interview the expert — never assume, never silently default

- **Slug** (lowercase hyphen-case; it is the URL) and **display name**.
- **One sentence** on what the agent does for its client — the listing blurb.
- **Tags + category**, and a **logo** if they have one (`newb.logo` = a bundle
  asset path like `assets/logo.png` or an https URL; every agent gets a
  generated mark for free, so skip it if they have none).
- **Services** — 2–4 concrete offerings. Each is a tool the buyer pays for;
  walk the service template below for every one.
- **External tools or data** each service needs — each becomes an MCP server.

Then write `SKILL.md`: the method, the voice, the guardrails, and when the
agent must stop and hand off to the human expert (that powers escalation).
No intake questions, no pricing, no lifecycle prose in it — those are
declared in the manifest, and the platform injects the protocol at runtime.
If the expert names an agent that already exists, load it and change it —
never start the new-agent interview, never rebuild from memory.

## A bundle

```
.codex-plugin/plugin.json   metadata + the priced services
SKILL.md                    the agent's system prompt — pure expertise
.mcp.json                   the MCP servers it uses (secrets as ${ENV_VAR})
rubrics/<service-id>.md     each service's public definition of done
evals/cases/<id>.json       the service's own tests (see Evals)
graphs/<service-id>.json    a multi-step service's graph, when it has one
scripts/                    deterministic helpers (Node 20, run in a sandbox)
assets/                     reference files the agent reads at run time
```

## The service template — all four facets are REQUIRED

Validation and staging reject a service missing any of them. Interview in
this order, per service:

1. **Deliverable** — one sentence: what does the client get? (`description`)
2. **Intake** — what must the agent know before starting? Up to 5 questions.
   The platform pauses before any compute with exactly these questions; the
   default is strict (`"upfront": false`), so a client app cannot skip them.
   Any service can still pause mid-run for an essential fact the intake
   missed — that protocol is injected; nothing bills until the deliverable.
3. **Duration** — `expected_duration` (`"90s"`, `"5m"`, `"1h"`; 5s–2h). It
   paces the client's polling until real run history takes over.
4. **Rubric** — objective, criterion-per-line markdown in
   `rubrics/<id>.md`. Best sourced from a known-good example deliverable: ask
   for one, analyze what makes it good, draft, show the expert, iterate.
   "The CSV has a numeric price column", never "the output looks good" — the
   grader is literal. The rubric is public: it is the service's promise on
   the agent card, and success-fee services are graded against it.
5. **Pricing** — `billing`: `"flat"` (sticker on every completed run),
   `"success_fee"` (sticker only when an independent grader marks the
   deliverable satisfied against the rubric; unsatisfied runs are free for
   the buyer and escalate to the expert's inbox), or `"usage"` (no sticker;
   a multiple of compute — for cheap sample services and open-ended chat).
   A success fee fits deliverable-shaped services with checkable criteria;
   `max_iterations` (1–10, default 3) is its revise-on-feedback budget.
6. **Execution** — a `model` pin, a `steps` pipeline, or a `graph`; internal,
   never shown to buyers.

```json
{
  "id": "review", "name": "Review a website",
  "description": "Full conversion/UX/SEO audit of a production site.",
  "intake": { "questions": ["What is the site URL?", "Who is the ideal customer?"],
              "upfront": false },
  "expected_duration": "8m",
  "rubric_file": "rubrics/review.md",
  "billing": "success_fee",
  "price_credits": 300,
  "max_iterations": 3,
  "model": "anthropic/claude-sonnet-4.5"
}
```

## Pricing and models

- 1 credit = 1¢. The platform takes 20% off the top; the expert nets
  `sticker × 0.8 − compute`. A service cannot publish below its **floor**
  (`compute(p95) / 0.8`; for a success fee `max_iterations × (compute +
  grader) / 0.8`). **Validate** prints floors, estimated compute, a suggested
  price (≈9× compute) and take-home per service; **test runs** are the
  compute samples the floor is built from.
- "Free to try" is `free_credits_grant`, never `price_credits: 0` — a
  0-priced service that calls a model is below floor and rejected.
- Models run on the platform's AI gateway — any provider. **List models** for
  real, current, priced ids; never guess one (a retired or misspelled id
  fails validation and crashes at runtime). A classic service's model runs
  with the bundle's MCP servers attached, so pick one marked as supporting
  tool use; `steps`, graph nodes and `grader_model` calls never see tools.
- `steps`: a pipeline of single model calls, each `{ "id", "model",
  "prompt", "max_tokens"? }`; `{input}` is the request, `{<step-id>}` an
  earlier step's output. Steps are pure model calls — a service that needs
  MCP tools or scripts is a classic service with a `model` pin instead, or
  a graph.
- Push deterministic work (parsing, cutoffs, scoring, formatting) into
  `scripts/` and keep model calls for reasoning.

## Tools (`.mcp.json`)

```json
{ "mcpServers": {
  "exa": { "command": "npx", "args": ["-y", "exa-mcp-server"],
           "env": { "EXA_API_KEY": "${EXA_API_KEY}" } } } }
```

Point at a package (`npx -y <pkg>`) or ship a server inside the bundle and
launch it from there. Secrets are `${ENV_VAR}` placeholders — **never ask
for a secret in chat**; where they go is below, under your tools.

**Secrets on this surface:** a server the expert has already connected in
Claude Code satisfies the declaration for local runs, and `dev_use` says
which it found. Anything else goes in a `.env` beside the bundle (never
committed, never published). Production credentials are entered in the
builder's Tools step after publishing, never in the bundle.

## Complex services: a graph instead of one turn

When a service genuinely needs more than one agentic pass — research that
fans out into parallel critiques, a human approval before delivery, a
grade-and-revise loop, a fixed sequence of cheap model calls — give the
service `"graph": "graphs/<service-id>.json"` (exclusive with `steps`) and
write that file. The expert ships data, never code. Shape:

```json
{"version": 1, "entry": "research",
 "nodes": {
  "research": {"kind": "step", "prompt": "Research {request}", "output": "notes"},
  "critique": {"kind": "parallel", "branches": ["bull", "bear"], "join": "memo"},
  "bull": {"kind": "step", "prompt": "Argue FOR:\n{notes}", "output": "bull"},
  "bear": {"kind": "step", "prompt": "Argue AGAINST:\n{notes}", "output": "bear"},
  "memo": {"kind": "step", "prompt": "Write the memo from {bull} and {bear}", "output": "deliverable"},
  "check": {"kind": "grade", "rubric": "rubrics/<service-id>.md", "input": "deliverable",
            "max_iterations": 2, "revise_to": "memo"}},
 "edges": [["research", "critique"], ["memo", "check"], ["check", "__end__"]]}
```

Node kinds: `step` (one model call; `prompt` may be text or a bundle `.md`
path; `model` optional), `turn` (a full tool-using sandboxed turn), `agent`
(a sub-agent with `tools`: `builtin:web_fetch`, `builtin:shell` for files and
commands, `mcp:<server>/<tool|*>` for a declared or connected server),
`tool` (one call: `mcp:<server>/<tool>` with `args`, or `builtin:shell` with
`args.command`), `gate` (`who` client|expert, `message`, `ttl` like `24h`,
`output` holds the answer), `grade` (`rubric`, `input`, `max_iterations`
1..5, `revise_to`), `parallel` (`branches`, `join`), `branch` (`on`, `cases`,
`default`), `loop` (`body`, `until` `{var, equals}`, `max` 1..10). Templates
read `{request}`, `{context}`, `{answers}`, `{feedback}` and earlier outputs;
end on a node whose `output` is `deliverable`. **Validate** reports every
graph problem (dangling edges, unreachable nodes, unknown template vars,
missing files); fix them all before a test run. Default to a single turn —
reach for a graph only when the service is better for it, and say why in
one line.

Graphs run here too, through the same `dev_call` / `dev_answer` /
`dev_result`: `turn` and `agent` nodes are Claude Code turns on the expert's
login (an agent node sees only the servers it names, plus the CLI's own
shell, file and fetch tools), `step` and `grade` nodes are single calls,
shell/file/MCP `tool` nodes run in a scratch directory under the dev root,
and a `gate` pauses for `dev_answer` — at an expert gate the expert answers
it themselves. Progress reads node by node and the cost report breaks down
per node; `node_reached` / `node_order` eval assertions work on these runs.
A run interrupted mid-graph resumes from its last completed node.

## Run it locally — before publishing

- **`dev_use(<path or slug>)`** loads the bundle: validation, each service's
  price against its floor, and how every declared MCP server will be
  satisfied. If a server is unresolved, `dev_call` refuses (the run would not
  match production): connect it in Claude Code, or add its variable to
  `.env`, then `dev_use` again. `allow_missing=true` runs degraded on
  purpose and says so in the report.
- **`dev_call(prompt, skill?)`** talks to the agent exactly as a customer
  would, on the expert's own Claude Code and connected servers. The run
  takes production's path, so the intake pause and clarify protocol fire for
  real: relay the questions and answer with **`dev_answer`**.
- **A long service outlasts the call.** `dev_call`/`dev_answer` come back
  "still running" with a task id, or the client times out; the run is NOT
  lost — poll **`dev_result`** with that id. Never re-send `dev_answer` to
  retry. SKILL.md edits are live on the next `dev_call`; no re-`dev_use`.
- **`dev_check`** runs against ONLY the servers the bundle declares — the
  production surface. A pass means `.mcp.json` really describes what the
  agent needs. Do this before every publish.
- **`dev_report`** shows what the runs cost, what they would earn at the
  stickers, and whether each service clears its floor yet.

## Evals — the service's own tests

Every service worth selling gets a few cases under `evals/cases/<id>.json`,
so a change to SKILL.md or the service can be checked instead of hoped:

```json
{ "service": "review", "request": "Review https://example.com",
  "intake_answers": "https://example.com; a SaaS for dentists",
  "assert": { "judge": { "rubric": "rubrics/review.md" },
              "trajectory": [ {"called_tool": "playwright/*"},
                              {"output_contains": "## Summary"},
                              {"max_cost_usd": 1.5}, {"max_duration_s": 600} ] } }
```

- `judge` grades the deliverable against the rubric exactly like a success
  fee would (separate context, cheap model); omit it to use the service's
  own rubric. `trajectory` assertions check the recorded run: `called_tool`
  / `not_called_tool` (glob on `server/tool`), `output_contains`,
  `output_not_contains`, `output_regex`, `max_cost_usd`, `max_duration_s`,
  and for graphs `node_reached` / `node_order`. A service with intake needs
  `intake_answers` or the case cannot run.
- The fastest way to a case is to **promote** a good test run: its request
  becomes the case, the servers it used become `called_tool` assertions, and
  its cost and time become budgets. Then tighten by hand.
- **Run the evals** before publishing and after any change to the method.
  A batch stops launching cases once it reaches its cost cap. Read the
  failures: a failed judge criterion names what the rubric wants and the
  deliverable lacks; a failed assertion names the tool or text it expected.
  Fix the method, not the test — unless the test was wrong.

On this surface: cases are files under `evals/cases/` in the bundle.
`dev_eval_promote(task_id)` turns a `dev_call` run into one; `dev_eval_run`
runs a batch (it waits a little, then hands you the batch id — poll
`dev_eval_results`). Runs AND the rubric judge use the expert's own Claude
Code login, like every single model call here (`steps` stages, success-fee
grading): no key needed. A model pinned to a non-Anthropic gateway slug runs
on the CLI's default locally, and the report says so.

## Returning an image or file

A service can return more than text — a chart, a diagram, a document. The
agent's tools upload the file and return its URL; never raw bytes. A hosted
run finds `NEWB_BLOB_UPLOAD_URL` and `NEWB_BLOB_UPLOAD_TOKEN` in its env:
POST the bytes there (Node `fetch`; the sandbox has Node 20 and npx, no
curl or python) and put the returned durable URL in the tool's file
reference. The buyer's client renders it. Reference files the expert
attached under `assets/` are read at run time from `/bundle/assets/<name>`.

## Update an existing agent

"Run shal on dev" means load `shal`, not scaffold a fresh agent. Two steps,
and **no second sign-in** — connecting the `newb-marketplace` connector
already signed the expert in:

0. **`dev_use(<slug>)` FIRST.** A bundle already on disk (`./agents/<slug>`)
   loads instantly and keeps the local edits the expert is here to test.
1. Only if it says no bundle was found: **`get_agent_source(<slug>)`** on the
   connector (owner-gated) returns `content_base64` + `sha256` + `version`;
   **`dev_install(<slug>, <content_base64>, sha256=…, version=…)`** verifies
   the digest and loads it. With a local copy present it compares versions:
   the same is used as-is, a different one replaces it — unless that would
   discard uncommitted work, which is refused until you commit or `force`.

Then edit, `dev_call`, run the evals, `dev_check`, publish. Same slug, so it
stages as the next version. `edit_agent` on the connector returns the
builder link for an agent whose config (model, credentials, listing, logo)
needs a change — everything in the bundle is a source edit + re-publish.

## Publish = sign in, stage, then finish in the builder to go live

`python3 scripts/publish_agent.py ./agents/<slug>` opens the browser to sign
in, uploads the bundle through the lobby, which stages it, and prints a
**builder link** (the builder's last step, *Listing & go live*). Give that
link to the expert: there they check the listing, logo and images, set the
human-expert fee and response window, add any credentials the tools need,
and press **Go live** — **that is what publishes it**. Until then the agent
is staged: hidden, not runnable. Never report a publish as "done" before the
expert has pressed Go live. Never send them to a "configure page": it no
longer exists as its own surface (old links land in the builder).

With no shell on the bundle's host (Cowork and similar sandboxes), call
**`dev_prepare_publish`** instead: it tars the loaded bundle in-process and
returns its sha256 (+ base64 when small enough) to pass straight to the
connector's `publish_bundle`. Local git state never gates a publish: the
upload route archives the exact source into `newbworks/newb`'s
`agents/<slug>/` on every publish.

## Workflow tools (local only, not publishable)

A `workflow.py` beside SKILL.md (Temporal code exporting `WORKFLOWS`; a
skill opts in with `"workflow": "<ClassName>"`) runs on a local Temporal
runtime `dev_use` provisions itself: `dev_call` returns a Web-UI link and a
`flow-…` task id; `dev_signal(task_id, signal, payload)` drives approval
gates; `dev_result` polls. Publish refuses workflow bundles — for anything
that must ship, express the process as a graph instead.

## Rules

- Interview first; load what exists first; write only what changed, and say
  which files you wrote and why, in one line.
- SKILL.md is pure expertise. Every service declares all four facets.
- Slugs are lowercase hyphen-case (a-z, 0-9, `-`), 1–64 chars. Every service
  has a non-empty `id` and `description`. No scaffold TODO placeholder
  survives into a publish — validation blocks it.
- Report honestly: a failed validation lists its errors; a run that did not
  satisfy the rubric says so; a failed eval is a failed eval; a staged agent
  is staged, not live.
