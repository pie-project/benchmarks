#!/bin/bash
# Clean a benchmark Mac before a job: nothing from a previous test or a person's session may share it.
# Quits every app the runner's user has open (Etude, Activity Monitor, Stats, browsers...) except the ones
# the machine needs to stay reachable, kills inference engines an earlier job left, then waits for an idle GPU.
# Run by the runner's job-started hook and as the first step of every benchmark job.
set -u
. "$(dirname "$0")/common.sh"

# apps a runner must keep: the tailnet (else the Mac drops off), and the runner itself
keep='Tailscale|Runner\.|actions-runner'
apps=$(ps -U "$(id -u)" -o pid=,command= 2>/dev/null | grep -E '/(Applications|Users/[^/]+/Applications)/[^/]+\.app/Contents/MacOS/' | grep -Ev "$keep" || true)
if [ -n "$apps" ]; then
  echo "quitting apps: $(echo "$apps" | sed -E 's#.*/([^/]+)\.app/Contents/MacOS/.*#\1#' | sort -u | tr '\n' ' ')"
  echo "$apps" | awk '{print $1}' | xargs kill 2>/dev/null || true
  sleep 5
  echo "$apps" | awk '{print $1}' | xargs kill -9 2>/dev/null || true
fi

kill_engines

# a lit display (an animated wallpaper, a screensaver) keeps WindowServer drawing on the GPU
pmset displaysleepnow 2>/dev/null || true

quiet=0; t0=$(date +%s)
while :; do
  u=$(gpu_util)
  [ -z "$u" ] && { echo "GPU utilization unreadable: not waiting"; break; }
  if [ "$u" -le 5 ]; then quiet=$((quiet + 1)); else quiet=0; fi
  [ "$quiet" -ge 10 ] && { echo "clean: GPU idle (${u}%) after $(( $(date +%s) - t0 ))s"; break; }
  if [ $(( $(date +%s) - t0 )) -gt 1800 ]; then
    echo "::error::GPU still ${u}% busy after 30 min: $(ps -Ao %cpu,comm -r | sed -n 2,4p | tr -s ' ' | tr '\n' ';')"
    exit 1
  fi
  sleep 1
done
