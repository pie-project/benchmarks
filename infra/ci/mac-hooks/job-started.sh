#!/bin/bash
# Runs before every job on a benchmark Mac (ACTIONS_RUNNER_HOOK_JOB_STARTED).
# 1. one job per Mac: wait for any other runner's job on this machine to end
# 2. nothing left over: kill engines an earlier job left running
# 3. an idle GPU: at most 5% busy for 10 s before the job may start
set -u
. "$(dirname "$0")/common.sh"

worker=$(job_worker)
wait_s=${PIE_CI_LOCK_WAIT_S:-21600}
start=$(date +%s)
while ! mkdir "$LOCK" 2>/dev/null; do
  holder=$(cat "$LOCK/pid" 2>/dev/null || true)
  if [ -n "$holder" ] && ! kill -0 "$holder" 2>/dev/null; then
    echo "lock held by job worker $holder, which is gone: taking it"; rm -rf "$LOCK"; continue
  fi
  if [ -z "$holder" ] && [ $(( $(date +%s) - $(stat -f %m "$LOCK" 2>/dev/null || date +%s) )) -gt 60 ]; then
    rm -rf "$LOCK"; continue
  fi
  [ $(( $(date +%s) - start )) -gt "$wait_s" ] && { echo "::error::another CI job ($(cat "$LOCK/job" 2>/dev/null)) has held this Mac for ${wait_s}s"; exit 1; }
  if [ $(( ($(date +%s) - start) % 300 )) -lt 15 ]; then echo "waiting: this Mac is running $(cat "$LOCK/job" 2>/dev/null)"; fi
  sleep 15
done
echo "$worker" > "$LOCK/pid"
echo "${GITHUB_REPOSITORY:-?} run ${GITHUB_RUN_ID:-?} job ${GITHUB_JOB:-?}" > "$LOCK/job"
echo "machine lock taken by worker $worker after $(( $(date +%s) - start ))s"

kill_engines

quiet=0; t0=$(date +%s)
while :; do
  u=$(gpu_util)
  [ -z "$u" ] && { echo "GPU utilization unreadable: not waiting"; break; }
  if [ "$u" -le 5 ]; then quiet=$((quiet + 1)); else quiet=0; fi
  [ "$quiet" -ge 10 ] && { echo "GPU idle (${u}%) after $(( $(date +%s) - t0 ))s"; break; }
  [ $(( $(date +%s) - t0 )) -gt 1800 ] && { echo "::error::GPU still ${u}% busy after 30 min: something outside CI uses it"; rm -rf "$LOCK"; exit 1; }
  sleep 1
done
