#!/usr/bin/env bash
# Builds and pushes the five pie-bench images (linux/amd64), tagged latest and the repo's short commit.
#   docker/build.sh                       all five
#   docker/build.sh runpod-cuda gcloud-tpu   some
# REGISTRY (default pieproject) is the Docker Hub namespace; `docker login` first. ROCm images also get
# an :mi35x tag built on the MI350/MI355X base (their :latest is MI300X/MI325X).
set -euo pipefail
cd "$(dirname "$0")/.."
registry=${REGISTRY:-pieproject}
sha=$(git rev-parse --short HEAD)
names=("$@")
[ ${#names[@]} -gt 0 ] || names=(runpod-cuda runpod-rocm digitalocean-cuda digitalocean-rocm gcloud-tpu)

build() {  # image, dockerfile, target, tag suffix, extra args
  local image=$registry/benchmark-$1 file=docker/$2.Dockerfile target=$3 suffix=$4
  shift 4
  docker buildx build --platform linux/amd64 -f "$file" ${target:+--target "$target"} "$@" \
    -t "$image:${suffix:-latest}" -t "$image:$sha${suffix:+-$suffix}" --push .
}

for n in "${names[@]}"; do
  case "$n" in
    runpod-cuda|digitalocean-cuda) build "$n" cuda "${n%-cuda}" "" ;;
    runpod-rocm|digitalocean-rocm)
      build "$n" rocm "${n%-rocm}" "" --build-arg GFX=mi30x --build-arg LLAMA_GPU_TARGETS=gfx942
      build "$n" rocm "${n%-rocm}" mi35x --build-arg GFX=mi35x --build-arg LLAMA_GPU_TARGETS=gfx950 ;;
    gcloud-tpu) build "$n" tpu "" "" ;;
    *) echo "unknown image $n"; exit 2 ;;
  esac
done
