# flair builder (Codex)

Build and publish your own **expert agent** to the flair marketplace, from Codex.

Install via the marketplace, then say *"build my agent"*. The bundled skill interviews you, scaffolds a bundle, runs it on your own machine (`dev_call`), checks it with evals (`dev_eval_run`), and publishes it with the scripts in `scripts/` (self-contained Python 3). The agent runs hosted; anyone can pull it into Claude or Codex with free credits.

This directory is GENERATED from `newbworks/newb` (`python -m newb.marketplace.builder_skill --into <this checkout>`); edit it there.
