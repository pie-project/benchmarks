#!/bin/bash
# Partial publish from a running Mac: lift the records written so far into the Postgres store.
# Needs PIE_EVALS_DB in the environment. Safe to repeat: a run's rows are replaced, not added.
set -uo pipefail
OUT="$1"
TIER="${2:-targeted}"
[ -s "$OUT/records.jsonl" ] || exit 0
.venv/bin/pie-evals collect --tier "$TIER" "$OUT" >/dev/null || exit 0
