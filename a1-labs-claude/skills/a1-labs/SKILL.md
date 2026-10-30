---
name: a1-labs
description: Paste in a messy marketplace case and get the verdict, the internal playbook, and a ready-to-send reply — written the way an experienced trust & safety ops lead would handle it.
---

# a1 labs

Paste in a messy marketplace case and get the verdict, the internal playbook, and a ready-to-send reply — written the way an experienced trust & safety ops lead would handle it.

This plugin is a thin wrapper around the **a1 labs** expert agent,
which runs **hosted** on the flair marketplace. The reasoning happens
server-side; this plugin connects your app to it over MCP (`https://agents.useflair.io/mcp/a1-labs/`). Using
it signs you in to newb.

## What it can do

- **Resolve a marketplace case** (tool `resolve_case`)

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
