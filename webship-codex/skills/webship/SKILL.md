---
name: webship
description: Reviews and ships production websites — audits existing sites, and builds + deploys new ones (React + shadcn/ui) to GitHub and Vercel.
---

# Shal

Reviews and ships production websites — audits existing sites, and builds + deploys new ones (React + shadcn/ui) to GitHub and Vercel.

This plugin is a thin wrapper around the **Shal** expert agent,
which runs **hosted** on the newb marketplace. The reasoning happens
server-side; this plugin connects your app to it over MCP (`https://agents.newb.works/mcp/webship/`). Using
it signs you in to newb.

## What it can do

- **Review a website** (tool `review`)
- **Build & ship a website** (tool `build`)

Call the tool that matches what you need; the hosted agent does the work and
returns the result. Credits are metered per run.
