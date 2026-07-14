---
name: job-finder
description: Finds roles that actually fit you. Pulls from job boards and a curated hiring network, screens for fit against your background, and drafts tailored outreach to the people who make the call.
---

# Top Job Finder

Finds roles that actually fit you. Pulls from job boards and a curated hiring network, screens for fit against your background, and drafts tailored outreach to the people who make the call.

This plugin is a thin wrapper around the **Top Job Finder** expert agent,
which runs **hosted** on the newb marketplace. The reasoning happens
server-side; this plugin connects your app to it over MCP (`https://46-224-211-61.sslip.io/mcp/job-finder/`). Using
it signs you in to newb.

## What it can do

- **Find matching jobs** (tool `find_jobs`)
- **Draft tailored outreach** (tool `tailor_outreach`)

Call the tool that matches what you need; the hosted agent does the work and
returns the result. Credits are metered per run.
