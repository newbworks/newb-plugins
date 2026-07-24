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
