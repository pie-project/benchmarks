# pie-bench on NVIDIA GPUs: CUDA 13 (pie's CUDA line, the driver comes from the host and must be 580+),
# nvcc and cuBLAS headers for the engines that JIT kernels, Open MPI for TensorRT-LLM, llama.cpp built
# with CUDA. vLLM, SGLang and TensorRT-LLM install at their pins on the first run, into the data folder.
# Targets: runpod (sshd, keeps the pod up), digitalocean (one-shot `docker run`).
ARG CUDA=13.0.0
FROM nvidia/cuda:${CUDA}-devel-ubuntu24.04 AS base
ARG RUST_STABLE=1.98.1
ARG RUST_NIGHTLY=nightly-2026-10-18
ARG LLAMA_CUDA_ARCHS="75-real;80-real;86-real;89-real;90-real;100-real;103-real;120"
ENV DEBIAN_FRONTEND=noninteractive \
    RUSTUP_HOME=/usr/local/rustup \
    CARGO_HOME=/usr/local/cargo \
    UV_PYTHON_INSTALL_DIR=/opt/uv-python \
    PATH=/usr/local/cargo/bin:$PATH
COPY docker/install.sh docker/entrypoint.sh /usr/local/bin/
COPY src/pie_bench/matrix/engines.yaml /tmp/engines.yaml
RUN bash /usr/local/bin/install.sh tools cuda
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
