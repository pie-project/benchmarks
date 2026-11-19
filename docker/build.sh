#!/usr/bin/env bash
# Builds and pushes the five pie-bench images (linux/amd64), tagged latest and the repo's short commit.
#   docker/build.sh                          all five
#   docker/build.sh runpod-cuda gcloud-tpu   some
# REGISTRY (default pieproject) is the Docker Hub namespace; `docker login` first. The ROCm images also
# get an :mi35x tag built on the MI350/MI355X base (their :latest is MI300X/MI325X).
set -euo pipefail
cd "$(dirname "$0")/.."
registry=${REGISTRY:-pieproject}
sha=$(git rev-parse --short HEAD)
names=("$@")
[ ${#names[@]} -gt 0 ] || names=(runpod-cuda runpod-rocm digitalocean-cuda digitalocean-rocm gcloud-tpu)

build() {  # name, tag suffix, extra docker args
  local image=$registry/benchmark-$1 suffix=$2
  shift 2
  docker buildx build --platform linux/amd64 -f "docker/benchmark-${image##*/benchmark-}.Dockerfile" "$@" \
    -t "$image:${suffix:-latest}" -t "$image:$sha${suffix:+-$suffix}" --push .
}

for n in "${names[@]}"; do
  [ -f "docker/benchmark-$n.Dockerfile" ] || { echo "unknown image $n"; exit 2; }
  build "$n" ""
  case "$n" in *-rocm) build "$n" mi35x --build-arg GFX=mi35x ;; esac
done
