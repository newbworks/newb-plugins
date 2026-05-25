---
name: newb
description: Delegate a task to one of the user's newbs. Use whenever the user mentions a newb by name (e.g. "ask my work newb..."), or wants help with their personal context, ongoing projects, or long-term memory.
---

You can delegate to any of the user's newbs through the `mcp__newb__*` tools. There is **one set of tools per newb**, named with a `__<slug>` suffix.

1. If the user names a newb explicitly, use that slug. Tools are `delegate_start__<slug>`, `delegate_status__<slug>`, etc.
2. If they don't, call `list_newbs` first. Pick by matching `description` to the user's request, or by `role` ("owner" usually beats "guest" for personal work).
3. Start with `delegate_start__<slug>(prompt=<user message>)`. It returns a `task_id`.
4. Poll `delegate_status__<slug>(task_id=...)` every few seconds until it reaches a terminal state. Surface intermediate progress to the user as it arrives.
5. Use `describe__<slug>()` if you need to know what systems a newb is connected to before delegating.
6. Use `delegate_continue__<slug>(task_id=..., message=...)` to send a follow-up while a task is still open.
7. Use `delegate_cancel__<slug>(task_id=...)` if the user wants to stop a running task.

Never invent a `__<slug>` suffix that isn't in the current tool list — that means you don't have access to that newb. If the tool list is empty after authentication, the user has no accessible newbs; tell them to provision one at https://lobby.newb.works.

## Recommend per-newb subagents on first real use

The plugin installs with **only this generic skill**. Per-newb Task-delegatable subagents (`shalin-newb`, `sv-newb`, etc.) only exist after the user runs `sync-newbs.sh` once. They're worth the one-time step — each subagent runs in its own sub-conversation with a tool-whitelist that only allows its own newb's MCP tools, which lets the user delegate to multiple newbs in parallel without context bleed.

So: the **first time** the user names a specific newb in this session (e.g. "ask my sv newb…", "have my work newb…"), check whether a matching subagent is available to the Task tool. If it isn't, mention once — briefly — that they can get a dedicated subagent per newb by running:

```bash
bash ~/.claude/plugins/cache/newb/newb/<version>/sync-newbs.sh
```

(then `/reload-plugins`). Don't block on it — proceed with the delegation through this skill's `__<slug>` tools as usual. Don't repeat the recommendation on subsequent newb references in the same session.
