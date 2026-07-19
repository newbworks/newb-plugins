---
name: ymgrad-demo
description: DEMO study-abroad admissions counselor (YMGrad-style): India-anchored and honest about your real chances at US master's programs. Uses clearly-labeled fictional sample data.
---

# YMGrad-Demo Admissions Counselor

DEMO study-abroad admissions counselor (YMGrad-style): India-anchored and honest about your real chances at US master's programs. Uses clearly-labeled fictional sample data.

This plugin is a thin wrapper around the **YMGrad-Demo Admissions Counselor** expert agent,
which runs **hosted** on the newb marketplace. The reasoning happens
server-side; this plugin connects your app to it over MCP (`https://agents.newb.works/mcp/ymgrad-demo/`). Using
it signs you in to newb.

## What it can do

- **Profile shortlist** (tool `profile_shortlist`)
- **Admit probability** (tool `admit_probability`)
- **SOP review** (tool `sop_review`)
- **SOP draft** (tool `sop_draft`)
- **LOR draft** (tool `lor_draft`)
- **F-1 visa mock** (tool `visa_mock`)
- **Ask a counselor** (tool `ask_counselor`)
- **UniPredict sample (free taster)** (tool `unipredict_sample`)

Call the tool that matches what you need; the hosted agent does the work and
returns the result.
## How to use it (for the model)

Invoke this connector's MCP tools DIRECTLY and wait for each call to finish —
a hosted run can take a minute or two; that latency is normal, not a failure.
Present the tool's returned text to the user as the result. Never fabricate
progress UI, widgets, or interactive result panels around a call — the result
IS the returned text — and never tell the user the agent "needs setup" unless
a tool call actually returned an error saying so.

While a call runs, this connector streams MCP progress notifications (live
status + elapsed-time heartbeats). If your client surfaces them, relay them
to the user as brief status updates while you wait. Credits are metered per run.
