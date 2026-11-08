window.Pie = window.Pie || {};

// Methods: how the theoretical limit is worked out, a chapter per workload, written as a short paper. Each chapter
// gives its numbered formulas with the work each rests on, why they hold, every simplification and which way it moves
// the limit, a check against every measured result, a worked example, and the references. A bar over the page picks the
// chapter with the grid's own workload pop-up, so the grid and the Methods page always show the same workload.
(() => {
  const element = document.getElementById("methods");
  const esc = (text) => Pie.format.escape(text);

  // the works the formulas rest on, checked against arXiv and the DOI registry
  const REFS = {
    roofline: { authors: "S. Williams, A. Waterman, D. Patterson", title: "Roofline: An Insightful Visual Performance Model for Multicore Architectures", venue: "Communications of the ACM 52(4)", year: 2009, url: "https://doi.org/10.1145/1498765.1498785" },
    kaplan: { authors: "J. Kaplan et al.", title: "Scaling Laws for Neural Language Models", venue: "arXiv:2001.08361", year: 2020, url: "https://arxiv.org/abs/2001.08361" },
    shazeer: { authors: "N. Shazeer", title: "Fast Transformer Decoding: One Write-Head is All You Need", venue: "arXiv:1911.02150", year: 2019, url: "https://arxiv.org/abs/1911.02150" },
    pope: { authors: "R. Pope et al.", title: "Efficiently Scaling Transformer Inference", venue: "MLSys 2023, arXiv:2211.05102", year: 2022, url: "https://arxiv.org/abs/2211.05102" },
    yuan: { authors: "Z. Yuan et al.", title: "LLM Inference Unveiled: Survey and Roofline Model Insights", venue: "arXiv:2402.16363", year: 2024, url: "https://arxiv.org/abs/2402.16363" },
    leviathan: { authors: "Y. Leviathan, M. Kalman, Y. Matias", title: "Fast Inference from Transformers via Speculative Decoding", venue: "ICML 2023, arXiv:2211.17192", year: 2022, url: "https://arxiv.org/abs/2211.17192" },
    chen: { authors: "C. Chen et al.", title: "Accelerating Large Language Model Decoding with Speculative Sampling", venue: "arXiv:2302.01318", year: 2023, url: "https://arxiv.org/abs/2302.01318" },
    megatron: { authors: "M. Shoeybi et al.", title: "Megatron-LM: Training Multi-Billion Parameter Language Models Using Model Parallelism", venue: "arXiv:1909.08053", year: 2019, url: "https://arxiv.org/abs/1909.08053" },
    metal: { authors: "Apple", title: "MTLDevice.recommendedMaxWorkingSetSize", venue: "Metal documentation", year: 2016, url: "https://developer.apple.com/documentation/metal/mtldevice/recommendedmaxworkingsetsize" },
    kwon: { authors: "W. Kwon et al.", title: "Efficient Memory Management for Large Language Model Serving with PagedAttention", venue: "SOSP 2023, arXiv:2309.06180", year: 2023, url: "https://arxiv.org/abs/2309.06180" },
  };


  // the worked examples: one machine and one model from the catalog, at the 4-bit weights the runs use
  const EXAMPLE = { hardware: "m5-max-128g", model: "qwen3.5-4b", scheme: "affine_u4_g64" };
  // the Limit page's speculation defaults: 70% accepted, a half-billion-parameter drafter that proposes its whole block
  // in one pass (DFlash), and draft widths up to 16 to pick the best from
  const SPEC = { a: 0.7, drafter: 0.5, widest: 16 };

  const num = (n) => (n >= 100 ? Math.round(n).toLocaleString("en-US") : n >= 10 ? n.toFixed(0) : n.toFixed(1));
  const ms = (s) => `${(s * 1e3).toFixed(s * 1e3 >= 10 ? 0 : 2)} ms`;
  const gb = (n) => `${n.toFixed(2)} GB`;

  // a formula as a paper typesets it: the result's name, the equation in symbols, and the works it rests on
  const eq = (result, math, cites = []) => ({ result, math, cites });

  // each quantity's symbol, as a paper's notation table states them: a letter, italic, with an upright subscript; the
  // symbol names its quantity on hover
  const SYM = {
    "Memory time": ["T", "mem"], "Math time": ["T", "math"], "Interconnect time": ["T", "link"],
    "Weights read": ["W"], "Weights touched": ["W"], "Cache read": ["C"], "Caches read": ["C"], "Prompt cache": ["C"], "Prompt caches": ["C"],
    "Memory bandwidth": ["B", "mem"], "Active body": ["N", "act"], "Output head": ["N", "head"], "Peak FLOPS": ["F"],
    "Layers": ["L"], "Link latency": ["τ"], "Activations exchanged": ["A"], "Link bandwidth": ["B", "link"],
    "Limit": ["R"], "Single Decode": ["R", "raw"], "Prompt tokens": ["P"], "Prompts": ["n"], "Tokens per prompt": ["P"],
    "Tokens per step": ["E"], "Acceptance": ["α"], "Drafts": ["k"], "Verify time": ["T", "verify"],
    "Draft time": ["T", "draft"], "Drafter weights read": ["W", "draft"], "Step time": ["T", "step"],
    "Requests": ["b"], "Bandwidth bound": ["R", "mem"], "Compute bound": ["R", "math"], "Interconnect bound": ["R", "link"],
    "Arithmetic per output token": ["Q", "tok"],
    "Weights size": ["S"], "Needs": ["M", "need"], "Usable memory": ["M", "gpu"], "Fits": ["fit"],
    "Parameters": ["N"], "Bits per weight": ["b"], "Headroom": ["h"], "Memory": ["M"], "Usable share": ["u"],
  };
  const v = (name) => {
    const [base, sub] = SYM[name];
    // a quantity as Numbers writes a reference in a formula: a rounded token with its name; its symbol on hover
    return `<span class="m-var" data-name="${name}" title="${base}${sub ? `_${sub}` : ""}">${name}</span>`;
  };
  // where each input comes from, in a sentence, and the catalog page that holds its numbers
  const SOURCES = {
    "Weights read": ["Active parameters × bits per weight: 4.5 for 4-bit, 8.5 for 8-bit, 16 for bf16; in a 2-bit build the experts' own 2-bit size.", "models"],
    "Weights touched": ["As Weights read, with every expert the prompt's tokens reach.", "models"],
    "Cache read": ["KV cache for the prompt plus half the answer, from the model's shape.", "models"],
    "Caches read": ["Cache read for every request in the batch.", "models"],
    "Prompt cache": ["The KV cache the prompt writes, from the model's config.", "models"],
    "Prompt caches": ["The KV cache every prompt writes, from the model's config.", "models"],
    "Prompts": [() => `The run's own, ${Pie.store.index.workloads?.prefill_batch?.parallel || "4–1,024"} cold prompts at once: pf16-512 is 16.`, "workloads"],
    "Tokens per prompt": [() => `The run's own: the ${Pie.store.index.workloads?.prefill_batch?.prompt_tokens ?? 512}-token prompt with the chat template and cold-cache tag each engine prefills with it, as its tok/s counts them.`, "workloads"],
    "Memory bandwidth": ["The machine's peak, from its spec sheet.", "hardware"],
    "Peak FLOPS": ["FP16 peak from the spec sheet, or the FP8 one for the matmuls an 8-bit or MXFP4 build runs there. Apple's are estimates.", "hardware"],
    "Active body": ["Parameters each token runs through, minus embeddings and output head.", "models"],
    "Output head": ["Vocabulary × hidden size, the last matmul.", "models"],
    "Layers": ["Transformer layers, from the model's config.json.", "models"],
    "Link latency": ["30 µs on Thunderbolt 5, 15 µs on PCIe 5.0 and NVLink.", "hardware"],
    "Link bandwidth": ["10 GB/s on Thunderbolt 5, 64 GB/s on PCIe 5.0 ×16, 900 GB/s on NVLink.", "hardware"],
    "Activations exchanged": ["Hidden state per all-reduce: tokens × hidden size × 2 bytes.", "models"],
    "Prompt tokens": [() => `The run's own, all in one pass: the ${Pie.store.index.workloads?.raw?.prompt_tokens ?? 512}-token prompt with the chat template and cold-cache tag the engine prefills with it (about 554 on Qwen, 605 on gpt-oss), as its tok/s counts them.`, "workloads"],
    "Requests": [() => `The run's own, ${Pie.store.index.workloads?.throughput?.parallel || "4–1,024"} at once: c1024 is 1,024 requests of 128 tokens in and 256 out.`, "workloads"],
    "Arithmetic per output token": ["2 × (Active body + Output head), plus the prompt's share.", "models"],
    "Acceptance": [() => `${Pie.specAlpha}%, set in the field above. The runs do not record it yet.`, null],
    "Drafts": ["Every width from 1 to 16 is tried; the Limit keeps the fastest.", null],
    "Drafter weights read": ["A 0.5 B block drafter at the model's bits per weight.", null],
    "Memory time": ["Single Decode's.", null],
    "Math time": ["Single Decode's.", null],
    "Interconnect time": ["Single Decode's.", null],
    "Single Decode": ["The Single Decode limit, without drafting.", null],
    "Parameters": ["Every parameter, not only the active ones: all of them sit in memory.", "models"],
    "Bits per weight": ["The build the engine runs: 4.5 for a Mac's 4-bit MLX build, 4.25 for MXFP4, 8 for FP8, 16 for bf16.", "models"],
    "Memory": ["The machine's memory, every GPU's together.", "hardware"],
    "Headroom": ["1.25: a quarter more for the KV cache, activations and the runtime.", null],
  };
  // a quantity's colour says where it comes from, the same on every workload, as Numbers colours each table's
  // references: the machine blue, the model green, the workload orange, an assumption grey, a worked-out term purple
  const KIND = { hardware: "#0a84ff", models: "#30d158", workloads: "#ff9f0a" };
  const GROUPS = ["workloads", "models", "hardware", null];
  const ASSUMED = new Set(["Acceptance", "Drafts", "Drafter weights read", "Headroom", "Usable share"]);
  const colorOf = (name) => KIND[SOURCES[name]?.[1]] || (ASSUMED.has(name) ? "#8e8e93" : "#bf5af2");
  const tint = (html) => html.replace(/class="m-(?:var|tag)" data-name="([^"]+)"/g, (m, name) => `${m} style="--pill: ${colorOf(name)}"`);
  // a term as Finder lists a tagged file: its colour as a dot before the name
  const tag = (name) => `<span class="m-tag" data-name="${name}"><span class="m-dot"></span>${name}</span>`;
  const o = (x) => `<span class="m-op">${x}</span>`;
  const par = (x) => `<span class="m-paren">(</span>${x}<span class="m-paren">)</span>`;
  // a fraction in one line, as Math Notes and Numbers write one: a slash, and brackets round a side that holds an
  // operator outside its own brackets, so every formula stays a single row
  const bare = (x) => x.replace(/<span class="m-paren[^"]*">\(<\/span>.*<span class="m-paren[^"]*">\)<\/span>/s, "");
  const side = (x) => (/class="m-op">[+−]</.test(bare(x)) ? par(x) : x);  // × binds before ÷, so only a sum needs them
  const fr = (num, den) => `${side(num)}${o("÷")}${side(den)}`;
  const fn = (name, ...args) => `<span class="m-fn">${name}</span>${par(args.join(`<span class="m-comma">,</span>`))}`;
  const sum = (...xs) => xs.join(o("+"));
  const times = (...xs) => xs.join(o("×"));
  const link = `2${o("×")}${v("Layers")}${o("×")}${par(sum(v("Link latency"), fr(v("Activations exchanged"), v("Link bandwidth"))))}`;

  // the effect of a simplification on the limit, as one quiet tag on its row
  const EFFECT = { up: "Raises the limit", down: "Lowers the limit", small: "Under 1%", choice: "Choice" };
  // which matmuls run at the FP8 peak rather than the 16-bit one, on every compute-bound chapter
  const NARROW = ["An FP8 build runs its body's matmuls at the chip's FP8 peak. An MXFP4 build runs its experts there too, against 8-bit activations, on chips whose tensor cores take MX block scales (Blackwell, MI350X); elsewhere they run at 16 bits. Attention, router and output head stay at the 16-bit peak, and no build is taken to cut its activations below 8 bits.", "choice"];

  const ceilingOf = (metric) => Pie.ceiling?.({ hardware: EXAMPLE.hardware, model: EXAMPLE.model, scheme: EXAMPLE.scheme, workload: "raw" }, metric);

  const CONTENT = [
    {
      id: "decode",
      lede: "One request decodes one token at a time. Each token reads the model's active weights and its context from memory and does two operations per active weight. The limit is whichever of the two takes longer.",
      equations: [
        eq("Memory time", fr(sum(v("Weights read"), v("Cache read")), v("Memory bandwidth")), ["roofline", "shazeer"]),
        eq("Math time", fr(`2${o("×")}${par(sum(v("Active body"), v("Output head")))}`, v("Peak FLOPS")), ["kaplan"]),
        eq("Interconnect time", link, ["megatron"]),
        eq("Limit", fr("1", fn("max", v("Memory time"), v("Math time"), v("Interconnect time"))), ["roofline"]),
      ],
      why: [
        "Decode reads every active weight once per token, so memory bandwidth, not arithmetic, sets the limit {roofline} {pope}.",
      ],
      assumptions: [
        ["Bandwidth and FLOPS are the spec sheet's peaks. Real kernels reach less, so results should stay below 100%.", "up"],
        ["Weights are read once per token, with no reuse from cache, and nothing else is read besides the context cache.", "up"],
        ["Attention arithmetic, activations, sampling and kernel launches cost nothing.", "up"],
        ["4-bit weights are 4.5 bits each: 4 bits plus a 16-bit scale and bias per group of 64. 8-bit is 8.5 bits, bf16 16.", null],
        ["A 2-bit scheme puts only the routed experts in 2 bits. MLX's keeps them at 2.25 bits (a 16-bit scale and bias per 128) and the rest at 4.5; llama.cpp's Q2_K mix keeps their gate and up in Q2_K (2.625 bits) and their down in Q3_K (3.4375), the output head in Q6_K, and nothing below Q2_K.", "up"],
        ["The context is the prompt plus half the answer, the average over the answer's tokens.", null],
        ["Parameter counts, embedding sizes and cache shapes are each model's own, from its config.json and safetensors on Hugging Face.", null],
        ["The input embedding is only looked up, one row a token, so it is not counted as read; the output head is a full matmul and is. Gemma's per-layer embedding tables and Qwen3.8-Flash-Next's n-gram table are lookups too.", null],
        ["The cache read is the model's real one: full-attention layers read every cached token, sliding-window layers their window, and linear-attention layers read and write their fixed state, in bf16: the configs ask fp32, but pie and TensorRT-LLM keep bf16, and the limit takes the smallest an engine keeps.", "up"],
      ],
      check: { workload: "raw", metric: "decode", key: "decode_tok_s" },
      example: () => {
        const c = ceilingOf("decode");
        if (!c) return null;
        const p = c.parts;
        return {
          inputs: [
            ["Weights read", gb(p.weightGB), `${p.body.toFixed(2)} B body + ${p.head.toFixed(2)} B output head, ${p.bits} bits`],
            ["Cache read", gb(p.cacheGB), `${p.context} tokens, from the model's config`],
            ["Memory bandwidth", `${p.bw} GB/s`, "Spec sheet"],
            ["Peak FLOPS", `${p.tflops} TFLOPS`, "Spec sheet"],
          ],
          values: [ms(p.readS), ms(p.mathS), `${num(c.tps)} tok/s`],
        };
      },
    },
    {
      id: "spec",  // the setup pop-up's id for Spec Decode, so picking it opens this chapter
      lede: "A small drafter proposes the next few tokens and the model checks all of them in one pass, keeping each one it agrees with. More drafts cost more and add less, so the limit is the draft width that gives the most tokens per second.",
      equations: [
        eq("Tokens per step", fr(`1${o("−")}${v("Acceptance")}${o("^")}${par(sum(v("Drafts"), "1"))}`, `1${o("−")}${v("Acceptance")}`), ["leviathan"]),
        eq("Verify time", fn("max", v("Memory time"), `${par(sum(v("Drafts"), "1"))}${o("×")}${v("Math time")}`), ["roofline"]),
        eq("Draft time", fr(v("Drafter weights read"), v("Memory bandwidth")), ["roofline"]),
        eq("Step time", sum(v("Verify time"), v("Draft time")), ["leviathan", "chen"]),
        eq("Limit", fn("max", v("Single Decode"), fr(v("Tokens per step"), v("Step time"))), ["leviathan"]),
      ],
      symbols: "k is the number of drafted tokens per step and α the chance that each is accepted. Memory time and Math time are Single Decode's. A block drafter proposes all k drafts in one pass, so its Draft time is one read of its weights; a drafter that proposes one token at a time pays k of them. The limit tries every k from 1 to 16 and keeps the fastest, and falls back to Single Decode when no k pays.",
      why: [
        "One pass checks k + 1 tokens for one read of the weights, and greedy verification keeps the output unchanged {leviathan} {chen}.",
        "Draft k only counts if every draft before it was accepted, so each extra draft adds α^k tokens: at 70%, four drafts keep 2.8 tokens, eight 3.2 and sixteen 3.3, the most any k can give being 1 ÷ (1 − α).",
        "Decode is memory-bound, so the first extra rows of a verify are nearly free. Once (k + 1) × Math time passes Memory time, every row costs its arithmetic and wider drafts lose. Many requests at once reach that point at a smaller k, which is why engines draft less, or not at all, under load.",
        "a is measured, not given: over a run, a = accepted drafts ÷ (accepted drafts + rejections), counting one rejection for each step that stopped before its last draft. The drafter's authors report it for their benchmarks, but it changes with the prompt, so an engine reads it from its own steps.",
      ],
      assumptions: [
        ["Each draft is accepted independently with the same chance a. Real acceptance falls along the draft.", "up"],
        ["The drafter proposes its whole block in one pass, as DFlash does. A drafter that proposes one token at a time pays k passes.", "up"],
        ["The drafter has 0.5 B parameters and 70% acceptance, the Limit page's defaults. Neither is measured per run.", null],
        ["Everything Single Decode assumes.", "up"],
      ],
      check: null,
      noCheck: "Not checked yet: the runs do not record their acceptance rate, and the limit depends on it.",
      example: () => {
        const c = ceilingOf("decode");
        if (!c) return null;
        const p = c.parts;
        const draft = Math.max((SPEC.drafter * p.bytes) / p.bw, (2 * SPEC.drafter * 1e9) / (p.tflops * 1e12));
        const at = (k) => {
          const kept = (1 - SPEC.a ** (k + 1)) / (1 - SPEC.a);
          const verify = Math.max(p.readS, (p.flopsPerToken * (k + 1)) / (p.tflops * 1e12));
          return { k, kept, verify, tps: kept / (verify + draft) };
        };
        const best = Array.from({ length: SPEC.widest }, (_, i) => at(i + 1)).reduce((x, y) => (y.tps > x.tps ? y : x));
        const plain = 1 / Math.max(p.readS, p.flopsPerToken / (p.tflops * 1e12));
        return {
          inputs: [
            ["Acceptance, a", `${Math.round(SPEC.a * 100)}%`, "Assumed"],
            ["Best k", `${best.k}`, `the fastest of 1 to ${SPEC.widest}`],
            ["Verify time", ms(best.verify), `Single Decode with ${best.k + 1} tokens`],
            ["Draft time", ms(draft), `one pass of a ${SPEC.drafter} B block drafter, assumed`],
          ],
          values: [best.kept.toFixed(2), ms(best.verify), ms(best.verify + draft), `${num(Math.max(plain, best.tps))} tok/s`],
        };
      },
    },
    {
      id: "batching",
      lede: "Many requests decode together and share each read of the weights. Adding requests raises the speed until the arithmetic runs out; from there it stays flat.",
      equations: [
        eq("Bandwidth bound", fr(times(v("Requests"), v("Memory bandwidth")), sum(v("Weights read"), v("Caches read"))), ["roofline", "pope"]),
        eq("Compute bound", fr(v("Peak FLOPS"), v("Arithmetic per output token")), ["kaplan"]),
        eq("Interconnect bound", fr(v("Requests"), v("Interconnect time")), ["megatron"]),
        eq("Limit", fn("min", v("Bandwidth bound"), v("Compute bound"), v("Interconnect bound")), ["roofline"]),
      ],
      symbols: "The arithmetic per output token is 2 × (active body + output head), plus each request's prompt, 2 × active body per prompt token, spread over its answer: the prompt uses the same FLOPS but does not count as output. The prompt's pass writes the answer's first token, so decode steps write all of the answer but that one, and, as in prefill, Gemma's KV-sharing layers run only for the prompt's last token.",
      why: [
        "A batch reads the weights once for all its requests, so speed grows with the batch until it meets the compute roof {pope} {roofline}.",
      ],
      assumptions: [
        ["Each request's cache is read every step, at the middle of its answer, from the model's real cache shape.", null],
        ["All requests stay in flight for the whole run, so every step carries the full batch.", "up"],
        ["Attention arithmetic is not counted.", "up"],
        ["A mixture of experts touches more experts the more tokens a step carries, assuming each token picks its experts independently. Tokens that agree on their experts read fewer of them, so every batched request has its own prompt: with one prompt for all, every request wrote the same answer and the whole batch read the same few experts.", "down"],
        ["Peak FLOPS is the spec sheet's. On Apple M5 chips it includes the GPU's neural accelerators, which an engine may not use.", "up"],
        NARROW,
      ],
      check: { workload: "throughput", metric: "throughput", key: "output_tok_s", batched: true },
      example: () => {
        const bound = Pie.platform?.batchedBound?.(EXAMPLE.hardware, EXAMPLE.model);
        const w = Pie.store.index.workloads?.throughput;
        const hw = Pie.store.index.hardware?.[EXAMPLE.hardware];
        if (!bound || !w || !hw) return null;
        const md = Pie.store.index.models?.[EXAMPLE.model];
        return {
          inputs: [
            ["Requests", `${w.concurrency}`, "Workload"],
            ["Each request", `${w.prompt_tokens} in, ${w.output_tokens} out`, "Workload"],
            ["Weights read a step", gb(bound.parts.weightGB), "Body touched + output head, 4.5 bits"],
            ["Caches read a step", gb(bound.parts.cacheGB), `${w.concurrency} requests, from the model's config`],
            ["Memory bandwidth", `${hw.bandwidth_gbs} GB/s`, "Spec sheet"],
            ["Peak FLOPS", `${hw.tflops_fp16} TFLOPS`, "Spec sheet"],
          ],
          values: [`${num(bound.bandwidth)} tok/s`, `${num(bound.compute)} tok/s`, `${num(bound.tps)} tok/s`],
        };
      },
      figure: () => {
        const bound = Pie.platform?.batchedBound?.(EXAMPLE.hardware, EXAMPLE.model);
        const w = Pie.store.index.workloads?.throughput;
        return bound && w ? roofline(bound, w.concurrency) : "";
      },
    },
    {
      id: "prefill",
      lede: "The whole prompt goes through in one pass. The weights are read once for all of its tokens, so arithmetic, not memory, sets the speed.",
      equations: [
        eq("Memory time", fr(sum(v("Weights touched"), v("Prompt cache")), v("Memory bandwidth")), ["roofline"]),
        eq("Math time", fr(`2${o("×")}${par(sum(times(v("Active body"), v("Prompt tokens")), v("Output head")))}`, v("Peak FLOPS")), ["kaplan"]),
        eq("Interconnect time", link, ["megatron"]),
        eq("Limit", fr(v("Prompt tokens"), fn("max", v("Memory time"), v("Math time"), v("Interconnect time"))), ["roofline"]),
      ],
      why: [
        "The whole prompt goes through one pass that reads the weights once, so prefill is compute-bound {roofline} {kaplan}.",
      ],
      assumptions: [
        ["In a mixture-of-experts model, the weights touched assume each token picks its experts independently and uniformly. Real routing is uneven. This only changes memory time, which is not the limit here.", "small"],
        ["Attention arithmetic, which grows with the square of the prompt, is not counted. At 512 tokens it is a few percent.", "up"],
        ["Only the last prompt token needs the output head: the first answer token is all prefill has to produce.", null],
        ["Gemma's KV sharing: layers that reuse an earlier layer's K and V run only for the last prompt token, since the others only fill the cache.", null],
        ["FLOPS is the spec sheet's peak. Apple publishes no FP16 figure, so the catalog's are estimates.", "up"],
        NARROW,
        ["On Apple M1 to M4 chips pie splits a dense SwiGLU model's MLP between the GPU and the Neural Engine, so pie's limit there adds the Neural Engine's FP16 peak to the GPU's. No other engine uses the Neural Engine, and its peak is far above what a matmul reaches on it. pie runs its share in int8, which Apple rates at twice the FP16 peak from M4 on; the limit counts FP16, as for every unit.", "up"],
      ],
      check: { workload: "raw", metric: "prefill", key: "prefill_tok_s" },
      // shown only while results run above the limit: what is known about why, and what is not
      open: "The result above the limit is on the Apple M5, whose FLOPS figure is the weakest input here: Apple publishes none, and per GPU core the catalog's M5 figure is a fifth below its M5 Max figure (0.94 against 1.18 TFLOPS), so it is probably too low. A prompt-cache hit in the engine, which the timing would not see, is the other open explanation.",
      example: () => {
        const c = ceilingOf("prefill");
        if (!c) return null;
        const p = c.parts;
        return {
          inputs: [
            ["Prompt tokens", `${p.tokens}`, "Workload"],
            ["Weights read", gb(p.weightGB), `${p.body.toFixed(2)} B body + ${p.head.toFixed(2)} B output head, ${p.bits} bits`],
            ["Memory bandwidth", `${p.bw} GB/s`, "Spec sheet"],
            ["Peak FLOPS", `${p.tflops} TFLOPS`, "Spec sheet"],
          ],
          values: [ms(p.readS), ms(p.mathS), `${num(c.tps)} tok/s`],
        };
      },
    },
    {
      id: "pbatch",
      lede: "Many prompts go through together, each in one pass. The weights are read once for every prompt's tokens, so the step is arithmetic: the speed is the chip's peak rate over the work each token needs.",
      equations: [
        eq("Memory time", fr(sum(v("Weights touched"), v("Prompt caches")), v("Memory bandwidth")), ["roofline"]),
        eq("Math time", fr(`2${o("×")}${v("Prompts")}${o("×")}${par(sum(times(v("Active body"), v("Tokens per prompt")), v("Output head")))}`, v("Peak FLOPS")), ["kaplan"]),
        eq("Interconnect time", link, ["megatron"]),
        eq("Limit", fr(times(v("Prompts"), v("Tokens per prompt")), fn("max", v("Memory time"), v("Math time"), v("Interconnect time"))), ["roofline"]),
      ],
      why: [
        "Batching prompts only adds tokens to a pass that is already compute-bound, so the limit is the same arithmetic roof as one prompt's, reached with less idle time between passes {roofline} {kaplan}.",
      ],
      assumptions: [
        ["A mixture-of-experts batch touches nearly every expert, so the weights touched are close to all of them; this only changes memory time, which is not the limit here.", "small"],
        ["Attention arithmetic, which grows with the square of each prompt, is not counted.", "up"],
        ["Each prompt needs the output head once, for its first answer token.", null],
        ["FLOPS is the spec sheet's peak. Apple publishes no FP16 figure, so the catalog's are estimates.", "up"],
        NARROW,
        ["Single Prefill's Neural Engine share: pie's limit on Apple M1 to M4 chips adds the Neural Engine's FP16 peak for a dense SwiGLU model.", "up"],
      ],
    },
  ];

  // Memory Fit: whether a model fits a machine, worked out for every pair whether it ran or not; a crossed circle in
  // the grid where it does not
  const FIT = {
    id: "fit",
    equations: [
      eq("Weights size", fr(times(v("Parameters"), v("Bits per weight")), "8"), ["kaplan"]),
      eq("Needs", times(v("Weights size"), v("Headroom")), ["kwon"]),
      eq("Fits", `${v("Needs")}${o("≤")}${v("Memory")}`, []),
    ],
  };

  // a chapter per workload in the grid's pop-up: the same names, in the same order (decode, then prefill), taken from
  // its list so the two cannot drift apart. A workload without a chapter written for it has none
  const CHAPTERS = (Pie.platform?.metrics() || []).map((m) => {
    const text = CONTENT.find((t) => t.id === m.id);
    return text && { ...text, title: m.label };
  }).filter(Boolean);

  // batched decode drawn as a roofline: tokens per second against requests at once, both axes doubling;
  // the bandwidth line climbs with the batch until it meets the flat compute ceiling, and the lower of the two is the limit
  const roofline = (bound, at) => {
    const W = 640, H = 220, L = 8, R = 8, T = 18, Bm = 30;
    const batches = [1, 2, 4, 8, 16, 32, 64, 128, 256];
    const perOne = bound.bandwidth / at;  // the bandwidth limit of one request
    const lo = Math.min(perOne, bound.compute) / 2;
    const hi = Math.max(bound.compute, perOne * 256) * 1.6;
    const x = (n) => L + (Math.log2(n) / 8) * (W - L - R);
    const y = (t) => T + (1 - Math.log(t / lo) / Math.log(hi / lo)) * (H - T - Bm);
    const knee = Math.min(256, Math.max(1, bound.compute / perOne));
    // the knee is a point of its own, so the limit turns a sharp corner where the two bounds meet
    const points = [...new Set([...batches, knee])].sort((p, q) => p - q);
    const line = (f) => points.map((n, i) => `${i ? "L" : "M"}${x(n).toFixed(1)},${y(f(n)).toFixed(1)}`).join("");
    const limit = (n) => Math.min(perOne * n, bound.compute);
    return `
      <figure class="roofline">
        <svg viewBox="0 0 ${W} ${H}" role="img" aria-label="The limit against requests at once: bandwidth bound below ${num(knee)} requests, compute bound above">
          ${batches.map((n) => `<line class="roof-grid" x1="${x(n)}" x2="${x(n)}" y1="${T}" y2="${H - Bm}"/><text class="roof-tick" x="${x(n)}" y="${H - 10}">${n}</text>`).join("")}
          <path class="roof-other" d="${line((n) => perOne * n)}"/>
          <path class="roof-other" d="M${x(1)},${y(bound.compute)}H${x(256)}"/>
          <path class="roof-limit" d="${line(limit)}"/>
          <circle class="roof-dot" cx="${x(at)}" cy="${y(limit(at))}" r="4.5"/>
          <text class="roof-label" x="${x(1) + 4}" y="${y(bound.compute) - 8}">Compute bound · ${num(bound.compute)} tok/s</text>
          <text class="roof-label" x="${x(1) + 4}" y="${y(perOne) + 18}">Bandwidth bound · ${num(perOne)} tok/s per request</text>
          <text class="roof-label is-dot" x="${x(at) + 9}" y="${y(limit(at)) + 16}">${at} requests · ${num(limit(at))} tok/s</text>
        </svg>
        <figcaption>Figure 1. The limit against requests at once, both axes doubling. Below ${num(knee)} requests memory sets the pace; above, arithmetic.</figcaption>
      </figure>`;
  };

  // the chapter is the grid's workload: one choice for both pages, kept with the rest of the view
  let current = CHAPTERS[0].id;
  let state = null;

  // a Methodology chapter's page of it, read as a document rather than a table: the workload's tabs, its lede, each
  // formula on a line of its own with its sources, the terms as a definition list, then why and what is assumed
  const doc = (kind) => {
    const c = kind === "fit" ? FIT : CHAPTERS.find((ch) => ch.id === current);
    const cite = (key) => {
      const r = REFS[key];
      const author = r.authors.split(",")[0].replace(/ et al\.?$/, "").split(" ").pop();
      return `<a class="cite" href="${r.url}" target="_blank" rel="noopener" title="${esc(`${r.authors} ${r.title}. ${r.venue}, ${r.year}`)}">${esc(author)} ${r.year}</a>`;
    };
    const prose = (text) => esc(text).replace(/\s?\{(\w+)\}/g, (_, key) => (REFS[key] ? ` ${cite(key)}` : ""));
    const made = new Set(c.equations.map((e) => e.result));
    const used = [...new Set(c.equations.flatMap((e) => [...e.math.matchAll(/data-name="([^"]+)"/g)].map((m) => m[1])))]
      .filter((name) => !made.has(name) && SOURCES[name])
      .sort((x, y) => GROUPS.indexOf(SOURCES[x][1]) - GROUPS.indexOf(SOURCES[y][1]));
    const terms = used.map((name) => {
      const [text, from] = SOURCES[name];
      const how = typeof text === "function" ? text() : text;
      const source = from ? ` <a class="cite" role="link" tabindex="0" data-go="${from}">${esc(Pie.schema[from].label)}</a>` : "";
      return `<dt>${tag(name)}</dt><dd>${esc(how)}${source}</dd>`;
    }).join("");
    return tint(`<div class="m-doc">
      ${c.lede ? `<p>${prose(c.lede)}</p>` : ""}
      <h3>Formulas</h3>
      <div class="m-doc-eqs">${c.equations.map((e) => `
        <div class="m-doc-eq"><span class="m-doc-eq-line">${tag(e.result)}<span class="op">=</span><span class="m-eq">${e.math}</span></span>${e.cites.length ? `<span class="m-doc-cite">${e.cites.map(cite).join(", ")}</span>` : ""}</div>`).join("")}</div>
      ${terms ? `<h3>Terms</h3><dl class="m-doc-terms">${terms}</dl>` : ""}
      ${c.why?.length ? `<h3>Why</h3>${c.why.map((t) => `<p>${prose(t)}</p>`).join("")}` : ""}
      ${c.assumptions?.length ? `<h3>Assumptions</h3><ul class="m-doc-list">${c.assumptions.map(([t]) => `<li>${prose(t)}</li>`).join("")}</ul>` : ""}</div>`);
  };

  // `kind` is "fit" for Memory Fit, else the workload's limit
  const page = (kind = state.table === "fit" ? "fit" : "limit") => {
    const c = kind === "fit" ? FIT : CHAPTERS.find((ch) => ch.id === current);

    // a citation is the work's first author and year, a link straight to the paper
    const cite = (key) => {
      const r = REFS[key];
      const author = r.authors.split(",")[0].replace(/ et al\.?$/, "").split(" ").pop();
      return `<a class="cite" href="${r.url}" target="_blank" rel="noopener" title="${esc(`${r.authors} ${r.title}. ${r.venue}, ${r.year}`)}">${esc(author)} ${r.year}</a>`;
    };
    const prose = (text) => esc(text).replace(/\s?\{(\w+)\}/g, (_, key) => (REFS[key] ? cite(key) : ""));
    // the formulas as rows of the site's data table: the result's name, then its equation in symbols
    const formulaRows = c.equations.map((e) => `
      <tr><td class="row-number"></td><td class="lim-term">${tag(e.result)}</td><td class="lim-formula"><span class="m-eq">${e.math}</span></td><td class="lim-fill"></td><td class="lim-source">${e.cites.map(cite).join(", ")}</td></tr>`).join("");

    // every quantity the formulas use and none of them works out, in order of first use: how it is found and where
    const made = new Set(c.equations.map((e) => e.result));
    const used = [...new Set(c.equations.flatMap((e) => [...e.math.matchAll(/data-name="([^"]+)"/g)].map((m) => m[1])))]
      .filter((name) => !made.has(name) && SOURCES[name])
      // grouped by where they come from, so each colour reads as one block: workload, model, machine, the rest
      .sort((x, y) => GROUPS.indexOf(SOURCES[x][1]) - GROUPS.indexOf(SOURCES[y][1]));
    const inputRows = used.map((name) => {
      const [text, from] = SOURCES[name];
      const how = typeof text === "function" ? text() : text;  // a workload's number, read from the catalog
      const source = from ? `<a class="cite" role="link" tabindex="0" data-go="${from}">${esc(Pie.schema[from].label)}</a>` : "";
      return `<tr><td class="row-number"></td><td class="lim-term">${tag(name)}</td><td class="lim-how" title="${esc(how)}">${esc(how)}</td><td class="lim-fill"></td><td class="lim-source">${source}</td></tr>`;
    }).join("");

    // the bar: the grid's setup control, with Spec Decode as a segment of its own since this page has a chapter for it
    const bar = `
      <div class="platform-bar limit-bar methods-bar">
        ${Pie.platform.setupControl(c.id, ["decode", "spec", "prefill", "batching"])}
        ${c.id === "spec" ? `
        ${Pie.specField()}` : ""}
      </div>`;

    // the chapter as the site's other pages: the formulas as a data table under the bar, each citing its works by
    // name, linked
    // Memory has no workload to pick, but keeps the bar, empty, so the page sits under the toolbar as the rest do and
    // filters have a place when it grows them
    return `${c === FIT ? `<div class="platform-bar limit-bar methods-bar" aria-hidden="true"></div>` : bar}
      <div class="lim-tables">
        <table class="data-table lim-table">
          <thead><tr><th class="row-number" aria-label="Row"></th><th>Term</th><th>Definition</th><th class="lim-fill"></th><th class="lim-source">Reference</th></tr></thead>
          <tbody>${tint(formulaRows + inputRows)}</tbody>
        </table>
      </div>`;
  };


  element.addEventListener("click", (event) => {
    // a citation scrolls to its reference, as a footnote link does
    // a catalog link opens that page, as the sidebar would
    const go = event.target.closest("[data-go]");
    if (go) {
      document.querySelector(`.sidebar-item[data-table="${go.dataset.go}"]`)?.click();
      return;
    }
    // a setup segment: the grid's own setup, so a pick changes both pages
    const tab = event.target.closest("[data-mode]");
    if (tab && state) {
      state.platform.mode = tab.dataset.mode;
      Pie.platform.changed();
      return;
    }
  });

  // the acceptance field: the input follows the shared value when it changes elsewhere
  Pie.bindSpecField(element, () => {
    const input = element.querySelector("[data-alpha]");
    if (input && document.activeElement !== input) input.value = Pie.specAlpha;
    // and the Acceptance row says the new value
    const row = element.querySelector('.m-tag[data-name="Acceptance"]')?.closest("tr")?.querySelector(".lim-how");
    if (row) row.textContent = row.title = SOURCES.Acceptance[0]();
  });

  Pie.methods = {
    // the limit's workload as a pop-up button at the right of the chapter's title, as the Overview sets a card's pick:
    // its mark, its name and the menu's chevron; it opens Pie.platform's setup menu
    setupPick() {
      const NAMES = { decode: "Single Decode", prefill: "Single Prefill", batching: "Batched Decode", pbatch: "Batched Prefill" };
      return `<button class="filter-button board-title-pick" type="button" data-methods-setup aria-haspopup="menu" aria-label="Workload">${Pie.platform.degree(current)}${esc(NAMES[current] || current)}<svg class="popup-chevron" viewBox="0 0 10 14" aria-hidden="true"><path d="M2 5l3-3 3 3M2 9l3 3 3-3"/></svg></button>`;
    },
    // its menu (the popover's "methods:setup"): the four workloads after their marks, the picked one checked; a pick is the
    // grid's workload too, so both pages agree
    menu(k) {
      if (k !== "setup") return [];
      const NAMES = { decode: "Single Decode", prefill: "Single Prefill", batching: "Batched Decode", pbatch: "Batched Prefill" };
      return Object.keys(NAMES).map((id) => ({ value: id, label: NAMES[id], selected: id === current, detail: id === "decode" || id === "prefill" ? "Latency" : "Throughput", icon: Pie.platform.degree(id) }));
    },
    pick(k, value) {
      if (k === "setup" && state && ["decode", "prefill", "batching", "pbatch"].includes(value)) state.platform.mode = value;
    },
    // a Methodology chapter's tables: the limit for the grid's workload (its setup bar on top) or Memory Fit, and the key
    // that changes when they would read differently
    chapter(kind, viewState) {
      state = viewState;
      // no Speculative Decode here: the grid on it opens the first chapter
      current = CHAPTERS.some((c) => c.id === state.platform.mode && c.id !== "spec") ? state.platform.mode : CHAPTERS[0].id;
      return { html: doc(kind), key: `${kind === "fit" ? "fit" : current}@${state.release}@${Pie.specAlpha}` };
    },
    render(viewState) {
      state = viewState;
      element.hidden = state.table !== "methods" && state.table !== "fit";
      // the grid's workload, or the first chapter when that workload has none written yet
      current = CHAPTERS.some((c) => c.id === state.platform.mode) ? state.platform.mode : CHAPTERS[0].id;
      const key = `${state.table === "fit" ? "fit" : current}@${state.release}`;
      if (!element.hidden && element.dataset.key !== key) {
        element.innerHTML = page();
        element.dataset.key = key;
        element.scrollTop = 0;
      }
    },
  };
})();
