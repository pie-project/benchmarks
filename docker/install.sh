#!/usr/bin/env bash
# Image build steps shared by every Dockerfile here.
#   install.sh tools <cuda|rocm|tpu>   apt packages, uv, Python 3.12, Rust at pie's pins, llama.cpp at its pin
#   install.sh bench                   pie-bench from /src into /opt/pie-bench, on PATH as `pie-bench`
set -euo pipefail
step=$1
backend=${2:-}

if [ "$step" = tools ]; then
  apt-get update
  apt-get install -y --no-install-recommends --allow-change-held-packages \
    ca-certificates curl git jq unzip xz-utils patch procps build-essential cmake ninja-build pkg-config \
    libssl-dev python3 python3-dev python3-venv
  if [ "$backend" = cuda ]; then
    apt-get install -y --no-install-recommends --allow-change-held-packages libnccl2 libopenmpi-dev openmpi-bin
  fi
  apt-get clean && rm -rf /var/lib/apt/lists/*

  curl -LsSf https://astral.sh/uv/install.sh | env UV_INSTALL_DIR=/usr/local/bin sh
  uv python install 3.12

  curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --profile minimal --default-toolchain "$RUST_STABLE" --no-modify-path
  rustup toolchain install "$RUST_NIGHTLY" --profile minimal --target wasm32-wasip3
  chmod -R a+rwX "$RUSTUP_HOME" "$CARGO_HOME"

  if [ "$backend" = cuda ] || [ "$backend" = rocm ]; then
    pin=$(awk '/- id: llamacpp$/{f=1} f&&/pin:/{gsub(/[" ]|pin:/,""); print; exit}' /tmp/engines.yaml)
    git clone --quiet --depth 1 --branch "$pin" https://github.com/ggml-org/llama.cpp /tmp/llama.cpp
    cd /tmp/llama.cpp
    flags=(-G Ninja -DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED_LIBS=OFF -DGGML_NATIVE=OFF -DLLAMA_CURL=OFF -DLLAMA_BUILD_TESTS=OFF)
    if [ "$backend" = cuda ]; then
      cmake -S . -B build "${flags[@]}" -DGGML_CUDA=ON -DCMAKE_CUDA_ARCHITECTURES="$LLAMA_CUDA_ARCHS"
    else
      hip="${ROCM_PATH:-/opt/rocm}/bin/hipconfig"; HIPCXX="$($hip -l)/clang" HIP_PATH="$($hip -R)" \
        cmake -S . -B build "${flags[@]}" -DGGML_HIP=ON -DGPU_TARGETS="$LLAMA_GPU_TARGETS"
    fi
    cmake --build build --target llama-server
    install -m 755 build/bin/llama-server /usr/local/bin/llama-server
    cd / && rm -rf /tmp/llama.cpp
  fi
  rm -f /tmp/engines.yaml
fi

if [ "$step" = bench ]; then
  uv venv --quiet --python 3.12 /opt/pie-bench
  uv pip install --quiet --python /opt/pie-bench/bin/python /src
  ln -sf /opt/pie-bench/bin/pie-bench /usr/local/bin/pie-bench
  rm -rf /src /root/.cache/uv
  pie-bench --version
fi
