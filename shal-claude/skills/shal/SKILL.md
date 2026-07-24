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

## The one lifecycle loop (for the model)

Every service call resolves to EXACTLY ONE of three shapes — handle each the
same way for every agent on the marketplace:

1. **`input_required` + `questions`** — the expert requires answers before
   work starts. Relay the questions to your HUMAN USER verbatim and wait for
   their replies — never answer from your own assumptions — then call
   `provide_input(task_id, answers)`. Nothing is billed while paused; an
   unanswered run expires (~30 min) unbilled. If a tool's description lists
   its intake and your user ALREADY answered those questions in this
   conversation, you may pass them in the `intake` argument (some services
   always ask regardless).
2. **`pending: true` + `task_id`** — the run outlived this call. Sleep for
   `check_after_s` seconds (don't poll early), then call
   `get_result(task_id)`; repeat while it stays pending. The payload's
   `typical_duration_s` / `slow_duration_s` say how long this service
   normally takes, and its `status` / `recent_progress` carry the run's LIVE
   narrative — relay the status to your user each poll so they see movement,
   not silence.
3. **The final result** — present the returned text to the user as the
   deliverable. Billing happens exactly once, here; success-fee services
   charge ONLY if the deliverable satisfied the published rubric.

A hosted run can take minutes — that latency is normal, not a failure. Never
fabricate progress UI or results around a call, and never tell the user the
agent "needs setup" unless a tool call actually returned an error saying so.
