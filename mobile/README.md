# mobile

The phone benchmark app. It runs the phone workloads on the phone and shares the results as `records.jsonl`; `pie-bench import-phone` turns that file into a pie-bench submission. They show on the site's Mobile page next to the Mac rows.

- **Workloads:** `raw-512-256` (Raw), `c4` (Batching) and `pf4-512` (Batched Prefill).
- **Same prompts as the Macs:** `shared/workloads.json` is made by `tools/gen_workloads.py` from the harness's own seeded prompt code. It holds each model's chat template and the prompt token counts.
- **Method:** load the model once, then a warmup and 3 rounds. The server computes decode tok/s, prefill tok/s and TTFT from the raw per-request timings with the harness's own code, and keeps the median round.

## Engines and weights

| Engine | Android | iPhone | Weights |
|---|---|---|---|
| llama.cpp b11312 | CPU (Vulkan optional) | Metal | GGUF Q4_K_M, the Mac rows' files |
| LiteRT-LM 0.19.1 (MediaPipe's successor) | GPU, or CPU | - | `.litertlm`: Gemma 4 mixed 2/4/8-bit QAT, Qwen3.5-4B mixed int4, Qwen3.5-0.8B int8 |
| MLC LLM (44fd06d) | OpenCL | Metal | q4f16_1 (Qwen3.5-0.8B: q4f32_1). Only qwen3.5-0.8b, qwen3.5-4b and gemma-4-e2b |
| MLX Swift 3.32.3 | - | Metal | MLX 4-bit g64, the Mac mlx-lm rows' weights |
| Pie (fdc91d79 on iPhone, a6547509 on Android) | Vulkan, in-process | Metal, in-process | `.metal.zt` / `.vulkan.zt` made with `pie model import <repo> --deployment <sku>`, then copied to the phone |

- **Models:** qwen3.5-0.8b, qwen3.5-4b, gemma-4-e2b, gemma-4-e4b, gemma-4-12b. Use gemma-4-12b only on 12-16 GB phones.
- **Downloads:** the app downloads weights from Hugging Face. Pie artifacts come from `antonmeln/pie-bench-phone` (`metal/<pie commit>/<artifact>.metal.zt`, made with `pie model import` at the app's pie commit); the iPhone build also ships `qwen3.5-0.8b-mlx4.metal.zt` inside the app, and the import button next to each model takes your own.

## Install

- **Android:** download `app-debug.apk` from the GitHub release `mobile-v0.1.0` and open it on the phone (allow "install unknown apps"). Or run `adb install -r app-debug.apk`.
  - To build it yourself: `cd android && ./gradlew assembleDebug`, which needs JDK 17 and the Android SDK with NDK 28.
  - Pie and MLC need their libraries in `android/app/libs/` (not committed). Without them the APK builds, and those engines report "not built".
- **iPhone:**
  1. Open `ios/PieBench.xcodeproj`.
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

## Sending results

1. In the app, tap **Share records.jsonl** and AirDrop it to the Mac (or save it to Files).
2. `pie-bench import-phone records.jsonl --tag <release tag> --dry-run` checks the rows and prints them.
3. `pie-bench import-phone records.jsonl --tag <release tag>` writes one submission per phone run into `~/.pie-bench/phone/<run id>/`.
4. `pie-bench upload ~/.pie-bench/phone/<run id>` sends it to the API.

- **Which release the rows join:** the `--tag` given at import, e.g. the site's current `main-<commit>` tag. A `test-*` tag is never shown on the site.
- **Simulator and Mac test rows** are taken only under a `test-*` tag.
- **Unknown phones:** a phone not in `src/pie_bench/matrix/phones.yaml` is stored as `android-<model>` or `ios-<model>`.
