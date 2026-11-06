# mobile

The phone benchmark app. It runs the pie-evals phone workloads on the phone and sends the results to the pie-evals database. They show on the site's Mobile page next to the Mac rows.

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
| Pie (a6547509) | Vulkan, in-process | Metal, in-process | `.metal.zt` / `.vulkan.zt` made with `pie model import <repo> --deployment <sku>`, then copied to the phone |

- **Models:** qwen3.5-0.8b, qwen3.5-4b, gemma-4-e2b, gemma-4-e4b, gemma-4-12b. Use gemma-4-12b only on 12-16 GB phones.
- **Downloads:** the app downloads weights from Hugging Face. Pie artifacts are not hosted there.

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
  - TestFlight needs App Store Connect credentials; this project doesn't set it up.
  - To build with MLC and Pie too: `ios/scripts/generate-all.sh <pie checkout>`.

## Sending results

1. **Over the tailnet:** turn on the official Tailscale app on the phone. In the app's Settings, enter the URL `http://100.85.194.44:8787` (the site laptop) and the token, then tap Send.
   - The token is in `~/.config/pie-evals/phone-ingest.token` on that laptop.
   - The ingest (`pie-evals phone-ingest`) listens only on the laptop's Tailscale address and answers only tailnet peers. Nothing is exposed to the internet.
   - It holds rows in `~/.pie-evals/phone-inbox`, and the pages build stores them in the database within about 5 minutes.
   - Start it once with `ingest/install-launchd.sh`.
2. **Without the tailnet:**
   - Tap Share to send `records.jsonl` by AirDrop, Files or email. Then run `pie-evals import-phone records.jsonl` (needs `PIE_EVALS_DB`), or drop the file into `~/.pie-evals/phone-inbox/pending/` on the site laptop.
   - Or tap "Copy for workflow" and run `gh workflow run phone-import.yml -f records="<pasted text>"`.

- **Which release the rows join:** rows join the newest release tag unless a tag is set in Settings.
- **Test tags:** a `test-*` tag is never shown on the site. Remove one with `gh workflow run phone-import.yml -f drop_tag=test-...`.
- **Unknown phones:** a phone not in `../matrix/phones.yaml` is stored as `android-<model>` or `ios-<model>` and still shows on the site.
