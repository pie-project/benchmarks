# pie-bench on DigitalOcean NVIDIA GPUs: CUDA 13.0 (pie's CUDA line; the host driver must be 580+), nvcc and cuBLAS
# headers for the engines that JIT kernels, Open MPI for TensorRT-LLM, llama.cpp's CUDA build at its pin.
# vLLM, SGLang and TensorRT-LLM install at their pins on the first run, into the data folder.
# One-shot: docker run --gpus all ... <pie-bench args>.
FROM nvidia/cuda:13.0.0-devel-ubuntu24.04
ARG RUST_STABLE=1.98.1
ARG RUST_NIGHTLY=nightly-2026-10-18
ENV DEBIAN_FRONTEND=noninteractive \
    RUSTUP_HOME=/usr/local/rustup \
    CARGO_HOME=/usr/local/cargo \
    UV_PYTHON_INSTALL_DIR=/opt/uv-python \
    PIE_BENCH_PROVIDER=digitalocean \
    PATH=/usr/local/cargo/bin:$PATH
COPY docker/install.sh docker/entrypoint.sh /usr/local/bin/
COPY src/pie_bench/matrix/engines.yaml /tmp/engines.yaml
RUN bash /usr/local/bin/install.sh tools cuda 
COPY pyproject.toml PYPI.md /src/
COPY src /src/src
RUN bash /usr/local/bin/install.sh bench
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
