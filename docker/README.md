# Docker images

`pie-bench` ready to run, one image per place we rent machines:

| Image | Base | Where |
|---|---|---|
| `pieproject/benchmark-runpod-cuda` | CUDA 13.0 devel, Ubuntu 24.04 | RunPod NVIDIA pods |
| `pieproject/benchmark-runpod-rocm` | `lmsysorg/sglang:v0.5.22-rocm10-mi30x` (`:mi35x` for MI350/MI355X) | RunPod AMD pods |
| `pieproject/benchmark-digitalocean-cuda` | CUDA 13.0 devel, Ubuntu 24.04 | DigitalOcean NVIDIA droplets |
| `pieproject/benchmark-digitalocean-rocm` | as RunPod ROCm | AMD Developer Cloud droplets |
| `pieproject/benchmark-gcloud-tpu` | Ubuntu 22.04, libtpu 0.0.48 | Cloud TPU VMs |

Each has uv, Python 3.12, Rust at pie's pins and `pie-bench` from this repo; CUDA and ROCm add llama.cpp at its pin. The engines (pie, vLLM, SGLang, TensorRT-LLM) install on the first run, into the data folder.

The arguments go to `pie-bench`. With no arguments, `PIE_BENCH_ARGS` is used. A `run` gets `-y`, and `PIE_BENCH_MACHINE` becomes `--machine` (needed on AMD, where the CLI cannot detect the machine; TPUs read it from the VM's metadata).

Caches, results and the upload token go to `/workspace` on RunPod and to `/data` if it is mounted elsewhere (`PIE_BENCH_DATA` overrides).

## Run

RunPod: image `pieproject/benchmark-runpod-cuda`, a volume on `/workspace`, CUDA 13 hosts (driver 580+). With no start command the pod stays up for SSH (`PUBLIC_KEY`); with `PIE_BENCH_ARGS="run"` it measures, uploads, then stays up. On AMD add `PIE_BENCH_MACHINE=mi300x-x1`.

DigitalOcean NVIDIA:

```sh
docker run --gpus all --ipc=host -v /mnt/pie-bench:/data pieproject/benchmark-digitalocean-cuda run
```

DigitalOcean AMD:

```sh
docker run --device /dev/kfd --device /dev/dri --group-add video --ipc=host --shm-size 64g \
  -v /mnt/pie-bench:/data -e PIE_BENCH_MACHINE=mi300x-x1 pieproject/benchmark-digitalocean-rocm run
```

Cloud TPU VM:

```sh
sudo docker run --privileged --net=host --ipc=host -v /mnt/pie-bench:/data pieproject/benchmark-gcloud-tpu run
```

## Build

```sh
docker login
docker/build.sh                        # all five, linux/amd64, tagged latest and the commit
docker/build.sh runpod-cuda gcloud-tpu # some
```
