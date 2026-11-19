# pie-bench on AMD Instinct GPUs. The base is AMD's SGLang image at the engines.yaml pin, the one the
# harness takes SGLang from on ROCm (it carries ROCm and SGLang in /opt/venv); GFX picks mi30x
# (MI300X, MI325X) or mi35x (MI350, MI355X). llama.cpp is built with HIP; vLLM installs on the first run.
# Targets: runpod (sshd, keeps the pod up), digitalocean (one-shot `docker run`).
ARG SGLANG=0.5.22
ARG GFX=mi30x
FROM lmsysorg/sglang:v${SGLANG}-rocm10-${GFX} AS base
ARG RUST_STABLE=1.98.1
ARG RUST_NIGHTLY=nightly-2026-10-18
ARG LLAMA_GPU_TARGETS="gfx942;gfx950"
ENV DEBIAN_FRONTEND=noninteractive \
    RUSTUP_HOME=/usr/local/rustup \
    CARGO_HOME=/usr/local/cargo \
    UV_PYTHON_INSTALL_DIR=/opt/uv-python \
    PATH=/usr/local/cargo/bin:$PATH
COPY docker/install.sh docker/entrypoint.sh /usr/local/bin/
COPY src/pie_bench/matrix/engines.yaml /tmp/engines.yaml
RUN bash /usr/local/bin/install.sh tools rocm
COPY pyproject.toml PYPI.md /src/
COPY src /src/src
RUN bash /usr/local/bin/install.sh bench
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]

FROM base AS digitalocean
ENV PIE_BENCH_PROVIDER=digitalocean

FROM base AS runpod
RUN apt-get update && apt-get install -y --no-install-recommends openssh-server && rm -rf /var/lib/apt/lists/*
ENV PIE_BENCH_PROVIDER=runpod
WORKDIR /workspace
