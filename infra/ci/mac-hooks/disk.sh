#!/bin/bash
# Free a benchmark Mac's disk after every job, so the next one never starts on a full disk. Below the low-water mark:
# drop pie-evals' scratch (imported artifacts, old builds, shrink and work dirs) and the uv/pip download caches, then
# the least recently used Hugging Face checkpoints until the mark is met. Engine venvs (baselines) stay: they are small
# and slow to rebuild. Run as the last step of every Mac job, pass or fail.
set -u
LOW_GIB=${PIE_EVALS_DISK_LOW_GIB:-100}
free_gib() { df -g "$HOME" | awk 'NR==2 {print $4}'; }
drop() { [ -e "$1" ] || return 0; echo "disk: dropping $1 ($(du -sh "$1" 2>/dev/null | cut -f1))"; rm -rf "$1"; }
before=$(free_gib)
echo "disk: ${before} GiB free (low-water ${LOW_GIB})"
[ "$before" -ge "$LOW_GIB" ] && exit 0
cache=${PIE_EVALS_CACHE:-$HOME/.cache/pie-evals}
for d in "$cache/artifacts" "$cache/builds" "$cache/shrink" "$cache/_work" "$HOME/pie-evals-out" /tmp/pie-evals-*; do drop "$d"; done
command -v uv >/dev/null && uv cache prune >/dev/null 2>&1 || true
drop "$HOME/Library/Caches/pip"
hub=${HF_HUB_CACHE:-${HF_HOME:-$HOME/.cache/huggingface}/hub}
# oldest access first: the checkpoints the recent jobs did not touch go before the ones they did
for repo in $(ls -dtu "$hub"/models--* 2>/dev/null | tail -r); do
  [ "$(free_gib)" -ge "$LOW_GIB" ] && break
  # pie-local checkpoints (models.yaml) are on no hub: once dropped, no job can fetch them again
  case "$repo" in */models--pie-local--*) continue ;; esac
  drop "$repo"
done
echo "disk: ${before} -> $(free_gib) GiB free"
exit 0
