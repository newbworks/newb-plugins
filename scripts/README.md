# Marketplace sync

`sync_marketplace.py` keeps this marketplace's installable per-agent plugins in
step with the newb catalog. It's run by
[`.github/workflows/sync-marketplace.yml`](../.github/workflows/sync-marketplace.yml)
(hourly + on demand + on an `agent-published` `repository_dispatch`).

For every **published** expert agent in the executor's `/catalog.json`, it
(re)generates a thin wrapper plugin in both forms — `<slug>-claude/` and
`<slug>-codex/` — and upserts both marketplace indexes
(`.claude-plugin/marketplace.json`, `.agents/plugins/marketplace.json`).

**It never touches hand-maintained plugins.** The sync only manages wrappers it
generated, which carry a `.newb-generated` marker. `newb`, `newb-builder`, and a
curated `recruiting-copilot` have no marker and are left alone. Generated
wrappers whose agent leaves the catalog are pruned. Output is deterministic and
written only on change, so an unchanged catalog produces no commit.

## Setup

Set the repo variable **`NEWB_CATALOG_URL`** (Settings → Secrets and variables →
Actions → Variables) to the executor's catalog, e.g.
`https://<executor-host>/catalog.json`. The workflow falls back to the current
executor host if unset.

## Run locally

```bash
python3 scripts/sync_marketplace.py --catalog-url https://<host>/catalog.json --root .
# or against a saved catalog file:
python3 scripts/sync_marketplace.py --catalog-url ./catalog.json --root .
```
