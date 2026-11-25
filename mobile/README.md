# mobile

The phone benchmark app. It runs the phone workloads on the phone and shares the results as `records.jsonl`; `pie-bench import-phone` turns that file into a pie-bench submission. They show on the site's Mobile page next to the Mac rows.

- **Workloads:** `raw-512-256` (Raw), `c4` (Batching) and `pf4-512` (Batched Prefill).
- **Same prompts as the Macs:** `shared/workloads.json` is made by `shared/generate_workloads.py` from the harness's own seeded prompt code. It holds each model's chat template and the prompt token counts, so a phone engine can check it read the same prompt. To regenerate it, run `python mobile/shared/generate_workloads.py` from the repository root with `pie-bench` and `transformers` installed.
- **Method:** load the model once, then a warmup and 3 rounds. The server computes decode tok/s, prefill tok/s and TTFT from the raw per-request timings with the harness's own code, and keeps the median round.

## Engines and weights

| Engine | Android | iPhone | Weights |
|---|---|---|---|
| llama.cpp b11312 | CPU (Vulkan optional) | Metal | GGUF Q4_K_M, the Mac rows' files |
| LiteRT-LM 0.19.1 (MediaPipe's successor) | GPU, or CPU | GPU | `.litertlm`: Gemma 4 mixed 2/4/8-bit QAT, Qwen3.5-4B mixed int4, Qwen3.5-0.8B int8 |
| MLC LLM (44fd06d) | OpenCL | Metal | q4f16_1 (Qwen3.5-0.8B: q4f32_1). Only qwen3.5-0.8b, qwen3.5-4b and gemma-4-e2b |
| MLX Swift 3.32.3 | - | Metal | MLX 4-bit g64, the Mac mlx-lm rows' weights |
| Pie (fdc91d79 on iPhone, a6547509 on Android) | Vulkan, in-process | Metal, in-process | `.metal.zt` / `.vulkan.zt` made with `pie model import <repo> --deployment <sku>`, then copied to the phone |

- **Models:** qwen3.5-0.8b, qwen3.5-4b, gemma-4-e2b, gemma-4-e4b, gemma-4-12b. Use gemma-4-12b only on 12-16 GB phones.
- **Downloads:** the app downloads weights from Hugging Face. Pie artifacts come from `antonmeln/pie-bench-phone` (`metal/<pie commit>/<artifact>.metal.zt`, made with `pie model import` at the app's pie commit); the iPhone build also ships `qwen3.5-0.8b-mlx4.metal.zt` inside the app, and the import button next to each model takes your own.

## Install

- **Android:** download `pie-phone-bench-0.1.0-debug.apk` from the GitHub release `mobile-v0.1.0` and open it on the phone (allow "install unknown apps"). Or run `adb install -r pie-phone-bench-0.1.0-debug.apk`.
  - To build it yourself: `cd android && ./gradlew assembleDebug`, which needs JDK 17 and the Android SDK with NDK 28.
  - Pie and MLC need their libraries in `android/app/libs/` (not committed). Without them the APK builds, and those engines report "not built".
- **iPhone:**
  1. Run `xcodegen generate` in `ios/` (`brew install xcodegen`), which writes `ios/PieBench.xcodeproj` from `ios/project.yml`, then open it.
  2. Under Signing & Capabilities, pick your Team.
  3. Plug in the iPhone and press Run.
  4. Turn on Developer Mode on the phone, and trust the developer under Settings › General › VPN & Device Management.
  - A free team may refuse the increased-memory-limit entitlement; remove it if so.
  - To build with MLC and Pie too: `ios/scripts/generate-all.sh <pie checkout>`. MLX Swift is built in only with `MLX_ENABLED=YES`.
- **iPhone, TestFlight** (app `org.pie-project.pie-bench`, team 9B2K6Z98F9):
  1. In the pie checkout at fdc91d79, `git apply ios/scripts/pie-fdc91d79-ios.patch` (model paths passed unescaped; the recurrent-state buffer reserved at the page-rounded size its commits ask for, or Qwen3.5-4B starves on a phone's memory), then `PIE_APPLE_SLICES="aarch64-apple-ios aarch64-apple-darwin" ios/scripts/build-pie.sh <pie checkout>` (the slices need pie's `build-xcframework.sh` to read `PIE_APPLE_SLICES`; without it all three are built).
  2. `pie model import mlx-community/Qwen3.5-0.8B-4bit --deployment qwen35-d0.8b-u4g64-kv-bf16 --out ios/Vendor/pie/models/qwen3.5-0.8b-mlx4.metal.zt`, then rerun step 1's `xcodegen` so the app bundles it.
  3. Raise `CURRENT_PROJECT_VERSION` in `ios/project.yml` for every upload.
  4. `xcodebuild archive -project ios/PieBench.xcodeproj -scheme PieBench -destination generic/platform=iOS -archivePath build/PieBench.xcarchive -allowProvisioningUpdates`
  5. `xcodebuild -exportArchive -archivePath build/PieBench.xcarchive -exportOptionsPlist ios/ExportOptions.plist -exportPath build/export -allowProvisioningUpdates` uploads it to TestFlight.

## Build notes

### Android

- **llama.cpp source:** set `llama.cpp.dir` in `android/local.properties` to a local checkout of tag b11312. Without it, CMake downloads the tag.
- **llama.cpp GPU backend:** `./gradlew assembleDebug -PllamaGpu=vulkan|opencl|none` adds that backend next to the CPU one. The default is `vulkan` when `vulkan.headers.dir` is set in `local.properties`, else `none`. The NDK has `vulkan_core.h` and `libvulkan` but no `vulkan.hpp`, so Vulkan also needs Khronos Vulkan-Headers (`vulkan.headers.dir`) and SPIRV-Headers (`spirv.headers.cmake.dir`).
- **CPU variants:** every arm64 CPU variant (dotprod, fp16, i8mm, sve2, sme) is built as a loadable ggml backend, as in llama.cpp's own Android example, and the best one is picked at run time. ggml loads them with `dlopen`, so the APK keeps legacy native library packaging.
- **Optional engines:** pie builds in when `app/libs/pie/` holds its AAR or jar. MLC builds in when `app/libs/mlc/mlc4j/output/` holds `tvm4j_core.jar` and `arm64-v8a/libtvm4j_runtime_packed.so` (TVM, MLC and the compiled model libraries). `src/mlc/java` carries mlc4j's `JSONFFIEngine`.
- **Models by hand:** models live in `<app files>/models/<artifact id>/` next to a `meta.json` (`repo`, `file`, `revision`, `bytes`). To copy one in, `adb push` it to `/data/local/tmp`, then `adb shell run-as org.pieevals.phonebench cp /data/local/tmp/<file> files/models/<artifact id>/`.
- **Scripted runs (debug builds):** `adb shell am start -n org.pieevals.phonebench/.MainActivity --es engines llamacpp --es models qwen3.5-0.8b-llamacpp --es workloads raw-512-256 --es tag test-phone-e2e`. `models` takes site model ids or artifact ids, comma separated. The other extras are `litert_backend` and `llama_backend` (`cpu` or `gpu`), `threads` and `download`.

### iPhone

- **Simulator:** the b11312 release XCFramework has no simulator slice. `ios/scripts/build-llama-sim.sh [workdir]` builds one from source into `Packages/LlamaCpp/local/llama.xcframework`; then build with `LLAMA_XCFRAMEWORK=local/llama.xcframework`.
- **Pie:** `ios/scripts/build-pie.sh <pie checkout>` builds `PieServerCore.xcframework`, the bench inferlet (`examples/text-completion-bench`, `wasm32-wasip3`) and a project with the Pie package. It needs Rust and XcodeGen. Plain `xcodegen generate` drops pie again.
- **MLC:** `ios/scripts/vendor-mlc.sh <mlc-llm checkout> <dist dir>` copies a built MLC runtime into `Vendor/mlc`; then `MLC_ENABLED=YES xcodegen generate`. MLC is linked for devices only, so a simulator build reports MLC as unsupported. The dist was made on 2026-11-05 (Xcode 27.2) from mlc-llm 44fd06d0 with its TVM built from source (LLVM 20 static, Metal on; the nightly wheels lack Gemma 4 and crash on `compile --device iphone`) and patched with `ios/scripts/mlc-tvm-ios.patch`, without which every system-lib compile fails in `compact_kv_copy`. After `rustup target add aarch64-apple-ios`, run `python -m mlc_llm package --package-config mlc-package-config.json --mlc-llm-source-dir <mlc-llm> --output dist` with device `iphone`, the models Qwen3.5-0.8B-q4f32_1, Qwen3.5-4B-q4f16_1 and gemma-4-E2B-it-q4f16_1, `context_window_size` 4096, `prefill_chunk_size` 512 and `bundle_weight` false.
- **Everything built:** `ios/scripts/generate-all.sh [pie checkout]` adds MLC when `Vendor/mlc` exists and pie when `Vendor/pie` exists.
- **Bundled pie models:** `<artifact>.metal.zt` files in `ios/Vendor/pie/models` ship inside the app, so the phone needs no import.
- **Unattended runs:** launch with `PIEBENCH_AUTORUN=1`, `PIEBENCH_MODELS=<engine>/<artifact>,...`, `PIEBENCH_WORKLOADS=<id>,...`, `PIEBENCH_TAG=<tag>` and `PIEBENCH_EXIT=1`. `xcrun simctl launch` passes them as `SIMCTL_CHILD_*`, and the same keys work as `-PIEBENCH_X value` launch arguments. `PIEBENCH_LLAMA_CPU=1` runs llama.cpp on the CPU where the simulator's Metal falls short.

## Sending results

1. In the app, tap **Share records.jsonl** and AirDrop it to the Mac (or save it to Files).
2. `pie-bench import-phone records.jsonl --tag <release tag> --dry-run` checks the rows and prints them.
3. `pie-bench import-phone records.jsonl --tag <release tag>` writes one submission per phone run into `~/.pie-bench/phone/<run id>/`.
4. `pie-bench upload ~/.pie-bench/phone/<run id>` sends it to the API.

- **Which release the rows join:** the `--tag` given at import, e.g. the site's current `main-<commit>` tag. A `test-*` tag is never shown on the site.
- **Simulator rows** are taken only under a `test-*` tag.
- **Unknown phones:** a phone not in `src/pie_bench/matrix/phones.yaml` is stored as `android-<model>` or `ios-<model>`.
