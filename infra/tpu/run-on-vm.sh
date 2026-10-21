#!/usr/bin/env bash
# On a fresh Cloud TPU VM (any generation: platforms.yaml tpu:): install the toolchains, check out pie at a
# commit, and run one pie-evals job on the XLA engine. Started by .github/workflows/tpu.yml from
# the unpacked pie-evals tree; the node builds pie with --features xla, imports the model as a
# .xla.zt and writes out/<job_id>/records.jsonl. A job with vLLM or SGLang cells also gets their TPU builds
# (vllm-tpu, sglang-jax at the engines.yaml pins) in their own venvs, installed beside the toolchains.
#
#   bash infra/tpu/run-on-vm.sh <pie_commit> jobs/<job_id>.json
set -euo pipefail
commit=$1
job=$2
job_id=$(basename "$job" .json)
here=$(pwd)

# a data disk (platforms.yaml tpu.data_disk_gb) holds ~/.cache: the checkpoints, their imports, the venvs
root=$(lsblk -no PKNAME "$(findmnt -no SOURCE /)" 2>/dev/null | head -n 1 || true)
data=$(lsblk -dpno NAME,TYPE | awk -v r="/dev/$root" '$2 == "disk" && $1 != r {print $1; exit}' || true)
if [ -n "$data" ] && [ -z "$(lsblk -no MOUNTPOINT "$data" | tr -d '[:space:]')" ] && ! mountpoint -q "$HOME/.cache"; then
  sudo blkid "$data" >/dev/null 2>&1 || sudo mkfs.ext4 -q -F "$data"
  mkdir -p "$HOME/.cache" && sudo mount "$data" "$HOME/.cache" && sudo chown "$(id -u):$(id -g)" "$HOME/.cache"
  df -h "$HOME/.cache"
fi

sudo apt-get -o DPkg::Lock::Timeout=900 update -q  # a fresh VM's unattended-upgrades holds the lock for minutes
sudo DEBIAN_FRONTEND=noninteractive apt-get -o DPkg::Lock::Timeout=900 install -y -q --no-install-recommends \
  build-essential cmake ninja-build pkg-config libssl-dev git curl ca-certificates python3-yaml jq
command -v rustup >/dev/null || curl -sSf https://sh.rustup.rs | sh -s -- -y --profile minimal --default-toolchain none
command -v uv >/dev/null || curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.cargo/bin:$HOME/.local/bin:$PATH"

cd "$here"
uv venv -q --python 3.12 .venv
uv pip install -q --python .venv/bin/python -e .

# the TPU builds of vLLM and SGLang, in the background while the toolchains install: the node then finds
# the venvs ready (baselines.ensure_baseline, the same call it makes itself when a venv is missing)
pids=()
for engine in vllm sglang; do
  pin=$(jq -r ".baseline_versions.$engine // empty" "$job" 2>/dev/null || true)
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
if [ "${chips:-0}" -gt 1 ] && [ -z "${TPU_ALL_CHIPS:-}" ]; then  # tpu.all_chips: a tp>1 platform uses them all
  echo "$chips TPU chips on this host: the engines see chip 0 only"
  export TPU_VISIBLE_CHIPS=0 TPU_CHIPS_PER_PROCESS_BOUNDS=1,1,1 TPU_PROCESS_BOUNDS=1,1,1
fi
.venv/bin/pie-evals-node run --job "$job" --pie-root "$PIE_ROOT" --out "out/$job_id" --download
