#!/usr/bin/env bash
# llama.cpp for the browser: the library at a pinned release, built by emscripten with its WebGPU backend
# (ggml-webgpu over emdawnwebgpu, JSPI for the backend's waits), linked with lw.cpp into lw.mjs + lw.wasm.
#   build.sh <out-dir> <llama.cpp tag, e.g. b11312>
# Caches: $LW_CACHE (default ~/.cache/pie-evals/llamacpp-webgpu) holds emsdk, the Dawn package and the checkout.
set -euo pipefail
out=$(realpath -m "$1")
tag=$2
here=$(cd "$(dirname "$0")" && pwd)
cache=${LW_CACHE:-$HOME/.cache/pie-evals/llamacpp-webgpu}
EMSDK_VERSION=${EMSDK_VERSION:-latest}  # what llama.cpp's own wasm CI builds with
mkdir -p "$cache" "$out"
cd "$cache"
if [ ! -d emsdk ]; then git clone -q https://github.com/emscripten-core/emsdk.git; fi
(cd emsdk && ./emsdk install "$EMSDK_VERSION" >/dev/null && ./emsdk activate "$EMSDK_VERSION" >/dev/null)
# shellcheck disable=SC1091
source emsdk/emsdk_env.sh >/dev/null 2>&1
if [ ! -d "llama.cpp-$tag" ]; then
  git clone -q --depth 1 --branch "$tag" https://github.com/ggml-org/llama.cpp.git "llama.cpp-$tag"
fi
src="$cache/llama.cpp-$tag"
# the Dawn package llama.cpp's own wasm CI builds with at this tag
dawn=$(sed -n 's/^ *DAWN_TAG="\(.*\)"/\1/p' "$src/.github/workflows/build-wasm.yml" | head -1)
if [ ! -d "emdawn-$dawn" ]; then
  curl -fsSL -o emdawn.zip "https://github.com/google/dawn/releases/download/${dawn}/emdawnwebgpu_pkg-${dawn}.zip"
  mkdir -p "emdawn-$dawn" && (cd "emdawn-$dawn" && unzip -q ../emdawn.zip) && rm emdawn.zip
fi
pkg="$cache/emdawn-$dawn/emdawnwebgpu_pkg"
bld="$cache/build-$tag"
emcmake cmake -S "$src" -B "$bld" -G Ninja -DCMAKE_BUILD_TYPE=Release \
  -DGGML_WEBGPU=ON -DGGML_WEBGPU_JSPI=ON -DGGML_OPENMP=OFF -DLLAMA_OPENSSL=OFF -DLLAMA_CURL=OFF \
  -DLLAMA_WASM_MEM64=ON -DLLAMA_BUILD_TESTS=OFF -DLLAMA_BUILD_EXAMPLES=OFF -DLLAMA_BUILD_TOOLS=OFF -DLLAMA_BUILD_SERVER=OFF \
  -DLLAMA_BUILD_HTML=OFF -DBUILD_SHARED_LIBS=OFF -DEMDAWNWEBGPU_DIR="$pkg" >/dev/null
cmake --build "$bld" --target llama -j "$(nproc)"
libs=$(find "$bld" -name '*.a' | sort)
# 64-bit memory (llama.cpp's own wasm default): a GGUF past 4 GiB has offsets a 32-bit size_t cannot hold
em++ -O3 -std=c++17 -sMEMORY64=1 -fwasm-exceptions -I"$src/include" -I"$src/ggml/include" "$here/lw.cpp" $libs \
  --use-port="$pkg/emdawnwebgpu.port.py" -sJSPI -fwasm-exceptions \
  -sJSPI_EXPORTS=lw_load,lw_step -sEXPORTED_FUNCTIONS=_lw_load,_lw_submit,_lw_step,_lw_active,_lw_n_slots,_malloc,_free \
  -sEXPORTED_RUNTIME_METHODS=FS,WORKERFS,ccall,cwrap,HEAP32,HEAPU8,stringToUTF8,lengthBytesUTF8 \
  -lworkerfs.js -sFORCE_FILESYSTEM -sALLOW_MEMORY_GROWTH -sMEMORY64=1 -sMAXIMUM_MEMORY=16GB -sINITIAL_MEMORY=256MB -sSTACK_SIZE=8MB \
  -sMODULARIZE -sEXPORT_ES6 -sEXPORT_NAME=createLw -sENVIRONMENT=worker \
  -o "$out/lw.mjs"
echo "$tag emcc-$(emcc -dumpversion) dawn-$dawn" > "$out/VERSION"
ls -la "$out"
