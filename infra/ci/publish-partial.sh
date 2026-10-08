#!/bin/bash
# Partial publish from a running Mac: lift the records written so far into the Postgres store, under the run's tag.
# Needs PIE_EVALS_DB in the environment. Safe to repeat: a run's rows are replaced, not added.
set -uo pipefail
OUT="$1"
TIER="${2:-targeted}"
TAG="${3:-}"
KIND="${4:-}"
[ -s "$OUT/records.jsonl" ] || exit 0
args=(--tier "$TIER")
[ -n "$TAG" ] && args+=(--tag "$TAG")
[ -n "$KIND" ] && args+=(--tag-kind "$KIND")
.venv/bin/pie-evals collect "${args[@]}" "$OUT" >/dev/null || exit 0
