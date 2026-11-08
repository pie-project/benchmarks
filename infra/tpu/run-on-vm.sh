#!/usr/bin/env bash
# On a fresh Cloud TPU VM (any generation: platforms.yaml tpu:): install the toolchains, check out pie at a
# commit, and run one pie-evals job on the XLA engine. Started by .github/workflows/tpu.yml from
# the unpacked pie-evals tree; the node builds pie with --features xla, imports the model as a
# .xla.zt and writes out/<job_id>/records.jsonl. A job with vLLM or SGLang cells also gets their TPU builds
# (vllm-tpu, sglang-jax at the engines.yaml pins) in their own venvs, installed beside the toolchains.
#
#   bash infra/tpu/run-on-vm.sh <pie_commit> jobs/<job_id>.json [jobs/<job_id>.json ...]
# With PARITY_ARTIFACTS (comma-separated ids) set, no job: pie-evals-node parity against vllm-tpu at the
# engines.yaml pin on PARITY_PLATFORM, tagged PARITY_TAG, into out/parity (its store: out/parity/store).
set -euo pipefail
commit=$1
# one or more job files: a plan the budget split into shards runs them one after another on this VM
jobs=("${@:2}")
job=${jobs[0]:-}
here=$(pwd)

# a data disk (platforms.yaml tpu.data_disk_gb) holds ~/.cache: the checkpoints, their imports, the venvs
root=$(lsblk -no PKNAME "$(findmnt -no SOURCE /)" 2>/dev/null | head -n 1 || true)
data=$(lsblk -dpno NAME,TYPE | awk -v r="/dev/$root" '$2 == "disk" && $1 != r {print $1; exit}' || true)
if [ -n "$data" ] && [ -z "$(lsblk -no MOUNTPOINT "$data" | tr -d '[:space:]')" ] && ! mountpoint -q "$HOME/.cache"; then
  sudo blkid "$data" >/dev/null 2>&1 || sudo mkfs.ext4 -q -F "$data"
  mkdir -p "$HOME/.cache" && sudo mount "$data" "$HOME/.cache" && sudo chown "$(id -u):$(id -g)" "$HOME/.cache"
  df -h "$HOME/.cache"
fi

# a fresh VM's unattended-upgrades holds the dpkg lock for minutes, past 15 once (v5e 41764965822): stop it, finish what it left
# (the services stopped, a run already started by the timer killed by name: v5e 41797489994 waited 16 min on pid "unattended-upgr")
sudo systemctl stop apt-daily.timer apt-daily-upgrade.timer unattended-upgrades.service apt-daily.service apt-daily-upgrade.service 2>/dev/null || true
for _ in 1 2 3 4 5 6; do sudo pkill -9 -f unattended-upgrade 2>/dev/null || break; sleep 5; done
sudo DEBIAN_FRONTEND=noninteractive dpkg --configure -a 2>/dev/null || true
sudo apt-get -o DPkg::Lock::Timeout=900 update -q
sudo DEBIAN_FRONTEND=noninteractive apt-get -o DPkg::Lock::Timeout=900 install -y -q --no-install-recommends \
  build-essential cmake ninja-build pkg-config libssl-dev git curl ca-certificates python3-yaml jq
command -v rustup >/dev/null || curl -sSf https://sh.rustup.rs | sh -s -- -y --profile minimal --default-toolchain none
command -v uv >/dev/null || curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.cargo/bin:$HOME/.local/bin:$PATH"

cd "$here"
uv venv -q --python 3.12 .venv
uv pip install -q --python .venv/bin/python --torch-backend cpu -e ".${PARITY_ARTIFACTS:+[quality]}"

# the TPU builds of vLLM and SGLang, in the background while the toolchains install: the node then finds
# the venvs ready (baselines.ensure_baseline, the same call it makes itself when a venv is missing)
pids=()
for engine in vllm sglang; do
  if [ -n "${PARITY_ARTIFACTS:-}" ]; then
    [ "$engine" = vllm ] || continue
    pin=${PARITY_VLLM_PIN:-$(.venv/bin/python -c "from pie_evals.plan.matrix import Matrix; print(Matrix.load('matrix').engines['vllm'].pin)")}
  else
    pin=$(jq -rs "map(.baseline_versions.$engine // empty) | first // empty" "${jobs[@]}" 2>/dev/null || true)
  fi
  [ -n "$pin" ] || continue
  echo "$engine (TPU build) $pin: installing in the background"
  .venv/bin/python -c "import sys; from pie_evals.node.baselines import ensure_baseline; print(ensure_baseline(sys.argv[1], sys.argv[2], backend='xla'))" "$engine" "$pin" \
    > "$HOME/$engine-tpu-install.log" 2>&1 &
  pids+=("$engine:$!")
done

# pie at the commit; the node finds this checkout at that HEAD and only builds it
export PIE_ROOT="$HOME/pie"
if [ ! -d "$PIE_ROOT/.git" ]; then
  git init -q "$PIE_ROOT"
  git -C "$PIE_ROOT" remote add origin https://github.com/pie-project/pie.git
fi
git -C "$PIE_ROOT" fetch -q --depth 1 origin "$commit"
git -C "$PIE_ROOT" checkout -q --force FETCH_HEAD
# rust-toolchain.toml: the pinned channel with the wasm32-wasip2 target the inferlets build for
(cd "$PIE_ROOT" && rustup toolchain install)

# the PJRT plugin engine-xla dlopens: libtpu, at the version its vendored pjrt_c_api.h is
# generated from (crates/engine-xla/pjrt/bindgen.sh)
uv venv -q --python 3.12 "$HOME/libtpu"
uv pip install -q --python "$HOME/libtpu/bin/python" "libtpu==${LIBTPU_VERSION:-0.0.48}"
PIE_XLA_PLUGIN=$("$HOME/libtpu/bin/python" -c 'import libtpu, os; print(os.path.join(os.path.dirname(libtpu.__file__), "libtpu.so"))')
export PIE_XLA_PLUGIN
[ -f "$PIE_XLA_PLUGIN" ] || { echo "no libtpu.so at $PIE_XLA_PLUGIN"; exit 1; }

# KERNELS_TEST (tpu.yml `kernels`): engine-xla's kernel tests on this chip instead of a job, the filter as cargo
# takes it (kernels_attn, or one test's name); every test needs the chip, so they run one at a time, and the run
# log carries their output
if [ -n "${KERNELS_TEST:-}" ]; then
  cd "$PIE_ROOT"
  set +e
  cargo test --release -p engine-xla --test engine_xla -- $KERNELS_TEST --test-threads 1 2>&1 | tail -n 400
  rc=${PIPESTATUS[0]}
  set -e
  echo "cargo test -p engine-xla --test engine_xla -- $KERNELS_TEST: exit $rc"
  exit "$rc"
fi

cd "$here"
for p in "${pids[@]}"; do
  engine=${p%%:*}
  wait "${p#*:}" && echo "$engine (TPU build) installed" || echo "$engine (TPU build) install failed (the node retries it):"
  tail -n 20 "$HOME/$engine-tpu-install.log" || true
done
# a slice with more than one chip on the host (v4-8, v5p-8, TPU7x 2x2x1: 4 each): every engine sees chip 0
# only, so pie, vLLM (tp1) and SGLang-JAX (whose default mesh must equal the device count) all run on one chip
chips=$(ls -d /dev/accel* 2>/dev/null | wc -l || true)
[ "$chips" -gt 0 ] || chips=$(ls /dev/vfio 2>/dev/null | grep -cv '^vfio$' || true)
if [ "${chips:-0}" -gt 1 ] && [ -z "${TPU_ALL_CHIPS:-}" ] && [ -z "${PARITY_VLLM_TP:-}" ]; then  # tpu.all_chips: a tp>1 platform uses them all
  echo "$chips TPU chips on this host: the engines see chip 0 only"
  export TPU_VISIBLE_CHIPS=0 TPU_CHIPS_PER_PROCESS_BOUNDS=1,1,1 TPU_PROCESS_BOUNDS=1,1,1
fi
if [ -n "${PARITY_ARTIFACTS:-}" ]; then
  .venv/bin/pie-evals-node build --pie-commit "$commit" --features xla --pie-root "$PIE_ROOT"
  PIE_PY=$(.venv/bin/python -c "from pie_evals.node.build import bench_python; print(bench_python())" | tail -n 1)
  export PIE_PY
  rc=0
  # PARITY_LANES (a slice with that many chips): the models split round-robin over lanes, each lane its own chip,
  # running its models one at a time; 1 (the default): every model on chip 0, one after another
  lanes=${PARITY_LANES:-1}
  [ "$lanes" -le "${chips:-1}" ] || lanes=${chips:-1}
  models=()
  for a in $(echo "$PARITY_ARTIFACTS" | tr ',' ' '); do [ "$a" = kernels ] || models+=("$a"); done
  lane() {
    local i=$1 a k lrc=0
    if [ "$lanes" -gt 1 ]; then
      export TPU_VISIBLE_CHIPS=$i TPU_VISIBLE_DEVICES=$i TPU_CHIPS_PER_PROCESS_BOUNDS=1,1,1 TPU_PROCESS_BOUNDS=1,1,1
      export TPU_MESH_CONTROLLER_ADDRESS=localhost:$((8476 + i)) TPU_MESH_CONTROLLER_PORT=$((8476 + i))
    fi
    for ((k = i; k < ${#models[@]}; k += lanes)); do
      a=${models[$k]}
      # a model's cap (PARITY_MODEL_MINUTES, 60 by default): a hung serve or compile costs one model, not the run
      timeout -k 60 "$(( ${PARITY_MODEL_MINUTES:-60} * 60 ))" .venv/bin/pie-evals-node parity --artifact "$a" --platform "$PARITY_PLATFORM" --pie-root "$PIE_ROOT" \
        --store out/parity/store --tag "$PARITY_TAG" --tag-kind manual --out "out/parity/lane$i" \
        ${PARITY_ACCURACY:+--accuracy "$PARITY_ACCURACY" --n "${PARITY_N:-100}"} || { lrc=$?; echo "parity $a: exit $lrc"; }
      # the servers run in sessions of their own: a capped model's leave the chip held (this lane's only)
      for p in $(pgrep -f 'vllm.entrypoints|parity_pie_serve|target/release/pie' || true); do
        [ "$lanes" -gt 1 ] && ! tr '\0' '\n' < "/proc/$p/environ" 2>/dev/null | grep -qx "TPU_VISIBLE_CHIPS=$i" && continue
        kill -9 "$p" 2>/dev/null || true
      done
      mv "out/parity/lane$i/failed.json" "out/parity/failed-$a.json" || true
      # its checkpoint and import dropped after it: the VM's disk holds a few models', not all
      hub=$(.venv/bin/python -c "import sys; from pie_evals.plan.matrix import Matrix; print(Matrix.load('matrix').artifacts[sys.argv[1]].base_model.replace('/', '--'))" "$a" 2>/dev/null || true)
      if [ "$lanes" -gt 1 ] && [ -n "$hub" ]; then
        rm -rf "$HOME/.cache/huggingface/hub/models--$hub" "$HOME"/.cache/pie-evals/artifacts/"$a"-*
      else
        rm -rf "$HOME"/.cache/huggingface/hub/models--* "$HOME"/.cache/pie-evals/artifacts
      fi
    done
    return $lrc
  }
  pids=()
  for ((i = 0; i < lanes; i++)); do
    # lanes after the first start a little later: their downloads and imports do not all land at once
    ( sleep $((i * 30)); lane "$i" ) > >(sed -u "s/^/[lane $i] /") 2>&1 &
    pids+=($!)
  done
  for p in "${pids[@]}"; do wait "$p" || rc=$?; done
  if [[ ",$PARITY_ARTIFACTS," == *,kernels,* ]]; then  # pie's kernel tests (engine-xla's KERR lines) as one row
    .venv/bin/pie-evals-node kernels --platform "$PARITY_PLATFORM" --pie-root "$PIE_ROOT" --store out/parity/store \
      --tag "$PARITY_TAG" --tag-kind manual --out out/parity/kernels || rc=$?
  fi
  exit $rc
fi
# a shard's watchdog kills its own process group, and an engine server it started in a session of its own
# (engines/lifeline.py) can outlive it holding the chip: every engine of the next shard then fails to open it
# ("open(/dev/vfio/0): 16: Device or resource busy", tpu.yml 42511693568). Before each shard, whatever still holds
# the TPU's device files is stopped (TERM, then KILL) and the chip is free when the shard starts.
free_tpu() {
  local devs pids i
  devs=$(ls /dev/vfio/[0-9]* /dev/accel* 2>/dev/null || true)
  [ -n "$devs" ] || return 0
  for i in $(seq 1 24); do
    # shellcheck disable=SC2086
    pids=$( { sudo lsof -t $devs 2>/dev/null || true; sudo fuser $devs 2>/dev/null || true; } | tr -s ' \t' '\n' | grep -E '^[0-9]+$' | sort -u || true)
    [ -z "$pids" ] && return 0
    echo "the TPU is still held by $(echo $pids): stopping it"
    # shellcheck disable=SC2086
    if [ "$i" -le 3 ]; then sudo kill -TERM $pids 2>/dev/null || true; else sudo kill -KILL $pids 2>/dev/null || true; fi
    sleep 5
  done
  echo "the TPU is still held after 2 minutes"
}
rc=0
for job in "${jobs[@]}"; do
  free_tpu
  .venv/bin/pie-evals-node run --job "$job" --pie-root "$PIE_ROOT" --out "out/$(basename "$job" .json)" --download || rc=$?
done
exit $rc
