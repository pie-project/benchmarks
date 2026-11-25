#!/usr/bin/env bash
set -euo pipefail
step=$1
backend=${2:-}

if [ "$step" = tools ]; then
  apt-get update
  apt-get install -y --no-install-recommends --allow-change-held-packages \
    ca-certificates curl git jq unzip xz-utils patch procps build-essential cmake ninja-build pkg-config \
    libssl-dev libgomp1 libcurl4 python3 python3-dev python3-venv
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
    rel=https://github.com/ggml-org/llama.cpp/releases/download/$pin
    mkdir -p /opt/llama.cpp
    if [ "$backend" = cuda ]; then
      curl -fsSL "$rel/llama-$pin-bin-ubuntu-cuda-13.4-x64.tar.gz" | tar xz --strip-components 1 -C /opt/llama.cpp
      curl -fsSL "$rel/cudart-llama-$pin-bin-ubuntu-cuda-13.4-x64.tar.gz" | tar xz --strip-components 1 -C /opt/llama.cpp
    else
      curl -fsSL "$rel/llama-$pin-bin-ubuntu-rocm-10.0-x64.tar.gz" | tar xz --strip-components 1 -C /opt/llama.cpp
    fi
    ln -sf /opt/llama.cpp/llama-server /usr/local/bin/llama-server
  fi
  if [ "${3:-}" = ssh ]; then
    apt-get update && apt-get install -y --no-install-recommends openssh-server && apt-get clean && rm -rf /var/lib/apt/lists/*
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
