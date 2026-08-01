---
name: idea-reviewer
description: See if your startup idea will win or lose against a specific thesis about the future.
---

# idea-reviewer

See if your startup idea will win or lose against a specific thesis about the future.

This plugin is a thin wrapper around the **idea-reviewer** expert agent,
which runs **hosted** on the newb marketplace. The reasoning happens
server-side; this plugin connects your app to it over MCP (`https://agents.newb.works/mcp/idea-reviewer/`). Using
it signs you in to newb.

## What it can do

- **Idea Verdict** (tool `idea_verdict`)

Call the tool that matches what you need; the hosted agent does the work and
returns the result. Each tool's description states its price, typical
duration, and the intake it asks for.

## Conduct (for the model)

The platform surfaces are self-describing — follow them exactly:
- **Every tool result tells you the next step.** A paused run returns its
  questions and says to relay them to your user; a pending run says how long
  to sleep and carries live `status` to share; the final result is the
  deliverable. Do what the payload says — nothing more.
- A hosted run can take minutes; that latency is normal, not a failure.
- Never fabricate progress, results, or setup errors around a call — the
  result IS the returned text.
