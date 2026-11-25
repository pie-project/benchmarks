#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
registry=${REGISTRY:-pieproject}
sha=$(git rev-parse --short HEAD)
names=("$@")
[ ${#names[@]} -gt 0 ] || names=(runpod-cuda runpod-rocm digitalocean-cuda digitalocean-rocm gcloud-tpu)

build() {
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
