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

1. **Interview the expert.** Ask for each of these — don't assume, and don't
   silently default:
   - **Name (slug)** — lowercase hyphen-case, drives the URL `<host>/mcp/<slug>`.
   - **Display name** — the human-facing title shown on the listing (defaults
     to a title-cased slug if they don't care).
   - **One sentence** on what the agent does for the user (the listing blurb).
   - **Tags + category** — how it's found in the catalog.
   - **Logo** — how the agent looks in the catalog and as the installed
     plugin's icon. Ask "do you have a logo?" See **Logo** below; if they
     don't, skip it — every agent gets a distinct generated mark for free.
   - **Services** — its 2–4 concrete offerings (each becomes a tool the buyer
     calls). Every service is built to ONE template — see **The service
     template** below; walk it per service.
   - **External tools/data** it needs — each becomes an MCP server (step 5).
2. **Scaffold** (writes `./agents/<name>/`):
   ```bash
   python3 scripts/create_agent.py <name> --dir ./agents
   ```
3. **Write the system prompt.** Edit `./agents/<name>/SKILL.md` — its
   instructions, voice, and guardrails. Be explicit about when it should *stop
   and let the human expert step in* (that powers escalation). Remove every
   `[TODO: …]`. Do NOT add client-intake instructions ("first ask for X"),
   lifecycle notes, or pricing prose — those are declared in the manifest,
   not the prompt. Keep the SKILL.md pure expertise.

## The service template (walk this per service — all four facets REQUIRED)

Every service ships four declared facets; `validate` (and staging) REJECTS a
service missing any of them. Interview the expert in this order:

1. **Deliverable** — one sentence: what does the client get? (→ the service's
   `description`.)
2. **Intake** — "what must you know from the client before you can start?"
   Up to 5 questions. The platform pauses the run with EXACTLY these
   questions before any compute is spent, and the default is STRICT: they
   are always put to the human. Only if the expert explicitly accepts
   client-app-supplied answers (e.g. a URL already in the conversation), set
   `"upfront": true`. Separately, any service can pause mid-run to ask for
   essential facts the intake didn't cover — that protocol is
   platform-injected; nothing bills until the final deliverable.
3. **Duration** — "how long does a typical run take?" → `expected_duration`
   (`"90s"`, `"5m"`, `"1h"`; must be 5s–2h). It paces the client's polling
   from the very first run; observed run history takes over automatically.
4. **Rubric** — the public definition of done, REQUIRED for every service.
   Best sourced from a known-good example deliverable: ask for one, analyze
   what makes it good, and write objective, criterion-per-line markdown in
   `rubrics/<service-id>.md`. It appears on the agent card as the service's
   promise; success-fee services are additionally GRADED against it.
5. **Pricing** — pick a billing mode (see **Pricing** below): `flat`
   (sticker charged on completion), `success_fee` (sticker charged only on a
   satisfied grader verdict; escalates to the expert when unsatisfied), or
   `usage` (multiple × compute, no sticker).
6. **Execution** — model pin or a `steps` pipeline, scripts. Internal; never
   shown to buyers.

   A complete service entry:

   ```json
   {
     "id": "review", "name": "Review a website",
     "description": "Full conversion/UX/SEO audit of a production site.",
     "intake": { "questions": ["What is the site URL?", "What does the business do?",
                              "Who is your ideal customer?", "How does it make money?"],
                 "upfront": false },
     "expected_duration": "8m",
     "rubric_file": "rubrics/review.md",
     "billing": "success_fee",
     "price_credits": 300,
     "model": "claude-sonnet-5"
   }
   ```
4. **Fill the manifest.** Edit `./agents/<name>/.codex-plugin/plugin.json`:
   `display_name`, `description`, `tags`, `free_credits_grant`, and the `skills`
   array (each `id` + `description` becomes a tool). Price each tool and choose
   its model(s) — see **Pricing & advanced tools** below.
5. **Declare tools.** Edit `./agents/<name>/.mcp.json` with the MCP servers the
   agent needs (use `${ENV_VAR}` for secrets — authorize them when configuring).

### Logo

Every agent gets a distinct **generated** initials-on-gradient mark with zero
effort — so a logo is optional. To use your own, set `newb.logo` in
`plugin.json` to **either** an image shipped in the bundle **or** an absolute
URL:

```json
"newb": { "logo": "assets/logo.png", ... }   // shipped in the bundle
"newb": { "logo": "https://cdn.example.com/logo.svg", ... }  // hosted elsewhere
```

- **Shipped asset** (recommended — keeps the agent self-contained): drop the
  file under `assets/` and point `logo` at its bundle-relative path. Supported:
  `.png .jpg .jpeg .svg .webp .gif`. The executor serves it at
  `<host>/agents/<slug>/logo.svg`; `validate` fails if the file is missing.
- **URL**: any `http(s)` image; the logo endpoint redirects to it.

After publishing, the expert can also swap the logo on the configure page
(`edit_agent` → `logo`) without a re-publish — that override wins over the
bundle's `logo`. Precedence: configure-page override → bundle `logo` →
generated mark. Don't send image **bytes** through a tool response; host the
image and reference it by URL (same rule as agent output images below).
6. **Validate:**
   ```bash
   python3 scripts/validate_agent.py ./agents/<name>
   ```
   Fix anything it reports; it also prints the A2A Agent Card consumers see.
   The script needs the newb repo on PYTHONPATH (it uses the real loader). In
   a sandbox without it, use the `newb-marketplace` MCP tool
   **`validate_agent`** instead — pass `bundle_base64` (print it with
   `publish_agent.py --emit-b64 <tarball>` after `--prepare`) to pre-check the
   local bundle without staging, or `agent_id` to check an already-staged
   agent. It runs the full publish lint with the live rate card: pricing
   floors (including outcome floors), rubric size, retired models, TODOs.
   Staging enforces the same checks server-side, so an invalid bundle is
   rejected at upload with the same messages — validate first to avoid the
   round-trip.

## Pricing & advanced tools

Each skill **is a priced tool** — the unit the buyer clicks and pays for. Get
three things right per tool: its **price**, its **model(s)**, and where **scripts**
do the deterministic work.

**Billing modes (`billing`, explicit on every service).**
- `"flat"` + `price_credits` — the sticker charges on every completed run.
- `"success_fee"` + `price_credits` — the sticker charges ONLY when an
  independent grader marks the deliverable satisfied against the service's
  rubric (see **Outcome pricing** below). Higher floor; unsatisfied runs are
  free for the buyer and escalate to the expert.
- `"usage"` — no sticker; bills a multiple of the run's compute (like the
  free-form `ask` tool). Good for cheap sample/hook services.

**Price (`price_credits`).** The sticker in credits (1 credit = 1¢). The
platform takes **20% off the top**; the expert nets `sticker × 0.8 −
compute`. A tool can't publish below its **floor** = `compute(p95) / (1 − 0.20)`.
Run `newb agent validate` (the CLI validator) or the `validate_agent` MCP tool
to print each service's floor, estimated compute, a suggested price
(≈9× compute), and take-home.

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

## Outcome pricing (success fee) — sell a completed service

Instead of a flat per-call sticker, a tool can bill **only when the deliverable
is actually done**: an independent grader (separate context, can't be talked
into a pass) scores the deliverable against the expert's **published rubric**;
the hosted agent revises on the grader's feedback up to `max_iterations`. A
*satisfied* verdict bills the sticker; anything else bills the buyer **nothing**
and auto-escalates the run to the expert's inbox.

**When to offer it.** Ask the expert, per tool: "flat price per call, or a
success fee — the buyer pays only if the deliverable meets your definition of
done?" A success fee fits deliverable-shaped tools (a review, a draft, a model,
a report) with checkable criteria. It does NOT fit open-ended conversation —
keep `ask`-like tools usage-based.

**Interview the expert for the rubric — this is the productization step:**
1. Best method: ask for a **known-good example deliverable**, analyze what makes
   it good, and draft the rubric from that. Otherwise interview for explicit
   criteria: "what would make you reject this deliverable?"
2. Write objective, gradeable, criterion-per-line items under headings —
   "The CSV contains a price column with numeric values", never "the output
   looks good". **The grader is literal**: vague criteria produce noisy grades
   and angry buyers.
3. Show the expert the draft and iterate. Make two things explicit: the rubric
   is **public** (it's on the agent card — it is the service contract), and an
   unsatisfied run means they earn nothing while still paying the compute, and
   the job lands in their escalation inbox to finish by hand.
4. Save it as `rubrics/<skill-id>.md` in the bundle and mark the skill:

```json
"skills": [{
  "id": "dcf_model", "name": "DCF model", "description": "Build a DCF model as .xlsx.",
  "billing": "success_fee",
  "price_credits": 2500,
  "rubric_file": "rubrics/dcf_model.md",
  "max_iterations": 3,
  "expected_duration": "10m",
  "intake": { "questions": ["Which company, and which fiscal years?"], "upfront": false }
}]
```

`max_iterations` (1–10, default 3) is the revision budget per run: more retries
raise the success rate but burn more compute per run — compute the expert pays
for even when the run fails. An optional `"grader_model"` overrides the
platform's default (a cheap model; grading is classification, not generation).
A success-fee service **requires** a positive `price_credits`, and its floor is
higher than a flat one's: `max_iterations × (compute + grader) / (1 − 20%)` —
`validate` prints it. Steps pipelines and classic tools can both be
success-fee billed; the loop wraps whichever the tool uses. (The older nested
`"outcome": {...}` form still parses but is deprecated — use the service-level
fields above.)

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

## Returning an image or file to the user

A tool can return more than text — a rendered chart, a generated diagram, a
produced document. **Host the asset and return its URL; never put raw bytes on
the wire.** Inside your MCP tool: upload the file, then return a file reference
alongside your text. The platform carries it to the buyer's client as a
structured file part (which renders the image); the consumer sees a `files`
list of `{ "uri", "mime_type", "name" }` on the result.

- Reference by `http(s)` URL (a small `data:` URI is tolerated for a tiny
  thumbnail; anything large is dropped — host it instead).
- The URL should be durable for as long as the buyer might re-open the result.
  A signed URL is fine as long as it outlives the response.

**The platform gives you a host — no storage account needed.** A hosted run
finds two env vars set: `NEWB_BLOB_UPLOAD_URL` and `NEWB_BLOB_UPLOAD_TOKEN`.
POST your image bytes there and you get back a durable URL.

The hosted sandbox ships **Node 20 + npx only** — there is no `curl`, `wget`, or
`python3` — so upload with `fetch` (built into Node 18+):

```js
import { readFile } from "node:fs/promises";

const res = await fetch(process.env.NEWB_BLOB_UPLOAD_URL, {
  method: "POST",
  headers: {
    Authorization: `Bearer ${process.env.NEWB_BLOB_UPLOAD_TOKEN}`,
    "Content-Type": "image/png",
  },
  body: await readFile("chart.png"),
});
const { url } = await res.json();  // → https://.../blob/<hash>.png
```

The token is per-run and short-lived; the storage credential never touches your
sandbox. Accepts png/jpeg/webp/gif/svg + pdf, up to 8 MB. Put the returned
`url` in your tool's file reference.

> The same constraint applies to anything in your bundle's `scripts/`: it runs
> in that Node-only sandbox. A Python helper will not execute there.

## Update an existing agent

Your environment is often a fresh sandbox with no copy of the agent's source —
never rebuild from memory. Pull the CURRENT source first with the
`newb-marketplace` MCP tool **`get_agent_source`** (owner-gated: sign in as
the account that published it): it returns the active bundle as a base64
.tar.gz. Decode + extract it, make the edits, then `validate_agent` and
publish as below — same slug, so it stages as the next version. The
`edit_agent` tool covers only config (LLM, creds, price multiple, logo) via
the configure page; everything else — SKILL.md, skills/stickers/steps,
rubrics, scripts, .mcp.json — is a source edit + re-publish.

## Publish = sign in, stage, then configure to go live

```bash
python3 scripts/publish_agent.py ./agents/<name>
```

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
- **Every service must declare all four facets** — `intake`,
  `expected_duration`, `rubric_file`, and an explicit `billing` — `validate`
  and staging both reject incomplete services. Walk the service template for
  each one; completeness IS the publish gate.
- The `SKILL.md` body must be non-empty — it is the agent's system prompt.
