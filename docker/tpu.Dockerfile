# pie-bench on a Cloud TPU VM (v4, v5e, v5p, v6e, TPU7x): Ubuntu 22.04 as the VM, libtpu at the version
# pie's XLA engine is generated against (PIE_XLA_PLUGIN), Rust for the --features xla build. vllm-tpu and
# sglang-jax install at their pins on the first run. The machine id comes from the VM's metadata.
FROM ubuntu:22.04
ARG RUST_STABLE=1.98.1
ARG RUST_NIGHTLY=nightly-2026-10-18
ARG LIBTPU=0.0.48
ENV DEBIAN_FRONTEND=noninteractive \
    RUSTUP_HOME=/usr/local/rustup \
    CARGO_HOME=/usr/local/cargo \
    UV_PYTHON_INSTALL_DIR=/opt/uv-python \
    PIE_XLA_PLUGIN=/opt/libtpu/libtpu.so \
    PIE_BENCH_PROVIDER=gcloud \
    PATH=/usr/local/cargo/bin:$PATH
COPY docker/install.sh docker/entrypoint.sh /usr/local/bin/
COPY src/pie_bench/matrix/engines.yaml /tmp/engines.yaml
RUN bash /usr/local/bin/install.sh tools tpu \
    && uv venv --quiet --python 3.12 /opt/libtpu \
    && uv pip install --quiet --python /opt/libtpu/bin/python "libtpu==${LIBTPU}" \
    && ln -s "$(/opt/libtpu/bin/python -c 'import libtpu, os; print(os.path.join(os.path.dirname(libtpu.__file__), "libtpu.so"))')" /opt/libtpu/libtpu.so \
    && test -f /opt/libtpu/libtpu.so
COPY pyproject.toml PYPI.md /src/
COPY src /src/src
RUN bash /usr/local/bin/install.sh bench
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
