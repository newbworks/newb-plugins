---
description: Run the hosted Recruiting Copilot expert agent
argument-hint: [what you need help with — a role, resume, or outreach]
---
Use ONLY the `recruiting-copilot` MCP tools (the `mcp__recruiting-copilot__*` tools) to help the
user with: $ARGUMENTS

Pick the tool that matches the need:
- `discover_candidate_edge` — find their distinctive strength
- `find_matching_opportunities` — rank companies/roles that fit
- `tailor_resume` — tailor a resume to a role
- `prepare_recruiter_outreach` — draft recruiter outreach
- `ask` — anything else, in natural language

This agent runs hosted; its own tools do the work. Do NOT delegate to a personal newb,
`delegate_start`, or any other agent, even if such tools are available.
