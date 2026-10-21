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
        eq("Interconnect time", ["2", "×", "Layers", "×", "(", "Link latency", "+", "Activations exchanged", "÷", "Link bandwidth", ")"], ["megatron"]),
        eq("Limit", ["1 token", "÷", "max(", "Memory time", ",", "Math time", ",", "Interconnect time", ")"], ["roofline"]),
      ],
      why: [
        "Decode reads every active weight once per token, so memory bandwidth, not arithmetic, sets the limit {roofline} {pope}.",
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
      id: "spec",  // the setup pop-up's id for Spec Decode, so picking it opens this chapter
      lede: "A small drafter proposes the next few tokens and the model checks all of them in one pass, keeping each one it agrees with. More drafts cost more and add less, so the limit is the draft width that gives the most tokens per second.",
      equations: [
        eq("Tokens per step", ["(", "1", "−", "a^(k+1)", ")", "÷", "(", "1", "−", "a", ")"], ["leviathan"]),
        eq("Verify time", ["max(", "Memory time", ",", "(", "k", "+", "1", ")", "×", "Math time", ")"], ["roofline"]),
        eq("Draft time", ["Drafter weights read", "÷", "Memory bandwidth"], ["roofline"]),
        eq("Step time", ["Verify time", "+", "Draft time"], ["leviathan", "chen"]),
        eq("Limit", ["max(", "Raw Decode", ",", "max over k(", "Tokens per step", "÷", "Step time", ")", ")"], ["leviathan"]),
      ],
      symbols: "k is the number of drafted tokens per step and a the chance that each is accepted. Memory time and Math time are Raw Decode's. A block drafter proposes all k drafts in one pass, so its Draft time is one read of its weights; a drafter that proposes one token at a time pays k of them. The limit tries every k from 1 to 16 and keeps the fastest, and falls back to Raw Decode when no k pays.",
      why: [
        "One pass checks k + 1 tokens for one read of the weights, and greedy verification keeps the output unchanged {leviathan} {chen}.",
        "Draft k only counts if every draft before it was accepted, so each extra draft adds a^k tokens: at 70%, four drafts keep 2.8 tokens, eight 3.2 and sixteen 3.3, the most any k can give being 1 ÷ (1 − a).",
        "Decode is memory-bound, so the first extra rows of a verify are nearly free. Once (k + 1) × Math time passes Memory time, every row costs its arithmetic and wider drafts lose. Many requests at once reach that point at a smaller k, which is why engines draft less, or not at all, under load.",
        "a is measured, not given: over a run, a = accepted drafts ÷ (accepted drafts + rejections), counting one rejection for each step that stopped before its last draft. The drafter's authors report it for their benchmarks, but it changes with the prompt, so an engine reads it from its own steps.",
      ],
      assumptions: [
        ["Each draft is accepted independently with the same chance a. Real acceptance falls along the draft.", "up"],
        ["The drafter proposes its whole block in one pass, as DFlash does. A drafter that proposes one token at a time pays k passes.", "up"],
        ["The drafter has 0.5 B parameters and 70% acceptance, the Limit page's defaults. Neither is measured per run.", null],
        ["Everything Raw Decode assumes.", "up"],
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
            ["Verify time", ms(best.verify), `Raw Decode with ${best.k + 1} tokens`],
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
        eq("Bandwidth bound", ["Requests", "×", "Memory bandwidth", "÷", "(", "Weights read", "+", "Caches read", ")"], ["roofline", "pope"]),
        eq("Compute bound", ["Peak FLOPS", "÷", "Arithmetic per output token"], ["kaplan"]),
        eq("Interconnect bound", ["Requests", "÷", "Interconnect time"], ["megatron"]),
        eq("Limit", ["min(", "Bandwidth bound", ",", "Compute bound", ",", "Interconnect bound", ")"], ["roofline"]),
      ],
      symbols: "The arithmetic per output token is 2 × (active body + output head), plus each request's prompt, 2 × active body per prompt token, spread over its answer: the prompt uses the same FLOPS but does not count as output.",
      why: [
        "A batch reads the weights once for all its requests, so speed grows with the batch until it meets the compute roof {pope} {roofline}.",
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
        eq("Interconnect time", ["2", "×", "Layers", "×", "(", "Link latency", "+", "Activations exchanged", "÷", "Link bandwidth", ")"], ["megatron"]),
        eq("Limit", ["Prompt tokens", "÷", "max(", "Memory time", ",", "Math time", ",", "Interconnect time", ")"], ["roofline"]),
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

  const page = () => {
    const i = CHAPTERS.findIndex((c) => c.id === current);
    const c = CHAPTERS[i];

    // a citation is the work's first author and year, a link straight to the paper
    const cite = (key) => {
      const r = REFS[key];
      const author = r.authors.split(",")[0].replace(/ et al\.?$/, "").split(" ").pop();
      return `<a class="cite" href="${r.url}" target="_blank" rel="noopener" title="${esc(`${r.authors} ${r.title}. ${r.venue}, ${r.year}`)}">${esc(author)} ${r.year}</a>`;
    };
    const prose = (text) => esc(text).replace(/\s?\{(\w+)\}/g, (_, key) => (REFS[key] ? cite(key) : ""));
    const OPS = /^([×÷+−(),]|max\(|min\(|max over k\()$/;
    const term = (t) => (OPS.test(t) ? `<span class="eqn-op">${esc(t)}</span>` : `<span>${esc(t).replace(/\^\((.+)\)$/, "<sup>$1</sup>")}</span>`);

    // the page as apple.com sets a feature: the workload's name on its banner, the formulas
    // as rows, and the check as four figures
    const kindOf = (e, n) => (n === c.equations.length - 1 ? "limit" : /memory|read|draft/i.test(e.result) ? "read" : /math|verify/i.test(e.result) ? "math" : "other");
    // a formula breaks only before an operator, as maths is typeset: each operator travels with
    // the term after it, and the citations with the last one
    const units = (e) => {
      // a function of several arguments (max, min) after the last operator: on a phone its arguments stack in a
      // column that starts after its bracket, one a line; on a wider screen they read inline
      const f = e.terms.findIndex((t) => /^[a-z]+\($/.test(t));
      if (f > 1 && e.terms.at(-1) === ")" && e.terms.includes(",")) {
        const args = [[]];
        e.terms.slice(f + 1, -1).forEach((t) => (t === "," ? args.push([]) : args.at(-1).push(t)));
        const head = e.terms.slice(0, f - 1).map((t, n) => (n ? " " : "") + term(t)).join("");
        const cites = asTable ? "" : `<span class="eqn-cites">${e.cites.map(cite).join("")}</span>`;
        const col = args.map((a, n) => `<span class="lim-arg">${a.map(term).join(" ")}${n < args.length - 1 ? term(",") : `${term(")")}${cites}`}</span>`).join(" ");
        return `<span class="lim-unit">${head}</span> <br class="lim-turn"><span class="lim-unit">${term(e.terms[f - 1])} ${term(e.terms[f])}</span><span class="lim-args">${col}</span>`;
      }
      const out = [];
      // on a phone every formula turns its line at the same place: before its last operator outside brackets
      let depth = 0, last = 0;
      e.terms.forEach((t, n) => {
        const piece = (n === 0 || /^[),]$/.test(t) || /\($/.test(e.terms[n - 1]) ? "" : " ") + term(t);
        if (/\($/.test(t)) depth++;
        else if (t === ")") depth--;
        if (n === 0 || /^[×÷+−]$/.test(t)) {
          if (depth === 0 && n > 0) last = out.length;
          out.push(piece.trimStart());
        } else out[out.length - 1] += piece;
      });
      if (!asTable) out[out.length - 1] += `<span class="eqn-cites">${e.cites.map(cite).join("")}</span>`;
      // when that last operator opens a bracket, its + and ÷ inside turn too, so the bracket reads one term a line
      const turns = new Set(last ? [last] : []);
      if (last && /<span class="eqn-op">\(<\/span>/.test(out[last]))
        out.forEach((u, n) => { if (n > last && /^<span class="eqn-op">[+÷]<\/span>/.test(u)) turns.add(n); });
      return out.map((u, n) => `${turns.has(n) ? '<br class="lim-turn">' : ""}<span class="lim-unit">${u}</span>`).join(" ");
    };
    // the formulas as rows of the site's data table: the term, the formula, and the works it rests on in its own column
    const asTable = true;
    const formulaRows = c.equations.map((e) => `
      <tr><td class="lim-term">${esc(e.result)}</td><td class="lim-formula">${units(e)}</td></tr>`).join("");

    // the bar: the grid's workload pop-up and its Configuration, the same buttons in the same place
    const bar = `
      <div class="platform-bar limit-bar methods-bar">
        <span class="filter platform-setup">
          <button class="filter-button" id="methods-metric" type="button" aria-haspopup="menu" aria-label="${esc(`Workload: ${c.title}`)}">${esc(c.title)}<svg class="popup-chevron" viewBox="0 0 10 14" aria-hidden="true"><path d="M2 5l3-3 3 3M2 9l3 3 3-3"/></svg></button>
        </span>
        ${c.id === "spec" ? `
        ${Pie.specField()}` : ""}
        <button type="button" class="plain-button rules-button" data-rules aria-expanded="false" aria-label="Test Conditions"><svg viewBox="0 0 16 16" aria-hidden="true"><circle cx="8" cy="8" r="6.5"/><path d="M8 7.2v3.6M8 5.2v.1"/></svg><span class="rules-label">Test Conditions</span></button>
      </div>`;

    // the chapter as the site's other pages: the formulas as a data table under the bar, each citing its works by
    // name, linked
    return `${bar}
      <div class="lim-tables">
        <table class="data-table lim-table">
          <thead><tr><th>Term</th><th>Formula</th><th class="lim-fill"></th></tr></thead>
          <tbody>${formulaRows.replace(/<\/tr>/g, '<td class="lim-fill"></td></tr>')}</tbody>
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
    // the workload pop-up: the grid's own menu, so a pick changes both pages
    const picker = event.target.closest("#methods-metric");
    if (picker && state) {
      event.stopPropagation();
      Pie.popover.open(picker, Pie.popover.METRIC, state);
      return;
    }
  });

  // the acceptance field: the input follows the shared value when it changes elsewhere
  Pie.bindSpecField(element, () => {
    const input = element.querySelector("[data-alpha]");
    if (input && document.activeElement !== input) input.value = Pie.specAlpha;
  });

  Pie.methods = {
    render(viewState) {
      state = viewState;
      element.hidden = state.table !== "methods";
      // the grid's workload, or the first chapter when that workload has none written yet
      current = CHAPTERS.some((c) => c.id === state.platform.mode) ? state.platform.mode : CHAPTERS[0].id;
      const key = `${current}@${state.release}`;
      if (!element.hidden && element.dataset.key !== key) {
        element.innerHTML = page();
        element.dataset.key = key;
        element.scrollTop = 0;
      }
    },
  };
})();
