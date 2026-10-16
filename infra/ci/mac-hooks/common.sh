# Shared by the runner hooks on a benchmark Mac. One CI job owns the machine at a time,
# whichever of its runners took the job: a lock directory names the owning job's worker.
LOCK=/tmp/pie-ci-machine.lock

# the Runner.Worker this hook runs under: the pid that lives exactly as long as the job
job_worker() {
  local pid=$$
  while [ "$pid" -gt 1 ]; do
    case "$(ps -o command= -p "$pid" 2>/dev/null)" in *Runner.Worker*) echo "$pid"; return ;; esac
    pid=$(ps -o ppid= -p "$pid" 2>/dev/null | tr -d ' ')
    [ -n "$pid" ] || break
  done
  echo $$
}

# every inference engine a benchmark starts, and anything serving the way they do
kill_engines() {
  local found
  # the runner runs hooks under bash -e -o pipefail: a search that finds nothing must not end the job
  found=$(pgrep -U "$(id -u)" -fl '(^|/)(pie|llama-server|splash)( |$)|mlx_lm[. ]server|launcher\.py serve' 2>/dev/null | grep -v pgrep || true)
  [ -z "$found" ] && return 0
  echo "leftover engines: $(echo "$found" | tr '\n' ';')"
  echo "$found" | awk '{print $1}' | xargs kill 2>/dev/null || true
  sleep 5
  echo "$found" | awk '{print $1}' | xargs kill -9 2>/dev/null || true
  return 0
}

# the GPU's busy share in percent, empty when unreadable
gpu_util() { ioreg -r -d 1 -c IOAccelerator 2>/dev/null | sed -n 's/.*"Device Utilization %"=\([0-9]*\).*/\1/p' | head -1 || true; }
