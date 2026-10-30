---
name: susan-okeefe
description: Blunt, specific MBA application feedback in the HBS Guru method: rate one essay on the Four Levels for free, then get a full-application sanity check, a ding report, or an interview prep brief — with Susan one escalation away for the call.
---

# Susan O'Keefe Demo

Blunt, specific MBA application feedback in the HBS Guru method: rate one essay on the Four Levels for free, then get a full-application sanity check, a ding report, or an interview prep brief — with Susan one escalation away for the call.

This plugin is a thin wrapper around the **Susan O'Keefe Demo** expert agent,
which runs **hosted** on the flair marketplace. The reasoning happens
server-side; this plugin connects your app to it over MCP (`https://agents.useflair.io/mcp/susan-okeefe/`). Using
it signs you in to newb.

## What it can do

- **Essay Rater (free)** (tool `essay_rater`)
- **One-Time Sanity Check** (tool `sanity_check`)
- **Ding Report** (tool `ding_report`)
- **Interview Prep Brief** (tool `interview_prep`)
- **Live Mock Interview (voice)** (tool `mock_interview`)

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
