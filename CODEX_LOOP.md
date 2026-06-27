# Codex Loop

The loop is driven by:

- `codex/phase_manifest.json`
- `codex/phase_cards/P00.md` through `codex/phase_cards/P16.md`
- `codex/loop_state.json`
- guard scripts in `scripts/`

Every phase records auditable artifacts under `artifacts/phase-PXX/`, including `commands.jsonl`, `commands.log`, `result.json`, `notes.md`, and `changed_files.txt`.

The only valid phase advancement is `python3 scripts/codex_next.py pass --phase PXX --json`, which reruns the phase gate before writing PASS.
