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
    kwon: { authors: "W. Kwon et al.", title: "Efficient Memory Management for Large Language Model Serving with PagedAttention", venue: "SOSP 2023, arXiv:2309.06180", year: 2023, url: "https://arxiv.org/abs/2309.06180" },
  };

  // the worked examples: one machine and one model from the catalog, at the 4-bit weights the runs use
  const EXAMPLE = { hardware: "m5-max-128g", model: "qwen3.5-4b", scheme: "affine_u4_g64" };
  // the Limit page's speculation defaults: four drafts, 70% accepted, a half-billion-parameter drafter
  const SPEC = { k: 4, a: 0.7, drafter: 0.5 };

  const num = (n) => (n >= 100 ? Math.round(n).toLocaleString("en-US") : n >= 10 ? n.toFixed(0) : n.toFixed(1));
  const ms = (s) => `${(s * 1e3).toFixed(s * 1e3 >= 10 ? 0 : 2)} ms`;
  const gb = (n) => `${n.toFixed(2)} GB`;

  // a formula in words, numbered as a paper numbers its equations: the result, its terms, and the works it rests on
  const eq = (result, terms, cites = []) => ({ result, terms, cites });

  // the effect of a simplification on the limit, as one quiet tag on its row
  const EFFECT = { up: "Raises the limit", down: "Lowers the limit", small: "Under 1%", choice: "Choice" };

  const ceilingOf = (metric) => Pie.ceiling?.({ hardware: EXAMPLE.hardware, model: EXAMPLE.model, scheme: EXAMPLE.scheme, workload: "raw" }, metric);

  const CONTENT = [
    {
      id: "decode",
      lede: "One request decodes one token at a time. Each token reads the model's active weights and its context from memory and does two operations per active weight. The limit is whichever of the two takes longer.",
      equations: [
        eq("Memory time", ["(", "Weights read", "+", "Cache read", ")", "÷", "Memory bandwidth"], ["roofline", "shazeer"]),
        eq("Math time", ["2", "×", "(", "Active body", "+", "Output head", ")", "÷", "Peak FLOPS"], ["kaplan"]),
        eq("Limit", ["1 token", "÷", "max(", "Memory time", ",", "Math time", ")"], ["roofline"]),
      ],
      why: [
        "A chip can run no faster than its slowest resource: the time to move the bytes or the time to do the arithmetic, whichever is longer. This is the roofline model {roofline}.",
        "A forward pass costs about two floating-point operations per parameter per token, one multiply and one add {kaplan}. In a mixture-of-experts model only the active parameters count.",
        "Decoding one token at a time must read every active weight for every token, so decode is limited by memory bandwidth long before arithmetic {shazeer} {pope}. On the machines here, math time is under a tenth of memory time.",
      ],
      assumptions: [
        ["Bandwidth and FLOPS are the spec sheet's peaks. Real kernels reach less, so results should stay below 100%.", "up"],
        ["Weights are read once per token, with no reuse from cache, and nothing else is read besides the context cache.", "up"],
        ["Attention arithmetic, activations, sampling and kernel launches cost nothing.", "up"],
        ["4-bit weights are 4.5 bits each: 4 bits plus a 16-bit scale and bias per group of 64. 8-bit is 8.5 bits, bf16 16.", null],
        ["The context is the prompt plus half the answer, the average over the answer's tokens.", null],
        ["Parameter counts, embedding sizes and cache shapes are each model's own, from its config.json and safetensors on Hugging Face.", null],
        ["The input embedding is only looked up, one row a token, so it is not counted as read; the output head is a full matmul and is. Gemma's per-layer embedding tables are lookups too.", null],
        ["The cache read is the model's real one: full-attention layers read every cached token, sliding-window layers their window, and linear-attention layers read and write their fixed state.", null],
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
      id: "speculation",
      lede: "A small drafter proposes the next few tokens and the model checks all of them in one pass, keeping each one it agrees with. Each kept token costs a fraction of a read of the weights.",
      equations: [
        eq("Tokens per step", ["(", "1", "−", "a^(k+1)", ")", "÷", "(", "1", "−", "a", ")"], ["leviathan"]),
        eq("Step time", ["Verify time", "+", "k", "×", "Draft time"], ["leviathan", "chen"]),
        eq("Limit", ["Tokens per step", "÷", "Step time"], ["leviathan"]),
      ],
      symbols: "k is the number of drafted tokens per step and a the chance that each is accepted. The verify time is Raw Decode's memory and math time with k + 1 tokens in the pass; the draft time is the same for the drafter.",
      why: [
        "With k drafted tokens, each accepted independently with probability a, the expected number of tokens a step produces is (1 − aᵏ⁺¹) ÷ (1 − a) {leviathan}. It counts the token the model always adds after the last accepted draft.",
        "Verifying k + 1 tokens in one pass reads the weights once, as decode does, so while decode is memory-bound the verify pass costs about the same as one decode step {chen}.",
        "With greedy verification the model keeps exactly the tokens it would have produced alone, so the output is unchanged {leviathan}.",
      ],
      assumptions: [
        ["Each draft is accepted independently with the same chance a. Real acceptance falls along the draft.", "up"],
        ["The drafter proposes its k tokens one at a time. Drafters that propose a whole block in one pass are cheaper.", "down"],
        ["The drafter has 0.5 B parameters and 70% acceptance, the Limit page's defaults. Neither is measured per run.", null],
        ["Everything Raw Decode assumes.", "up"],
      ],
      check: null,
      noCheck: "Not checked yet: the runs do not record their acceptance rate, and the limit depends on it.",
      example: () => {
        const c = ceilingOf("decode");
        if (!c) return null;
        const p = c.parts;
        const kept = (1 - SPEC.a ** (SPEC.k + 1)) / (1 - SPEC.a);
        const verify = Math.max(p.readS, (p.flopsPerToken * (SPEC.k + 1)) / (p.tflops * 1e12));
        const draft = Math.max((SPEC.drafter * p.bytes) / p.bw, (2 * SPEC.drafter * 1e9) / (p.tflops * 1e12));
        return {
          inputs: [
            ["Drafts per step, k", `${SPEC.k}`, "Assumed"],
            ["Acceptance, a", `${Math.round(SPEC.a * 100)}%`, "Assumed"],
            ["Verify time", ms(verify), "Raw Decode with k + 1 tokens"],
            ["Draft time", ms(draft), `${SPEC.drafter} B drafter, assumed`],
          ],
          values: [kept.toFixed(2), ms(verify + SPEC.k * draft), `${num(kept / (verify + SPEC.k * draft))} tok/s`],
        };
      },
    },
    {
      id: "batching",
      lede: "Many requests decode together and share each read of the weights. Adding requests raises the speed until the arithmetic runs out; from there it stays flat.",
      equations: [
        eq("Bandwidth bound", ["Requests", "×", "Memory bandwidth", "÷", "(", "Weights read", "+", "Caches read", ")"], ["roofline", "pope"]),
        eq("Compute bound", ["Peak FLOPS", "÷", "Arithmetic per output token"], ["kaplan"]),
        eq("Limit", ["min(", "Bandwidth bound", ",", "Compute bound", ")"], ["roofline"]),
      ],
      symbols: "The arithmetic per output token is 2 × (active body + output head), plus each request's prompt, 2 × active body per prompt token, spread over its answer: the prompt uses the same FLOPS but does not count as output.",
      why: [
        "One step of a batch reads the weights once for every request in it, so the bytes per token fall as the batch grows {pope} {kwon}. The arithmetic per token does not fall: it stays at two operations per active parameter {kaplan}.",
        "So speed grows with the batch until it meets the compute roof, then stays flat. Where the two lines meet is the batch at which the machine turns compute-bound {roofline} {yuan}.",
      ],
      assumptions: [
        ["Each request's cache is read every step, at the middle of its answer, from the model's real cache shape.", null],
        ["All requests stay in flight for the whole run, so every step carries the full batch.", "up"],
        ["Attention arithmetic is not counted.", "up"],
        ["A mixture of experts touches more experts the more tokens a step carries, assuming each token picks its experts independently.", "up"],
        ["Peak FLOPS is the spec sheet's. On Apple M5 chips it includes the GPU's neural accelerators, which an engine may not use.", "up"],
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
        eq("Memory time", ["(", "Weights touched", "+", "Prompt cache", ")", "÷", "Memory bandwidth"], ["roofline"]),
        eq("Math time", ["2", "×", "(", "Active body", "×", "Prompt tokens", "+", "Output head", ")", "÷", "Peak FLOPS"], ["kaplan"]),
        eq("Limit", ["Prompt tokens", "÷", "max(", "Memory time", ",", "Math time", ")"], ["roofline"]),
      ],
      why: [
        "The arithmetic grows with the prompt but the weights are read once, so a pass of hundreds of tokens is compute-bound on every machine here {roofline} {pope}.",
        "Each prompt token costs two operations per active parameter, as in decode {kaplan}.",
      ],
      assumptions: [
        ["In a mixture-of-experts model, the weights touched assume each token picks its experts independently and uniformly. Real routing is uneven. This only changes memory time, which is not the limit here.", "small"],
        ["Attention arithmetic, which grows with the square of the prompt, is not counted. At 512 tokens it is a few percent.", "up"],
        ["Only the last prompt token needs the output head: the first answer token is all prefill has to produce.", null],
        ["Gemma's KV sharing: layers that reuse an earlier layer's K and V run only for the last prompt token, since the others only fill the cache.", null],
        ["FLOPS is the spec sheet's peak. Apple publishes no FP16 figure, so the catalog's are estimates.", "up"],
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
  ];

  // a chapter per workload in the grid's pop-up: the same names, in the same order (decode, then prefill), taken from
  // its list so the two cannot drift apart. A workload without a chapter written for it has none
  // each chapter's animation (scenes.js), fed the worked example's numbers so the two always agree
  const sceneData = (id) => {
    const hw = Pie.store.index.hardware[EXAMPLE.hardware];
    const machine = hw?.name || EXAMPLE.hardware;
    const decode = ceilingOf("decode");
    if (id === "decode" || id === "speculation") {
      if (!decode) return null;
      const p = decode.parts;
      const read = p.readS;
      const compute = p.mathS;
      // speculation: the drafter's k passes first, then one verify pass of k + 1 tokens, as the worked example counts them
      const draft = SPEC.k * Math.max((SPEC.drafter * p.bytes) / p.bw, (2 * SPEC.drafter * 1e9) / (p.tflops * 1e12));
      const computeK = (p.flopsPerToken * (SPEC.k + 1)) / (p.tflops * 1e12);
      return { machine, weightsGB: p.weightGB.toFixed(2), bw: p.bw, read, compute, tps: decode.tps, k: SPEC.k, a: SPEC.a, drafter: SPEC.drafter, draft, computeK, kept: (1 - SPEC.a ** (SPEC.k + 1)) / (1 - SPEC.a) };
    }
    if (id === "batching") {
      const bound = Pie.platform?.batchedBound?.(EXAMPLE.hardware, EXAMPLE.model);
      const w = Pie.store.index.workloads?.throughput;
      if (!bound || !w || !decode) return null;
      return { machine, weightsGB: decode.parts.weightGB.toFixed(2), batch: w.concurrency, read: w.concurrency / bound.bandwidth, compute: w.concurrency / bound.compute, tps: bound.tps, bound: bound.bound };
    }
    if (id === "prefill") {
      const c = ceilingOf("prefill");
      if (!c) return null;
      const p = c.parts;
      return { machine, weightsGB: p.weightGB.toFixed(2), tokens: p.tokens, read: p.readS, compute: p.mathS, tps: c.tps };
    }
    return null;
  };
  let stopAnimation = () => {};

  const CHAPTERS = (Pie.platform?.metrics() || []).map((m) => {
    const text = CONTENT.find((t) => t.id === m.id);
    return text && { ...text, title: m.label };
  }).filter(Boolean);

  // every measured result against its limit: if one ran faster than its limit, a formula or an assumption is wrong
  const checkOf = (chapter, release) => {
    const spec = chapter.check;
    if (!spec || !release) return null;
    const rows = (Pie.store.snapshot(release) || []).filter((r) => r.workload === spec.workload && r[spec.key] && Pie.store.isMeasured(r));
    const shares = rows.map((r) => {
      const limit = spec.batched ? Pie.platform?.batchedBound?.(r.hardware, r.model, r.scheme)?.tps : Pie.ceiling?.(r, spec.metric)?.tps;
      return limit ? { r, share: r[spec.key] / limit } : null;
    }).filter(Boolean);
    if (!shares.length) return null;
    const names = Pie.store.names;
    // the machine with its memory, so two machines of one chip are told apart
    const machine = (id) => { const h = Pie.store.index.hardware[id]; return h ? `${h.name} ${h.memory_gib} GB` : id; };
    const label = (s) => `${names.engine(s.r.engine)}, ${names.model(s.r.model)} on ${machine(s.r.hardware)}`;
    const sorted = shares.map((s) => s.share).sort((x, y) => x - y);
    const top = shares.reduce((x, y) => (y.share > x.share ? y : x));
    return {
      n: shares.length,
      median: Math.round(sorted[Math.floor(sorted.length / 2)] * 100),
      top: Math.round(top.share * 100),
      topLabel: label(top),
      over: shares.filter((s) => s.share > 1).sort((x, y) => y.share - x.share).map((s) => ({ label: label(s), share: Math.round(s.share * 100) })),
    };
  };

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
  let release = null;
  let state = null;

  const page = () => {
    const i = CHAPTERS.findIndex((c) => c.id === current);
    const c = CHAPTERS[i];

    // the chapter's references, numbered in the order the page first cites them
    const order = [];
    const cite = (key) => {
      if (!order.includes(key)) order.push(key);
      return `<button type="button" class="cite" data-ref="${key}" title="${esc(REFS[key].title)}">[${order.indexOf(key) + 1}]</button>`;
    };
    const prose = (text) => esc(text).replace(/\s?\{(\w+)\}/g, (_, key) => (REFS[key] ? cite(key) : ""));
    const OPS = /^([×÷+−(),]|max\(|min\()$/;
    const term = (t) => (OPS.test(t) ? `<span class="eqn-op">${esc(t)}</span>` : `<span>${esc(t).replace(/\^\((.+)\)$/, "<sup>$1</sup>")}</span>`);

    // the formula and the worked example in one box: each equation ends in its value for the example
    const example = c.example();
    const equations = c.equations.map((e, n) => `
      <div class="eqn${n === c.equations.length - 1 ? " is-total" : ""}">
        <span class="eqn-result">${esc(e.result)}</span>
        <span class="eqn-sign">=</span>
        <span class="eqn-terms">${e.terms.slice(0, -1).map(term).join(" ")} <span class="eqn-tail">${term(e.terms[e.terms.length - 1])}<span class="eqn-cites">${e.cites.map(cite).join("")}</span></span></span>
        <span class="eqn-value">${example ? esc(example.values[n]) : ""}</span>
      </div>`).join("");
    const inputs = example ? `
      <div class="inputs">${example.inputs.map(([label, value, source]) => `
        <div class="input"><span class="input-label">${esc(label)}</span><span class="input-value">${esc(value)}</span><span class="input-source">${esc(source)}</span></div>`).join("")}
      </div>` : "";

    const why = c.why.map((p) => `<p>${prose(p)}</p>`).join("");
    const assumptions = c.assumptions.map(([text, effect]) => `
      <li><span>${esc(text)}</span><span class="effect is-${effect || "choice"}">${EFFECT[effect || "choice"]}</span></li>`).join("");

    const check = checkOf(c, release);
    const checkHtml = !c.check
      ? `<p class="book-plain">${esc(c.noCheck)}</p>`
      : !check
        ? `<p class="book-plain">No measured results in this release.</p>`
        : `<div class="check-figures">
            <div><span class="check-value">${check.n}</span><span class="check-label">Measured results</span></div>
            <div><span class="check-value">${check.median}%</span><span class="check-label">Median share</span></div>
            <div><span class="check-value">${check.top}%</span><span class="check-label">Highest share</span></div>
            <div class="${check.over.length ? "is-fail" : "is-pass"}"><span class="check-value">${check.over.length}</span><span class="check-label">Above the limit</span></div>
          </div>
          ${check.over.length
            ? `<p class="book-plain">${check.over.length} ${check.over.length === 1 ? "result runs" : "results run"} faster than the limit allows. A result cannot beat a true limit, so for ${check.over.length === 1 ? "it" : "these"} either an input above is wrong or the measurement is.</p>
              <div class="example-rows check-over">${check.over.map((o) => `<div class="example-row"><span>${esc(o.label)}</span><span></span><span class="example-value">${o.share}%</span></div>`).join("")}</div>
              ${c.open ? `<div class="open-question"><h3>Under investigation</h3><p>${esc(c.open)}</p></div>` : ""}`
            : `<p class="book-plain">Every result in this release, against its own limit. None runs faster than the limit allows; the closest is ${esc(check.topLabel)}, at ${check.top}%.</p>`}`;

    const machine = `${Pie.store.names.model(EXAMPLE.model)} on ${Pie.store.index.hardware[EXAMPLE.hardware]?.name || EXAMPLE.hardware}`;
    // the sections first, so the citations number the references in reading order
    const body = `
      <h1 class="book-title">${esc(c.title)}</h1>
      <p class="book-lede">${esc(c.lede)}</p>
      ${Pie.scenes?.html(c.id, sceneData(c.id)) || ""}
      <section class="book-section">
        <h2>How it is calculated</h2>
        <p class="book-plain">Each line in words, with its value for ${esc(machine)} at 4-bit.</p>
        <div class="eqns">${equations}</div>
        ${c.symbols ? `<p class="book-plain">${esc(c.symbols)}</p>` : ""}
        ${inputs}
        ${c.figure ? c.figure() : ""}
      </section>
      <section class="book-section">
        <h2>Checked against the measurements</h2>
        ${checkHtml}
      </section>
      <section class="book-section">
        <h2>Why it holds</h2>
        <div class="book-prose">${why}</div>
      </section>
      <section class="book-section">
        <h2>Assumptions</h2>
        <p class="book-plain">Every simplification, and which way it moves the limit. Those that raise it keep the limit a ceiling no engine can pass.</p>
        <ul class="assumptions">${assumptions}</ul>
      </section>
      <section class="book-section">
        <h2>Agentic workloads</h2>
        <div class="book-prose">
          <p>Agents hold longer contexts and run many at once, so they need more memory and more I/O. They branch, call tools and wait, which makes the load hard to predict and hard to schedule, and widens the gap to the limit. Every idle moment of the hardware shows up in the cost.</p>
          <p>Pie is built for these patterns. <a href="https://github.com/pie-project/pie" target="_blank" rel="noopener">Profile your multi-agent workloads with Pie.</a></p>
        </div>
      </section>`;

    // the bar: the grid's workload pop-up and its Configuration, the same buttons in the same place
    const bar = `
      <div class="platform-bar limit-bar methods-bar">
        <span class="filter platform-setup">
          <button class="filter-button" id="methods-metric" type="button" aria-haspopup="menu" aria-label="${esc(`Workload: ${c.title}`)}">${esc(c.title)}<span class="setup-chevron" aria-hidden="true"><svg viewBox="0 0 10 10"><path d="M2.75 4 5 6.25 7.25 4"/></svg></span></button>
        </span>
        <button type="button" class="plain-button rules-button" data-rules aria-expanded="false"><svg viewBox="0 0 16 16" aria-hidden="true"><circle cx="8" cy="8" r="6.5"/><path d="M8 7.2v3.6M8 5.2v.1"/></svg>Configuration</button>
      </div>`;

    return `${bar}
      <article class="book-page">
        ${body}
        <section class="book-section">
          <h2>References</h2>
          <ol class="refs">${order.map((key) => {
            const r = REFS[key];
            return `<li id="ref-${key}"><span>${esc(r.authors.replace(/\.$/, ""))}.</span> <a href="${r.url}" target="_blank" rel="noopener">${esc(r.title)}</a>. <span class="ref-venue">${esc(r.venue)}, ${r.year}.</span></li>`;
          }).join("")}</ol>
        </section>
      </article>`;
  };


  element.addEventListener("click", (event) => {
    // a citation scrolls to its reference and marks it for a moment, as a footnote link does
    const ref = event.target.closest("[data-ref]");
    if (ref) {
      const target = element.querySelector(`#ref-${ref.dataset.ref}`);
      if (!target) return;
      target.scrollIntoView({ behavior: "smooth", block: "center" });
      target.classList.remove("is-flash");
      void target.offsetWidth;
      target.classList.add("is-flash");
      return;
    }
    // the workload pop-up: the grid's own menu, so a pick changes both pages
    const picker = event.target.closest("#methods-metric");
    if (picker && state) {
      event.stopPropagation();
      Pie.popover.open(picker, Pie.popover.METRIC, state);
      return;
    }
  });

  Pie.methods = {
    render(viewState) {
      state = viewState;
      element.hidden = state.table !== "methods";
      // the grid's workload, or the first chapter when that workload has none written yet
      current = CHAPTERS.some((c) => c.id === state.platform.mode) ? state.platform.mode : CHAPTERS[0].id;
      const key = `${current}@${state.release}`;
      if (!element.hidden && element.dataset.key !== key) {
        release = state.release;
        stopAnimation();
        element.innerHTML = page();
        const scene = element.querySelector("[data-scene]");
        stopAnimation = scene ? Pie.scenes.start(scene, sceneData(current)) : () => {};
        element.dataset.key = key;
        element.scrollTop = 0;
      }
    },
  };
})();
