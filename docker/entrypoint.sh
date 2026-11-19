#!/usr/bin/env bash
# Runs pie-bench inside a container: caches on the data folder, the machine id when the CLI cannot
# detect it (TPU), then `pie-bench <args>`. With no args and none in PIE_BENCH_ARGS a RunPod pod
# stays up for SSH; anywhere else it prints the help.
set -euo pipefail

provider=${PIE_BENCH_PROVIDER:-}
data=${PIE_BENCH_DATA:-}
if [ -z "$data" ]; then
  if [ "$provider" = runpod ] && [ -d /workspace ]; then data=/workspace
  elif [ -d /data ]; then data=/data
  else data=/root; fi
fi
mkdir -p "$data"
export PIE_BENCH_HOME=${PIE_BENCH_HOME:-$data/.pie-bench}
export PIE_BENCH_CACHE=${PIE_BENCH_CACHE:-$data/.cache/pie-bench}
export HF_HOME=${HF_HOME:-$data/.cache/huggingface}
export UV_CACHE_DIR=${UV_CACHE_DIR:-$data/.cache/uv}
export XDG_CONFIG_HOME=${XDG_CONFIG_HOME:-$data/.config}
export UV_LINK_MODE=${UV_LINK_MODE:-copy}

if [ -d /opt/rocm ]; then
  export ROCM_PATH=${ROCM_PATH:-/opt/rocm}
  export PATH=$PATH:$ROCM_PATH/bin
fi

if [ -n "${PIE_XLA_PLUGIN:-}" ]; then
  if [ -z "${PIE_BENCH_MACHINE:-}" ]; then
    acc=$(curl -fs -m 5 -H Metadata-Flavor:Google \
      http://metadata.google.internal/computeMetadata/v1/instance/attributes/accelerator-type || true)
    if [ -n "$acc" ]; then
      PIE_BENCH_MACHINE=$(/opt/pie-bench/bin/python - "$acc" "${TPU_ALL_CHIPS:-}" <<'PY'
import sys
from pie_bench.paths import MATRIX
import yaml
acc, all_chips = sys.argv[1], bool(sys.argv[2])
for p in yaml.safe_load((MATRIX / "platforms.yaml").read_text())["platforms"]:
    tpu = p.get("tpu") or {}
    if acc in (tpu.get("type"), p["id"]) and bool(tpu.get("all_chips")) == all_chips:
        print(p["id"])
        break
PY
)
      export PIE_BENCH_MACHINE
    fi
  fi
  chips=$(ls -d /dev/accel* 2>/dev/null | wc -l || true)
  [ "$chips" -gt 0 ] || chips=$(ls /dev/vfio 2>/dev/null | grep -cv '^vfio$' || true)
  if [ "${chips:-0}" -gt 1 ] && [ -z "${TPU_ALL_CHIPS:-}" ]; then
    export TPU_VISIBLE_CHIPS=0 TPU_CHIPS_PER_PROCESS_BOUNDS=1,1,1 TPU_PROCESS_BOUNDS=1,1,1
  fi
fi

if [ "$provider" = runpod ] && [ -n "${PUBLIC_KEY:-}" ] && command -v sshd >/dev/null; then
  mkdir -p /root/.ssh /run/sshd && chmod 700 /root/.ssh
  echo "$PUBLIC_KEY" >> /root/.ssh/authorized_keys && chmod 600 /root/.ssh/authorized_keys
  ssh-keygen -A >/dev/null 2>&1
  /usr/sbin/sshd
fi

if [ $# -eq 0 ] && [ -n "${PIE_BENCH_ARGS:-}" ]; then
  read -r -a args <<<"$PIE_BENCH_ARGS"
  set -- "${args[@]}"
fi
[ "${1:-}" = pie-bench ] && shift

if [ $# -eq 0 ]; then
  if [ "$provider" = runpod ]; then
    echo "pie-bench ready; ssh in and run: pie-bench run"
    exec sleep infinity
  fi
  exec pie-bench --help
fi

case "$1" in
  run|plan)
    cmd=$1; shift
    extra=()
    if [ -n "${PIE_BENCH_MACHINE:-}" ] && [[ " $* " != *" --machine"* ]]; then extra+=(--machine "$PIE_BENCH_MACHINE"); fi
    if [ "$cmd" = run ] && [ ! -t 0 ] && [[ " $* " != *" -y "* ]] && [[ " $* " != *" --yes "* ]]; then extra+=(-y); fi
    set -- "$cmd" "${extra[@]}" "$@"
    ;;
  bash|sh|/*) exec "$@" ;;
esac

if [ "$provider" = runpod ]; then
  pie-bench "$@" || echo "pie-bench exited $?"
  exec sleep infinity
fi
exec pie-bench "$@"
