# Agent Contract

This repository is operated through the controlled Codex loop. The canonical phase manifest is `codex/phase_manifest.json`, generated from the Markdown bundle during P00.

Agents must use `scripts/codex_next.py next --json`, claim/progress the returned phase, modify only that phase's allowed paths plus global control paths, run and record pre-gate commands, pass `scripts/phase_gate.py check`, then `scripts/codex_next.py pass`.

Do not edit `codex_valkey_loop_md_bundle/` during loop execution. Do not convert skipped, fake, inconclusive, or unvalidated runtime evidence into production Valkey PASS claims.
