---
name: swetha-garimalla
description: Assesses AI-native biotech companies from their SEC filings, pipeline, patents, people, customers, insiders, earnings and news — a commercial-viability verdict with an FCF/ROIC workbook, and a read on whether the company is steered by investors, employees or clients.
---

# Swetha Garimalla — AI Biotech Viability

Assesses AI-native biotech companies from their SEC filings, pipeline, patents, people, customers, insiders, earnings and news — a commercial-viability verdict with an FCF/ROIC workbook, and a read on whether the company is steered by investors, employees or clients.

This plugin is a thin wrapper around the **Swetha Garimalla — AI Biotech Viability** expert agent,
which runs **hosted** on the flair marketplace. The reasoning happens
server-side; this plugin connects your app to it over MCP (`https://agents.useflair.io/mcp/swetha-garimalla/`). Using
it signs you in to newb.

## What it can do

- **Commercial viability assessment** (tool `viability_assessment`)
- **Stakeholder sentiment & strategic direction** (tool `stakeholder_direction`)

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
