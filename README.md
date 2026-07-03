# newb plugins

A single MCP plugin that exposes the user's newbs to coding agents. Ships as two parallel packages — one for Claude Code, one for Codex — sharing the same skill body and the same backend (lobby OAuth + `gateway.newb.works/mcp`).

## Layout

```
newb-plugins/
  .claude-plugin/marketplace.json    # Claude Code marketplace entry
  .agents/plugins/marketplace.json   # Codex marketplace entry
  claude/                            # Claude Code plugin
    .claude-plugin/plugin.json
    .mcp.json
    skills/newb/SKILL.md
    sync-newbs.sh
    README.md
  codex/                             # Codex plugin
    .codex-plugin/plugin.json
    .mcp.json
    skills/newb/SKILL.md
    install.sh
    sync-newbs.sh
    README.md
```

Both marketplace manifests live at the repo root so users can install via `/plugin marketplace add newbworks/newb-plugins` (Claude Code) or `codex plugin marketplace add newbworks/newb-plugins` (Codex).

## How it works

1. Plugin's MCP config points at `https://gateway.newb.works/mcp` with no auth header.
2. First MCP call → gateway returns `401` with `WWW-Authenticate: Bearer resource_metadata=...`.
3. Client (Claude Code or Codex) walks the standard OAuth 2.1 + PKCE flow at `https://lobby.newb.works/api/oauth/*`, sign-in gated by Supabase Google SSO.
4. After auth the gateway enumerates the user's newbs and exposes one set of MCP tools per newb (`delegate_start__<slug>`, `delegate_status__<slug>`, `describe__<slug>`, ...) plus a `list_newbs` enumerator.
5. The agent picks tools by name; the gateway routes by suffix to the right VM via the existing WebSocket hub.

No secrets in the plugin bundle. Tokens live in the client's secure storage.

## Per-newb skills / agents

After install, run `sync-newbs.sh` (lives in both `claude/` and `codex/`) to generate one skill (Codex) or one subagent (Claude Code) per newb you have access to. See the per-client READMEs for the exact paths.

## Local development

Test the Claude Code plugin against a running gateway:

```bash
claude --plugin-dir ./claude
```

Then trigger any `mcp__newb__*` call. Claude will prompt for OAuth on first use.

## Issues

Report issues at https://github.com/newbworks/newb-plugins/issues.

## newb-builder — for experts

This marketplace also ships **`newb-builder`**, a plugin that lets a domain
expert turn their expertise into a hosted agent others can install:

```bash
codex plugin marketplace add newbworks/newb-plugins    # Codex — then install: newb-builder
/plugin marketplace add newbworks/newb-plugins          # Claude Code
```

Install `newb-builder`, then say *"build my agent"*. It interviews you,
scaffolds a bundle, helps you write the instructions, validates, and publishes
it live (self-contained Python scripts under `builder-*/scripts/` — no CLI or
repo needed). Published agents run **hosted** and are pullable into Claude or
Codex with free credits. Packages: `builder-codex/` (Codex) and
`builder-claude/` (Claude Code).
