# newb plugins

The install surface of the **flair** marketplace ([marketplace.useflair.io](https://marketplace.useflair.io)):
one Claude Code plugin and one Codex plugin per published expert agent, plus
**`flair-builder`**, the plugin experts use to build and publish their own. Both
marketplace indexes live at the repo root, so one command adds everything:

```bash
/plugin marketplace add newbworks/newb-plugins          # Claude Code
codex plugin marketplace add newbworks/newb-plugins     # Codex
```

## Layout

```
newb-plugins/
  .claude-plugin/marketplace.json    # Claude Code index
  .agents/plugins/marketplace.json   # Codex index
  builder-claude/                    # flair-builder for Claude Code
  builder-codex/                     # flair-builder for Codex
  <slug>-claude/, <slug>-codex/      # one wrapper pair per published agent
  scripts/sync_marketplace.py        # regenerates the wrappers + indexes
```

## Agent wrappers

Each published agent ships as a thin wrapper whose `.mcp.json` points at that
agent's hosted endpoint (`https://agents.newb.works/mcp/<slug>/`). Install one
with `/plugin install <slug>@newb` (Claude Code) or `codex plugin add <slug>@newb`
(Codex). The first call signs you in with your marketplace account (OAuth) and
starts you with free credits; the agent itself runs hosted, on the expert's
model and tools.

Wrappers carry a `.newb-generated` marker and are regenerated from the live
catalog hourly, on demand, and the moment an agent is published — hand edits
are overwritten. See [`scripts/README.md`](scripts/README.md).

## flair-builder — for experts

**`flair-builder`** turns a domain expert's process into a hosted agent others
can install:

```bash
/plugin install flair-builder@newb      # Claude Code
codex plugin add flair-builder@newb     # Codex
```

Then say *"build my agent"*. It interviews you, scaffolds a bundle, runs it on
your own machine, checks it with evals, and publishes it live — self-contained
Python scripts under `builder-*/scripts/`, no CLI or repo needed. The agent then
appears here as its own wrapper.

`builder-claude/` and `builder-codex/` are generated from
[`newbworks/newb`](https://github.com/newbworks/newb) (`plugins/flair-builder/`,
rendered from `builder/skill/`): that repo's sync workflow mirrors the skill and
scripts on every push, and `python -m newb.marketplace.builder_skill --into
<this checkout>` writes the manifests, `.mcp.json` and READMEs. Edit them there.

## Issues

Report issues at https://github.com/newbworks/newb-plugins/issues.
