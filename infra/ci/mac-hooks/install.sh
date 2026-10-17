#!/bin/bash
# Install the job hooks on this Mac's runners: ./install.sh <dir holding the hooks>.
# Each runner reads ACTIONS_RUNNER_HOOK_* from its .env when its listener starts, so an idle
# listener is restarted (launchd brings it back); a busy one picks the hooks up after its job.
set -eu
src=${1:-$(cd "$(dirname "$0")" && pwd)}
dst="$HOME/.pie-ci-hooks"
mkdir -p "$dst" && cp "$src"/common.sh "$src"/clean.sh "$src"/job-started.sh "$src"/job-completed.sh "$dst"/ && chmod +x "$dst"/*.sh
for r in "$HOME"/workspace/pie-evals/runner "$HOME"/workspace/pie-evals/runner-2 "$HOME"/actions-runner*; do
  [ -f "$r/.runner" ] || continue
  touch "$r/.env"
  grep -v '^ACTIONS_RUNNER_HOOK_JOB_' "$r/.env" > "$r/.env.new" || true
  { echo "ACTIONS_RUNNER_HOOK_JOB_STARTED=$dst/job-started.sh"; echo "ACTIONS_RUNNER_HOOK_JOB_COMPLETED=$dst/job-completed.sh"; } >> "$r/.env.new"
  mv "$r/.env.new" "$r/.env"
  listener=$(pgrep -f "$r/bin/Runner.Listener" || true)
  if [ -z "$listener" ] || pgrep -f "$r/bin/Runner.Worker" >/dev/null; then
    echo "$r: hooks set${listener:+ (busy: they apply when its listener next starts)}"; continue
  fi
  # a user LaunchAgent restarts through launchctl; a system LaunchDaemon (KeepAlive) comes back after the kill
  agent=$(grep -l "$r/" "$HOME"/Library/LaunchAgents/*.plist 2>/dev/null | head -1)
  if [ -n "$agent" ]; then
    launchctl kickstart -k "gui/$(id -u)/$(basename "$agent" .plist)" && echo "$r: hooks set, listener restarted"
  else
    kill "$listener" && echo "$r: hooks set, listener restarted by launchd"
  fi
done
