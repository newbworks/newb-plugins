#!/usr/bin/env bash
#
# Sync per-newb skills (Codex) + per-newb agents (Claude Code) from
# the lobby.
#
# After the newb plugin is installed in either client, this script:
#   1. Walks OAuth 2.1 + PKCE against lobby.newb.works (browser tab).
#   2. Calls `mcp__newb__list_newbs` via the gateway with the fresh token.
#   3. For each detected client install:
#      - Codex:       writes skills/<mention>/SKILL.md  + agents/openai.yaml
#                     (auto-route by description, $<mention> mention)
#      - Claude Code: writes agents/<mention>.md (Task-delegatable
#                     subagent with tools-whitelist isolation — each
#                     agent can ONLY call its own newb's MCP tools)
#
# `<mention>` is a human-readable kebab-case form of the newb's display
# name (strips possessive `'s`, lowercases, hyphenates). The gateway-side
# tool suffix (`delegate_start__<slug>`) stays underscored so we don't
# break tool names; per-newb skill/agent files just reference the right
# `__<slug>` tools by name.
#
# Re-run when accessible newbs change. Files written (each client
# independently, only if its plugin is installed):
#   ~/.codex/plugins/cache/newb/newb/<v>/skills/<mention>/SKILL.md
#   ~/.codex/plugins/cache/newb/newb/<v>/skills/<mention>/agents/openai.yaml
#   ~/.claude/plugins/cache/newb/newb/<v>/agents/<mention>.md
#
# Requires: python3, curl, openssl (macOS defaults).

set -euo pipefail

GATEWAY_URL="${GATEWAY_URL:-https://gateway.newb.works}"
LOBBY_URL="${LOBBY_URL:-https://lobby.newb.works}"
CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
CLAUDE_HOME="${CLAUDE_HOME:-$HOME/.claude}"

# ── 0. Find installed plugin cache dirs (Codex + Claude Code) ────────
shopt -s nullglob
CODEX_VERSIONS=("$CODEX_HOME"/plugins/cache/newb/newb/*)
CLAUDE_VERSIONS=("$CLAUDE_HOME"/plugins/cache/newb/newb/*)
shopt -u nullglob

CODEX_PLUGIN_DIR=""
CLAUDE_PLUGIN_DIR=""
if [[ ${#CODEX_VERSIONS[@]} -gt 0 ]]; then
  CODEX_PLUGIN_DIR=$(ls -td "${CODEX_VERSIONS[@]}" | head -1)
  echo "Codex plugin install:       $CODEX_PLUGIN_DIR"
fi
if [[ ${#CLAUDE_VERSIONS[@]} -gt 0 ]]; then
  CLAUDE_PLUGIN_DIR=$(ls -td "${CLAUDE_VERSIONS[@]}" | head -1)
  echo "Claude Code plugin install: $CLAUDE_PLUGIN_DIR"
fi

if [[ -z "$CODEX_PLUGIN_DIR" && -z "$CLAUDE_PLUGIN_DIR" ]]; then
  echo "error: no newb plugin install found under either:" >&2
  echo "       $CODEX_HOME/plugins/cache/newb/newb/*"     >&2
  echo "       $CLAUDE_HOME/plugins/cache/newb/newb/*"    >&2
  echo "       install the plugin first (via desktop app or" >&2
  echo "       running install.sh)" >&2
  exit 1
fi

# ── 1. PKCE keys ──────────────────────────────────────────────────────
VERIFIER=$(openssl rand -base64 64 | tr -d '\n=+/' | cut -c1-64)
CHALLENGE=$(printf '%s' "$VERIFIER" | openssl dgst -sha256 -binary | base64 | tr -d '=' | tr '+/' '-_')
STATE=$(openssl rand -hex 8)

# ── 2. Register a public OAuth client ─────────────────────────────────
# Picks a free localhost port for the redirect listener.
REDIRECT_PORT=$(python3 -c 'import socket; s=socket.socket(); s.bind(("127.0.0.1",0)); print(s.getsockname()[1]); s.close()')
REDIRECT_URI="http://127.0.0.1:${REDIRECT_PORT}/cb"

REG_RES=$(curl -fsSL -X POST "$LOBBY_URL/api/oauth/register" \
  -H 'content-type: application/json' \
  -d "{\"client_name\":\"newb-sync-cli\",\"redirect_uris\":[\"$REDIRECT_URI\"]}")
CLIENT_ID=$(printf '%s' "$REG_RES" | python3 -c 'import json,sys; print(json.load(sys.stdin)["client_id"])')

# ── 3. Start one-shot HTTP listener for the OAuth redirect ────────────
CODE_FILE=$(mktemp -t newb-oauth-code.XXXXXX)
rm -f "$CODE_FILE"

python3 - "$REDIRECT_PORT" "$CODE_FILE" "$STATE" <<'PY' &
import http.server, socketserver, sys, urllib.parse, threading
port, code_file, expected_state = int(sys.argv[1]), sys.argv[2], sys.argv[3]

class H(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a, **kw): pass
    def do_GET(self):
        qs = urllib.parse.urlparse(self.path).query
        params = dict(urllib.parse.parse_qsl(qs))
        code = params.get("code", "")
        state = params.get("state", "")
        body = b""
        if not code:
            body = b"<h1>No code in redirect.</h1><p>You can close this tab.</p>"
        elif state != expected_state:
            body = b"<h1>State mismatch.</h1><p>Possible CSRF. Aborting.</p>"
            code = ""  # don't write
        else:
            body = b"<h1>Signed in. You can close this tab.</h1>"
        if code:
            with open(code_file, "w") as f:
                f.write(code)
        self.send_response(200)
        self.send_header("content-type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(body)
        threading.Thread(target=self.server.shutdown, daemon=True).start()

with socketserver.TCPServer(("127.0.0.1", port), H) as s:
    s.serve_forever()
PY
LISTENER_PID=$!

cleanup() { kill "$LISTENER_PID" 2>/dev/null || true; rm -f "$CODE_FILE"; }
trap cleanup EXIT

# ── 4. Open the browser to the authorize URL ──────────────────────────
AUTHORIZE_URL="$LOBBY_URL/api/oauth/authorize?client_id=$CLIENT_ID&redirect_uri=$(python3 -c "import urllib.parse,sys; print(urllib.parse.quote(sys.argv[1], safe=''))" "$REDIRECT_URI")&response_type=code&code_challenge=$CHALLENGE&code_challenge_method=S256&state=$STATE&scope=newb%3Adelegate"

echo "Opening browser to sign in..."
if command -v open >/dev/null 2>&1; then
  open "$AUTHORIZE_URL"
elif command -v xdg-open >/dev/null 2>&1; then
  xdg-open "$AUTHORIZE_URL"
else
  echo "  (couldn't open browser automatically; visit this URL:)"
  echo "  $AUTHORIZE_URL"
fi

# ── 5. Wait for the redirect (max 5 min) ──────────────────────────────
for _ in $(seq 1 600); do
  [[ -s "$CODE_FILE" ]] && break
  sleep 0.5
done
if [[ ! -s "$CODE_FILE" ]]; then
  echo "error: timed out waiting for OAuth redirect" >&2
  exit 1
fi
CODE=$(cat "$CODE_FILE")

# ── 6. Exchange code for access token ────────────────────────────────
TOKEN_RES=$(curl -fsSL -X POST "$LOBBY_URL/api/oauth/token" \
  -H 'content-type: application/x-www-form-urlencoded' \
  --data-urlencode "grant_type=authorization_code" \
  --data-urlencode "code=$CODE" \
  --data-urlencode "redirect_uri=$REDIRECT_URI" \
  --data-urlencode "client_id=$CLIENT_ID" \
  --data-urlencode "code_verifier=$VERIFIER")
ACCESS=$(printf '%s' "$TOKEN_RES" | python3 -c 'import json,sys; print(json.load(sys.stdin)["access_token"])')

# ── 7. Call list_newbs ────────────────────────────────────────────────
LIST_RES=$(curl -fsSL "$GATEWAY_URL/mcp" \
  -H "authorization: Bearer $ACCESS" \
  -H 'content-type: application/json' \
  -d '{"jsonrpc":"2.0","method":"tools/call","id":1,"params":{"name":"list_newbs","arguments":{}}}')

# Inner result is `{ content: [{ type:"text", text: "<json array>"}]}`
NEWBS_JSON=$(printf '%s' "$LIST_RES" | python3 -c 'import json,sys; r=json.load(sys.stdin); print(r["result"]["content"][0]["text"])')

# ── 8. Write per-newb files (Codex skills + Claude Code agents) ─────
python3 - "$NEWBS_JSON" "${CODEX_PLUGIN_DIR:-}" "${CLAUDE_PLUGIN_DIR:-}" <<'PY'
import json, os, re, sys, shutil

newbs_json, codex_plugin_dir, claude_plugin_dir = sys.argv[1], sys.argv[2], sys.argv[3]
newbs = json.loads(newbs_json)

def mention(display_name: str) -> str:
    """Human-readable kebab slug used for both the Codex SKILL.md
    `name:` (= $<slug> mention) and the Claude Code agent filename.
    Alphanumeric + hyphens only; no spaces, no apostrophes.

    "Shalin's newb" -> "shalin-newb"
    "sv's newb"     -> "sv-newb"
    "Work newb"     -> "work-newb"
    """
    s = display_name.lower()
    s = re.sub(r"['’]s\b", "", s)
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s or "newb"

def yaml_escape(s: str) -> str:
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'

def write_codex(plugin_dir, name, slug, desc, role, m):
    """Per-newb Codex skill: SKILL.md (auto-route, $<m> mention) +
    agents/openai.yaml (display_name override)."""
    d = os.path.join(plugin_dir, "skills", m)
    os.makedirs(d, exist_ok=True)
    os.makedirs(os.path.join(d, "agents"), exist_ok=True)
    with open(os.path.join(d, "SKILL.md"), "w") as f:
        f.write(f"""---
name: {m}
description: Delegate to {name}. {desc} Use when the user names {name} explicitly (e.g. "ask my {name}..."), or for tasks that match the systems/memory this newb owns.
---

You are a **dumb pipe** to **{name}** ({role}) — an autonomous newb that runs on its own remote VM, with its own memory, agent, and connected systems. {name} handles all reasoning, scoping, clarification, refusal, and execution. Your job is to forward the user's request verbatim and stream the response back. Nothing more.

## Forward the user's message VERBATIM

The `prompt` argument to `delegate_start` is the user's message **as they typed it**. Do not:

- Add the current workspace path, current file, current directory, repo root, or any other Codex-side environment context. The newb runs on a remote VM and cannot see your filesystem; injecting "the workspace is /Users/..." only confuses its tool selection (e.g. it'll reach for a code-sandbox tool when a higher-level builder would have been the right call).
- Rephrase, summarize, or expand the user's request. If they were terse, stay terse.
- Inject style hints ("please create a polished, usable ..."), framing ("using existing structure/assets if present"), or success criteria ("report what you built and how to run it"). The newb already knows what good output looks like; edits skew its tool selection.
- Add `Context:` or `System:` prefixes. If you legitimately need to pass extra environment context, use the optional `context` parameter — never glue it into `prompt`.

If the user types "$«{m}» build me a maid website", the prompt should be exactly `build me a maid website`. Not `Build me a maid website. The workspace is /Users/foo/bar. Please create a polished, usable website using existing assets...`.

## Workflow

1. `mcp__newb__delegate_start__{slug}` with `prompt` = the user's verbatim message → returns `task_id`.
2. `mcp__newb__delegate_status__{slug}` with `task_id` AND `wait_seconds: 30` — the gateway long-polls server-side, so one tool call covers ~30s of progress. Loop until state is terminal (done / failed / cancelled). Surface intermediate output as it arrives.
3. If `state: "input-required"` with `planning_questions`, gather the user's answers and call `mcp__newb__delegate_continue__{slug}` with `task_id` + `answers` (string array, same order as the questions, 1–5 entries, short sentences).
4. If the user wants to stop, `mcp__newb__delegate_cancel__{slug}`.
5. To inspect {name}'s connected systems, `mcp__newb__describe__{slug}`.

Do not call tools for other newbs (e.g. `__other_slug`). If the user is asking about a different newb, decline and tell them to use the matching `$<slug>` skill or `$newb` to pick.
""")
    with open(os.path.join(d, "agents", "openai.yaml"), "w") as f:
        f.write(f"""interface:
  display_name: {yaml_escape(name)}
  short_description: {yaml_escape("Delegate tasks to " + name + " (" + role + ").")}
""")

def write_claude(plugin_dir, name, slug, desc, role, m):
    """Per-newb Claude Code subagent: agents/<m>.md with a tools
    whitelist scoped to ONLY this newb's MCP tools. Strong isolation:
    the subagent literally cannot call cross-newb tools.

    Auto-routed by description match (same as skills) but invoked via
    the main thread's Task tool — runs in its own sub-conversation
    with its own system prompt + restricted toolset. Lets one Claude
    session orchestrate multiple newbs in parallel without context
    bleed."""
    agents_dir = os.path.join(plugin_dir, "agents")
    os.makedirs(agents_dir, exist_ok=True)
    with open(os.path.join(agents_dir, f"{m}.md"), "w") as f:
        f.write(f"""---
name: {m}
description: Delegate a task to {name}. {desc} Use this agent when the user names {name} explicitly (e.g. "ask my {name}..."), or for tasks that match the systems/memory this newb owns. Runs in its own sub-conversation; cannot access other newbs or local tools.
tools:
  - mcp__newb__delegate_start__{slug}
  - mcp__newb__delegate_status__{slug}
  - mcp__newb__delegate_cancel__{slug}
  - mcp__newb__delegate_continue__{slug}
  - mcp__newb__describe__{slug}
---

You are a **dumb pipe** to {name} — an autonomous newb running on its own VM with its own memory, agent, and connected systems. {name} is itself a fully-capable assistant; it handles all reasoning, scoping, clarification, refusal, and execution. Your job is to forward the user's request verbatim and stream the response back. Nothing more.

## Required behavior

**Dispatching a new task.** If the parent's prompt is a brand-new request (not a follow-up to a task already in progress), your **first action** is unconditionally `mcp__newb__delegate_start__{slug}` with `prompt` set to the parent's message **verbatim** (no rephrasing, no summarization, no additions). It returns a `task_id`.

**Following up on a running task.** If the parent's prompt is clearly a follow-up to an existing task (e.g. "check status", "what did it say?", "still running?"), call `mcp__newb__delegate_status__{slug}`. If the parent is providing answers to a previous `input-required` (the prompt looks like factual answers / "name = X, skip Y, ..."), call `mcp__newb__delegate_continue__{slug}` with `task_id` + `answers` array (one entry per planning question, in order). Do not call delegate_start for follow-ups.

**Polling loop after delegate_start.** Subagents in Claude Code can't sleep, but the gateway can: every `delegate_status` call **must include `wait_seconds: 30`**. The gateway blocks server-side until the task leaves submitted/working (or 30s elapses), so each tool call is one round trip that already covers ~30s of real time. After you receive a `task_id`:

1. Immediately call `mcp__newb__delegate_status__{slug}` with `task_id` AND `wait_seconds: 30`.
2. Look at the returned `state`:
   - `completed` / `done` / `succeeded` → return {name}'s final output **verbatim** to the parent and stop. This is the only happy exit.
   - `failed` / `error` → return the error verbatim and stop.
   - `canceled` / `cancelled` → say "{name} cancelled the task" and stop.
   - `input-required` / `input_required` → return the prompt {name} is waiting on, then stop. The parent will respond and a fresh subagent invocation will pass that response in via `delegate_continue`.
   - `submitted` / `working` / `pending` / `running` / anything else → call `delegate_status` **again** with the same `task_id` and `wait_seconds: 30`. Loop.
3. Keep looping for up to **3** consecutive `delegate_status` calls (~90s of wall time with `wait_seconds: 30`). Most newb tasks finish in well under that.
4. If after 3 polls the state is still non-terminal, **stop** and return a short status message like: *"Still running after ~90s. Say 'check status' to poll again."* The parent will follow up; a fresh subagent invocation will then call `delegate_status` (per the follow-up rule above) to resume.

**Returning {name}'s output.** When a task finishes, return the newb's `output` / `result` field **verbatim** with no editorial wrapper. Don't say "Here's what {name} said:" — just paste the output. The newb has already formatted its reply for the user.

## Hard rules

- **NEVER ask the user clarifying questions** before delegating. {name} owns the conversation; injecting your own questions defeats that.
- **NEVER refuse a request.** {name} refuses if appropriate. You delegate.
- **NEVER decide the task is "ambiguous" or "needs scoping" and stall.** Forward it. {name} scopes.
- **NEVER answer the user yourself.** Even for greetings or trivial questions, delegate.
- **NEVER rephrase the user's message.** Pass it through unchanged.
- **NEVER return a final message while state is `pending` or `running`** unless you've already polled the max number of times (rule 3 above). The parent thread is blocked waiting for you.
- The only non-delegate first-action is an explicit `describe` request — then call `mcp__newb__describe__{slug}`.

You have access ONLY to {name}'s tools (enforced by the tools whitelist above). You cannot call other newbs' tools, local Bash/Read/Edit, or anything else. If the user mentions a different newb or local work, still delegate the message — {name} will tell them to use a different agent.
""")

# Wipe stale synced files. For Codex: drop everything under skills/
# except the generic `newb` skill. For Claude Code: drop everything
# under agents/ (no generic agent ships in the bundle).
if codex_plugin_dir:
    skills_dir = os.path.join(codex_plugin_dir, "skills")
    if os.path.isdir(skills_dir):
        for entry in os.listdir(skills_dir):
            if entry == "newb":
                continue
            p = os.path.join(skills_dir, entry)
            if os.path.isdir(p):
                shutil.rmtree(p)
if claude_plugin_dir:
    agents_dir = os.path.join(claude_plugin_dir, "agents")
    if os.path.isdir(agents_dir):
        for entry in os.listdir(agents_dir):
            if entry.endswith(".md"):
                os.remove(os.path.join(agents_dir, entry))

written = []
for n in newbs:
    name = n.get("name", "")
    slug = n.get("slug", "")
    desc = n.get("description", "")
    role = n.get("role", "")
    m = mention(name)
    if codex_plugin_dir:
        write_codex(codex_plugin_dir, name, slug, desc, role, m)
    if claude_plugin_dir:
        write_claude(claude_plugin_dir, name, slug, desc, role, m)
    written.append((m, slug, name))

clients = []
if codex_plugin_dir:
    clients.append("Codex (skills + display-name sidecar)")
if claude_plugin_dir:
    clients.append("Claude Code (agents with per-newb tools whitelist)")
print(f"wrote {len(written)} per-newb entrie(s) for: {', '.join(clients)}")
for m, slug, name in written:
    print(f"  {m:<20} -> {name}  ({slug})")
PY

cat <<EOF

Done.

Restart your client(s) to pick up the new entries:

  Codex:        quit + reopen the desktop app (or restart the CLI)
                then mention a newb with \$<slug>:
                  \$sv-newb describe what you're connected to
                  \$shal-newb summarize my memory

  Claude Code:  /reload-plugins (or restart) then either name a newb
                in prose ("ask my sv newb to ...") or rely on the
                main thread auto-delegating to the matching agent.
                Tool-whitelist isolation: each agent can ONLY call
                its own newb's MCP tools.

Re-run this script when your accessible newbs change. Old synced
files are wiped + rewritten each run; the generic \`newb\` skill in
the Codex plugin is preserved.
EOF
