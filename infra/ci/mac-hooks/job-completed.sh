#!/bin/bash
# Runs after every job on a benchmark Mac (ACTIONS_RUNNER_HOOK_JOB_COMPLETED):
# no engine outlives its job, and the machine lock goes back.
set -u
. "$(dirname "$0")/common.sh"
kill_engines
worker=$(job_worker)
if [ "$(cat "$LOCK/pid" 2>/dev/null)" = "$worker" ]; then rm -rf "$LOCK"; echo "machine lock released"; fi
exit 0
