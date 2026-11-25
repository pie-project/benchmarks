# Browser engines

The engines that run in a browser tab on WebGPU, served to the bench client like any OpenAI server:

| Engine | Class | Page |
|---|---|---|
| WebLLM | `WebllmEngine` | `harness/page/engines/webllm.mjs` |
| llama.cpp on WebGPU | `LlamacppWebgpuEngine` | `harness/page/engines/llamacpp.mjs`, `llamacpp-worker.mjs` |
| pie on WebGPU | `PieWebEngine` | `harness/page/engines/pie.mjs` |

`webgpu.py` stages each engine's files (the model, its wasm, its options) in a folder of the pie-bench cache, then
starts `harness/bridge.mjs`: a Node server that serves the page and the staged files, drives headless Chrome through
Playwright, and answers the bench client's requests from the tab.

## Harness

`harness/` is the npm package `pie-bench-browser` (private). On first use `pie-bench` runs `npm install` there and
installs Playwright's Chromium with its system libraries, so a machine needs Node.js and npm. On Linux with an NVIDIA
driver it also checks Vulkan: it installs the loader (`libvulkan1`) when missing and writes the NVIDIA ICD manifest
when the driver's graphics libraries are present but no manifest names them. Without those libraries WebGPU runs on
SwiftShader.

## llama.cpp on WebGPU

`llamacpp_wasm/build.sh <out> <tag>` builds llama.cpp at the recipe's pinned tag for the browser:

- emsdk at `EMSDK_VERSION` (default `latest`, what llama.cpp's own wasm CI builds with);
- Dawn's emdawnwebgpu package at the `DAWN_TAG` of llama.cpp's own `build-wasm.yml`;
- llama.cpp's static libraries with WebGPU and JSPI on, linked with `llama_webgpu.cpp` (the `lw_*` entry points the
  page calls) into `lw.mjs` and `lw.wasm`, 64-bit memory up to 16 GB;
- a `VERSION` file with the tag, the emcc version and the Dawn tag.

Sources and toolchains are cached under `LW_CACHE` (default `~/.cache/pie-bench/llamacpp-webgpu`). The engine's
build folder is named by the tag and a hash of `llama_webgpu.cpp` and `build.sh`, so a change to either rebuilds it.
