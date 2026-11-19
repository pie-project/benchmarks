# pie-bench on RunPod AMD Instinct GPUs. The base is AMD's SGLang image at the engines.yaml pin (ROCm 10,
# SGLang in /opt/venv), which is where the harness takes SGLang from on ROCm; mi30x is MI300X/MI325X, build
# with --build-arg GFX=mi35x for MI350/MI355X. llama.cpp's ROCm build at its pin; vLLM installs on the first run.
# sshd (PUBLIC_KEY); the pod stays up after a run.
ARG GFX=mi30x
FROM lmsysorg/sglang:v0.5.22-rocm10-${GFX}
ARG RUST_STABLE=1.98.1
ARG RUST_NIGHTLY=nightly-2026-10-18
ENV DEBIAN_FRONTEND=noninteractive \
    RUSTUP_HOME=/usr/local/rustup \
    CARGO_HOME=/usr/local/cargo \
    UV_PYTHON_INSTALL_DIR=/opt/uv-python \
    PIE_BENCH_PROVIDER=runpod \
    PATH=/usr/local/cargo/bin:$PATH
COPY docker/install.sh docker/entrypoint.sh /usr/local/bin/
COPY src/pie_bench/matrix/engines.yaml /tmp/engines.yaml
RUN bash /usr/local/bin/install.sh tools rocm ssh
COPY pyproject.toml PYPI.md /src/
COPY src /src/src
RUN bash /usr/local/bin/install.sh bench
WORKDIR /workspace
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
