---
name: shal
description: Reviews websites with a standards-based framework, visualizes an improved concept, then builds and deploys polished changes through GitHub and Vercel.
---

# shal

Reviews websites with a standards-based framework, visualizes an improved concept, then builds and deploys polished changes through GitHub and Vercel.

This plugin is a thin wrapper around the **shal** expert agent,
which runs **hosted** on the newb marketplace. The reasoning happens
server-side; this plugin connects your app to it over MCP (`https://agents.newb.works/mcp/shal/`). Using
it signs you in to newb.

## What it can do

- **Review a website** (tool `review_website`)
- **Build or improve a website** (tool `build_website`)

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
