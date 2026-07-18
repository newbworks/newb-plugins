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
returns the result. Credits are metered per run.
