#!/bin/bash
set -uo pipefail
OUT="$1"
TIER="${2:-targeted}"
[ -s "$OUT/records.jsonl" ] || exit 0
TMP=$(mktemp -d)
trap 'git worktree remove --force "$TMP" >/dev/null 2>&1; rm -rf "$TMP"' EXIT
git fetch -q origin main && git worktree add -q --detach "$TMP" origin/main || exit 0
.venv/bin/pie-evals --matrix "$TMP/matrix" --store "$TMP/store" collect --tier "$TIER" "$OUT" >/dev/null || exit 0
cd "$TMP"
git add store
git diff --cached --quiet && exit 0
git -c user.name="pie-evals-bot" -c user.email="pie-evals-bot@users.noreply.github.com" commit -q -m "store: partial $(head -c 40 "$OUT/run_id.txt")"
for i in 1 2 3; do
  git push -q origin HEAD:main && exit 0
  git pull -q --rebase origin main || exit 0
done
