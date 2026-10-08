#!/usr/bin/env bash
# On a fresh Cloud TPU VM (runtime v2-alpha-tpuv6e): install the toolchains, check out pie at a
# commit, and run one pie-evals job on the XLA engine. Started by .github/workflows/tpu.yml from
# the unpacked pie-evals tree; the node builds pie with --features xla, imports the model as a
# .xla.zt and writes out/<job_id>/records.jsonl.
#
#   bash infra/tpu/run-on-vm.sh <pie_commit> jobs/<job_id>.json
set -euo pipefail
commit=$1
job=$2
job_id=$(basename "$job" .json)
here=$(pwd)

sudo apt-get update -q
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -q --no-install-recommends \
  build-essential cmake ninja-build pkg-config libssl-dev git curl ca-certificates python3-yaml
command -v rustup >/dev/null || curl -sSf https://sh.rustup.rs | sh -s -- -y --profile minimal --default-toolchain none
command -v uv >/dev/null || curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.cargo/bin:$HOME/.local/bin:$PATH"

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
uv venv -q --python 3.12 .venv
uv pip install -q --python .venv/bin/python -e .
.venv/bin/pie-evals-node run --job "$job" --pie-root "$PIE_ROOT" --out "out/$job_id" --download
