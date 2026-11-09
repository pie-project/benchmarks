window.Pie = window.Pie || {};

// Methodology: how the benchmark is run, written as prose, a chapter at a time, with the overview's outline down
// the left; a chapter added to CHAPTERS joins the outline and the previous and next links.
(() => {
  const element = document.getElementById("approach");

  const REPO = "https://github.com/pie-project/benchmarks";  // the open repository the Welcome chapter points to
  // [outline group, [id, title, colour, summary, body]]
  // the Limits chapters: one a setup, in the order the grid's setup menu lists them
  const LIMITS = [
    ["decode", "Single Decode", "#FF3B30", "One request writing its answer: the ceiling each engine's Single Decode is measured against."],
    ["prefill", "Single Prefill", "#FF9500", "One request reading its prompt: the ceiling each engine's Single Prefill is measured against."],
    ["batching", "Batched Decode", "#34C759", "Many requests writing at once: the ceiling each engine's Batched Decode is measured against."],
    ["pbatch", "Batched Prefill", "#007AFF", "Many prompts read at once: the ceiling each engine's Batched Prefill is measured against."],
  ];
  const CHAPTERS = [
    ["", [  // Welcome on its own at the top, under no heading, as the sidebar sets Overview
      ["welcome", "Welcome", "#0A84FF", "Open benchmarks for every inference engine.", () => welcome()],
      ["trust", "Why Trust Us", "#A2845E", "The safeguards behind every number.", () => trust()],
    ]],
    ["Setup", [
      ["setup", "CI Setup", "#8E8E93", "The CI setup behind every run.", () => setup()],
      ["workloads", "Workloads", "#30B0C7", "What each setup measures.", () => workloadsPage()],
      ["fairness", "Engine Settings", "#34C759", "What every engine shares, and what each tunes.", () => fairness()],
      ["measurement", "Measurement", "#FF9500", "Rounds, warmup, noise and how a cell's number is chosen.", () => measurement()],
      ["install", "Install Size", "#30B0C7", "What an engine's install size counts.", () => installPage()],
    ]],
    ["Models", [
      ["slices", "Model Slices", "#5E5CE6", "A fair comparison on one device, and a baseline for modeling scale.", () => slices()],
      // the former Memory page, its formulas drawn by methods.js
      ["fit", "Memory Fit", "#AF52DE", "How we decide whether a model fits a machine.", () => `
        <p>A model runs only where its weights, KV cache and engine buffers fit the GPU's memory. Where it does not, the grid shows a crossed mark <svg class="platform-nofit" viewBox="0 0 16 16" aria-hidden="true"><rect x="2.5" y="2.5" width="11" height="11" rx="2.5"/><path d="M4 12 12 4"/></svg>.</p>
        ${tables("fit")}`],
    ]],
    ["Limits", [
      // the former Roofline page, one chapter a setup: each draws the limit of its own workload, no setup to pick
      ...LIMITS.map(([setup, title, colour, summary]) => [`limit-${setup}`, title, colour, summary, () => `
        <p>These limits follow the roofline model (Williams et al., 2009): a step can run no faster than its memory traffic at peak bandwidth or its FLOPs at peak compute, whichever takes longer. Kernel Efficiency is an engine's measured throughput as a percentage of this limit.</p>
        ${tables(`limit:${setup}`)}`]),
    ]],
    ["Quality", [
      ["parity", "Parity Checks", "#007AFF", "How we confirm every engine computes the same model.", () => parity()],
      ["accuracy", "Accuracy", "#FFCC00", "Benchmark scores on the same weights and machine.", () => accuracy()],
    ]],
    ["Contribute", [
      ["add-engine", "Add an Engine", "#FF2D55", "How a new engine joins the benchmark.", () => addEngine()],
      ["run-yourself", "Run It Yourself", "#00C7BE", "The same harness and rules, on hardware you rent.", () => runYourself()],
    ]],
  ];

  // Welcome as a landing page, as a vendor's docs open: the live counts, the path a number takes, what is measured, why
  // to trust it and how to take part, each linking on to its chapter or page
  const welcome = () => {
    const n = (v) => Number(v || 0).toLocaleString("en-US");
    const rows = (t) => (Pie.store.rows(t) || []).length;
    const chevron = '<svg class="welcome-flow-arrow" viewBox="0 0 16 16" aria-hidden="true"><path d="M6 3.5 10.5 8 6 12.5"/></svg>';
    // the path every number takes; the limit check in the grid's CI Error red, the step that catches a wrong one
    const STEP_COLOURS = ["#007AFF", "#5E5CE6", "#30B0C7", "var(--color-negative)", "#34C759"];  // each step its own system colour
    const flow = [["Recipe", "Engine settings, public in the repo"], ["CI run", "Dedicated machine, nothing else running"],
      ["Repeated", "Until the noise is small"], ["Limit check", "Above the limit is a CI error", "is-check"], ["Published", "Here and on GitHub, with raw data"]];
    const workloads = [["decode", "Single Decode", "One request writing its answer"], ["prefill", "Single Prefill", "One request reading its prompt"],
      ["batching", "Batched Decode", "Many requests writing at once"], ["pbatch", "Batched Prefill", "Many prompts read at once"], ["spec", "Speculative Decode", "A draft model guessing ahead"]];
    return `
      <p class="welcome-lead">Every engine is capped by the same hardware limits, so most run within a few percent of each other. We measure the gap and show where it comes from.</p>
      ${flowCarousel(flow.map(([t, d, cls], i) => `<li class="${cls || ""}" style="--step: ${STEP_COLOURS[i]}"><i>${i + 1}</i><b>${t}</b><span>${d}</span></li>`).join(""), "<h3>How a number is made</h3>")}
      <h3>What we measure</h3>
      <ul class="welcome-list">${workloads.map(([id, t, d]) => `<li><button type="button" data-chapter-go="workloads">${Pie.platform.degree(id)}<b>${t}</b><span>${d}</span></button></li>`).join("")}</ul>`;
  };

  // the chapters' own parts, as Welcome and Why Trust Us draw theirs: a lead line, rows marked by a coloured square,
  // and numbered steps in their colours
  const lead = (text) => `<p class="welcome-lead">${text}</p>`;
  const facts = (rows) => `<ul class="welcome-list is-trust">${rows.map(([colour, t, d]) =>
    `<li><div class="welcome-row"><span class="trust-tile" style="--tile: ${colour}" aria-hidden="true"></span><b>${t}</b><span>${d}</span></div></li>`).join("")}</ul>`;
  // a run of numbered steps as a carousel: each step keeps its width and the row slides sideways, with the Overview's
  // paddles above it (shown only when the steps do not fit) and the far edge fading while more steps follow
  const FLOW_PADDLES = `<span class="platform-compare board-view board-carousel-nav flow-nav" role="group" aria-label="Steps" hidden><button type="button" class="plain-button" data-flow="-1" aria-label="Previous steps" title="Previous"><svg viewBox="0 0 16 16" aria-hidden="true"><path d="M10 3.5 5.5 8l4.5 4.5"/></svg></button><button type="button" class="plain-button" data-flow="1" aria-label="Next steps" title="Next"><svg viewBox="0 0 16 16" aria-hidden="true"><path d="M6 3.5 10.5 8 6 12.5"/></svg></button></span>`;
  // its title (a heading or the chapter's lead) on the left of one line, the paddles on its right
  const flowCarousel = (items, head = "") => `<div class="flow-carousel${head.startsWith("<h3") ? " has-title" : ""}"><div class="flow-head">${head}${FLOW_PADDLES}</div><ol class="welcome-flow">${items}</ol></div>`;
  const steps = (rows, head = "") => flowCarousel(rows.map(([colour, t, d, cls], i) =>
    `<li class="${cls || ""}" style="--step: ${colour}"><i>${i + 1}</i><b>${t}</b><span>${d}</span></li>`).join(""), head);
  // each carousel's paddles: shown only when its steps overflow, each greyed at its end; the fade off at the last step
  const flowPaddles = () => element.querySelectorAll(".flow-carousel").forEach((box) => {
    const row = box.querySelector(".welcome-flow"), nav = box.querySelector(".flow-nav");
    if (!row || !nav) return;
    const over = row.scrollWidth - row.clientWidth > 2;
    nav.hidden = !over;
    const [back, on] = nav.querySelectorAll("[data-flow]");
    back.disabled = row.scrollLeft <= 2;
    on.disabled = row.scrollLeft >= row.scrollWidth - row.clientWidth - 2;
    row.classList.toggle("is-end", !over || on.disabled);
  });

  // each platform's CI workflow, a row each that opens its file on GitHub
  const workflow = (file) => `${REPO}/blob/main/.github/workflows/${file}`;
  const flows = (rows) => `<ul class="welcome-list is-trust is-flows">${rows.map(([colour, t, file, d]) =>
    `<li><a href="${workflow(file)}" target="_blank" rel="noopener"><span class="trust-tile" style="--tile: ${colour}" aria-hidden="true"></span><b>${t}</b><code>${file}</code><span>${d}</span></a></li>`).join("")}</ul>`;
  // the engines we fork: each fork's branch, a row that opens it on GitHub
  const forks = (rows) => `<ul class="welcome-list is-trust is-flows">${rows.map(([colour, t, repo, branch, d]) =>
    `<li><a href="https://github.com/${repo}/tree/${branch}" target="_blank" rel="noopener"><span class="trust-tile" style="--tile: ${colour}" aria-hidden="true"></span><b>${t}</b><code>${branch}</code><span>${d}</span></a></li>`).join("")}</ul>`;
  const setup = () => `
      <h3>Workflows</h3>
      ${flows([["#636366", "Apple Silicon", "pie-eval.yml", "The resident Macs, one job per Mac"],
        ["#76b900", "NVIDIA GPU", "tier.yml", "RunPod pods launched as CI runners, torn down after"],
        ["#ED1C24", "AMD GPU", "tier.yml", "MI300X pods, the same flow"],
        ["#4285F4", "Google TPU", "tpu.yml", "A Cloud TPU VM per run, deleted after"],
        ["#8E8E93", "Browser", "pod-import.yml", "Chrome on rented pods, its results imported"],
        ["#FFCC00", "Quality", "quality.yml", "MATH-500 and first-token checks"]])}
      <h3>Engine forks</h3>
      <p>Each run uses the latest release. A fix we need lives in a public fork.</p>
      ${forks([["#E5484D", "vLLM", "pie-project/vllm", "pie-evals/v0.32.0", "Fork of vLLM 0.32.0"],
        ["#34C759", "SGLang", "pie-project/sglang", "pie-evals/v0.5.22", "Fork of SGLang 0.5.22"]])}
      ${steps([["#007AFF", "Lock", "One job per machine"], ["#5E5CE6", "Clean", "Stray apps and engines closed"],
        ["#30B0C7", "Quiet", "Waits for an idle GPU"], ["#34C759", "Pinned", "Engine versions recorded"]], "<h3>Before every run</h3>")}`;

  const workloadsPage = () => {
    const rows = [["decode", "Single Decode", "512 tokens in, 256 out, one request: output tokens per second"],
      ["prefill", "Single Prefill", "The same request, read as prompt tokens per second"],
      ["batching", "Batched Decode", "256 requests at once, fewer on a Mac: total output tokens per second"],
      ["pbatch", "Batched Prefill", "256 prompts of 512 tokens at once, one token out each"],
      ["spec", "Speculative Decode", "Single Decode with each engine's own drafter, verified greedily"]];
    return `
      ${lead("Five setups, each a single question about an engine.")}
      <ul class="welcome-list">${rows.map(([id, t, d]) => `<li><div class="welcome-row is-icon">${Pie.platform.degree(id)}<b>${t}</b><span>${d}</span></div></li>`).join("")}</ul>
      ${steps([["#30B0C7", "Seeded", "Same token ids on every engine"], ["#64D2FF", "Cold", "No prefix-cache hits"],
        ["#007AFF", "Fixed length", "Same output length on every engine"]], "<h3>Every workload</h3>")}`;
  };

  const fairness = () => `
      ${facts([["#34C759", "Same weights", "One checkpoint and precision class for every engine"],
        ["#30B0C7", "Same prompts", "Identical token ids, checked after every run"],
        ["#5E5CE6", "Same slice", "Where a model is cut to fit, every engine runs the same cut"],
        ["#007AFF", "Same decoding", "Greedy, temperature 0, thinking off"],
        ["#FFCC00", "Same KV cache", "bf16 on every engine"],
        ["#FF2D55", "Like-for-like drafters", "The same draft model across engines, verified losslessly"],
        ["#64D2FF", "One feature at a time", "Each measured alone, against the plain run"],
        ["#FF9500", "Own best settings", "Each engine tuned for its highest throughput, the recipe public"],
        ["#FF3B30", "Compiled at load", "Pie on TPU compiles its batch shapes at load, as vLLM-TPU and SGLang-JAX do"],
        ["#AF52DE", "Latest releases", "The newest release of each engine at run time, every run dated and tagged"]])}`;

  const measurement = () => `
      ${lead("A cell's number is the median of repeated rounds, taken after warmup.")}
      ${steps([["#8E8E93", "Warmup", "2–3 runs, not counted"], ["#007AFF", "Rounds", "3 single, 2 batched"],
        ["#FF9500", "Noise", "Over 2% spread (5% batched) adds rounds, up to 5"], ["#34C759", "Median", "The middle round counts"],
        ["var(--color-negative)", "Limit check", "Above the limit is a CI error", "is-check"]], "<h3>How a cell is measured</h3>")}
      <p>Rounds that still disagree are marked noisy. Macs cool down between rounds.</p>`;

  // Install Size: what the Overview's cards count, then every figure with how it was counted and where it came from
  // (matrix/install.yaml, exported as the `install` table)
  const installPage = () => {
    const esc = (text) => Pie.format.escape(text);
    const rows = Pie.store.tables.install || [];
    const size = (b) => (b >= 1e9 ? `${(b / 1e9).toFixed(2)} GB` : `${(b / 1e6).toFixed(1)} MB`);
    const on = [["mac", "Apple"], ["nvidia", "NVIDIA"], ["amd", "AMD"], ["tpu", "TPU"], ["web", "Browser"]].filter(([p]) => !Pie.hiddenPlatforms.has(p) && rows.some((r) => r.platform === p));
    const when = rows[0]?.measured ? new Date(`${rows[0].measured}T12:00`).toLocaleDateString("en-US", { day: "numeric", month: "short", year: "numeric" }) : "";
    // one line an engine (logo, name, version, size); what it counts and how it was measured in its hover card
    const card = (r) => `<div class="tip-title">${esc(Pie.store.names.engine(r.engine))} ${esc(r.version)}</div><div class="tip-sub">${size(r.bytes)} on disk</div><div class="tip-foot">${esc(r.method)}</div><div class="tip-foot install-tip-source">${esc(r.source)}</div>`;
    const entry = (r) => `<li data-tip-html="${esc(card(r))}"><div class="install-head">${Pie.engines.logo?.(r.engine) || ""}<b>${esc(Pie.store.names.engine(r.engine))}</b><span>${esc(r.version)}</span><b class="install-bytes">${size(r.bytes)}</b></div></li>`;
    return `
      ${lead("The disk an engine needs before any model: its binaries and every library it installs.")}
      ${facts([["#3776AB", "Python engines", "The venv the harness builds for it, without the base Python it links to"],
        ["#636366", "Native engines", "The release or build files it runs, with the system libraries it loads in place of a venv's"],
        ["#8E8E93", "Browser engines", "The JS and wasm the page downloads"],
        ["#FF9500", "Left out", "Any model, the GPU driver, and bytecode Python writes on its first run"],
        ["#34C759", "Measured", `Bytes of regular files, 1 GB being 10⁹ bytes${when ? `, on ${when}` : ""}`]]).replace("is-trust", "is-trust is-install")}
      ${on.map(([p, title]) => `<h3>${title}</h3><ul class="install-list">${rows.filter((r) => r.platform === p).sort((a, b) => a.bytes - b.bytes).map(entry).join("")}</ul>`).join("")}`;
  };

  const parity = () => `
      ${lead("A fast engine only counts if it computes the same model.")}
      ${steps([["#007AFF", "Same prompts", "Sent to both engines"], ["#5E5CE6", "One token", "One from each engine"],
        ["#30B0C7", "Compare", "KL divergence between them"], ["#34C759", "Pass", "KL under 0.15"]], "<h3>How a check runs</h3>")}
      <p>Two correct engines differ only in kernel order and bf16 rounding, which moves the distribution by about 0.001. A real bug, such as a wrong layer, rotary setting or chat template, lands far above 0.15, so the line sits two orders of magnitude above the noise. The first token comes from one pass through every layer, so it tests the whole model, even on a slice whose answers no longer make sense.</p>
      <p>Each engine reports its 20 most likely tokens. The KL runs over the reference's 20 and the rest of the vocabulary. A token the reference lists that Pie's 20 lack is given at most Pie's 20th probability, since Pie ranks it lower. Pie's list then fails the check if it holds none of the reference's likely tokens. Without that bound, such a pair would put all of both distributions in the rest and score zero. One Gemma-4-31B slice did exactly that: the reference put 0.23 on each of its top three tokens and Pie's 20 held none of them.</p>
      <p>A check can fail only if the reference's first token says something. Some slices leave it nearly flat. With the first 18 of Gemma-4-31B's 60 layers, the reference's 20 likeliest tokens hold 1% of the probability, and no prompt has a token that leads the runner-up by half a nat. Any engine whose output is also flat would pass. Such a cell runs a deeper cut where one fits: Gemma-4-31B sharpens at 30 layers, its top 20 holding 99.8%. Where no deeper cut fits, as on the 24 and 32 GB NVIDIA cards, the cell is marked as unable to be checked on that device instead of shown as a pass. Keeping the first and last layers does not help: feeding layer 5's output to layer 48 drives Gemma's logits into their softcap.</p>
      <p>A few slices are cut so deep that rounding alone moves their first token past the line. When Pie lands past 0.15, the reference engine runs again with only its kernels changed: vLLM in eager mode instead of its CUDA graphs, mlx-lm with its fused attention and normalization kernels swapped for plain ones. If Pie lands within twice the distance the reference moves from itself, the first token cannot tell Pie from rounding, and the slice is checked on its answers instead: both engines score the reference's greedy answers to 40 benchmark questions at every position, under the same 0.15 line. Gemma-4-26B-A4B with 24 of its 128 experts is one such slice. On an RTX 4090 its first token moves 0.44 when vLLM switches to eager mode and 0.35 between vLLM and SGLang, more than the 0.26 between the slice and one with 32 experts. On the answers vLLM moves 0.04 from itself and Pie 0.06, while the 32-expert slice lands at 0.21.</p>`;

  const accuracy = () => `
      ${lead("On a model that fits, Pie and another engine answer the same benchmark on the same weights and machine.")}
      ${facts([["#FFCC00", "Benchmark", "MATH-500, competition math"],
        ["#007AFF", "Decoding", "Greedy, thinking off"],
        ["#8E8E93", "Compared with", "One other engine on the same machine"],
        ["#34C759", "Pass", "Within the run's own noise of the other engine; 5 points where it has none"]])}`;

  // Contribute: the files an engine is added in, each a row that opens it on GitHub (its name in the file column, the
  // whole path in its title); commands as facts whose lines stay on a phone; links out as the trust rows' links
  const repoFiles = (rows) => `<ul class="welcome-list is-trust is-flows">${rows.map(([colour, t, path, name, d]) =>
    `<li><a href="${REPO}/${path.endsWith("/") ? "tree" : "blob"}/main/${path}" target="_blank" rel="noopener" title="${path}"><span class="trust-tile" style="--tile: ${colour}" aria-hidden="true"></span><b>${t}</b><code>${name}</code><span>${d}</span></a></li>`).join("")}</ul>`;
  const commands = (rows) => facts(rows).replace("is-trust", "is-trust is-install");
  const links = (rows) => `<ul class="welcome-list is-trust">${rows.map(([colour, t, href, d]) =>
    `<li><a href="${href}" target="_blank" rel="noopener"><span class="trust-tile" style="--tile: ${colour}" aria-hidden="true"></span><b>${t}</b><span>${d}</span></a></li>`).join("")}</ul>`;

  // Model Slices: its two claims as numbered steps, each then stated in a line, its formula set as the limit chapters
  // set theirs (a named result, its terms as coloured pills), and the facts it rests on; real cuts from matrix/models.yaml
  const mv = (name, colour, sym) => `<span class="m-var" data-name="${name}" title="${sym}" style="--pill: ${colour}">${name}</span>`;
  const mt = (name, colour) => `<span class="m-tag" data-name="${name}" style="--pill: ${colour}"><span class="m-dot"></span>${name}</span>`;
  const mo = (x) => `<span class="m-op">${x}</span>`;
  const mp = (x) => `<span class="m-paren">(</span>${x}<span class="m-paren">)</span>`;
  // the works each formula rests on, cited as the limit chapters cite theirs: the most cited statement of each idea
  const REFS = {
    kaplan: { authors: "J. Kaplan et al.", title: "Scaling Laws for Neural Language Models", venue: "arXiv:2001.08361", year: 2020, url: "https://arxiv.org/abs/2001.08361" },
    pope: { authors: "R. Pope et al.", title: "Efficiently Scaling Transformer Inference", venue: "MLSys 2023, arXiv:2211.05102", year: 2022, url: "https://arxiv.org/abs/2211.05102" },
    valiant: { authors: "L. G. Valiant", title: "A Bridging Model for Parallel Computation", venue: "Communications of the ACM 33(8)", year: 1990, url: "https://doi.org/10.1145/79173.79181" },
  };
  const cite = (key) => { const r = REFS[key]; const author = r.authors.split(",")[0].replace(/ et al\.?$/, "").split(" ").pop(); return `<a class="cite" href="${r.url}" target="_blank" rel="noopener" title="${r.authors} ${r.title}. ${r.venue}, ${r.year}">${author} ${r.year}</a>`; };
  const eqs = (rows) => `<div class="m-doc is-slices"><div class="m-doc-eqs">${rows.map(([result, colour, rel, math, cites = []]) =>
    `<div class="m-doc-eq"><span class="m-doc-eq-line">${mt(result, colour)}<span class="op">${rel}</span><span class="m-eq">${math}</span></span>${cites.length ? `<span class="m-doc-cite">${cites.map(cite).join(", ")}</span>` : ""}</div>`).join("")}</div></div>`;
  const slices = () => `
      ${lead("A slice is a frontier model cut to fit one device, with the full model's layer shapes kept. It has two uses: a fair comparison of engines on one accelerator, which the grid measures, and a baseline for modeling the full model at scale, which it does not.")}
      ${steps([["#5E5CE6", "Fair comparison", "Engines on the same slice, measured on this site"],
        ["#FF9500", "Proxy for scale", "Full-model and distributed compute: a model, not a measurement"]], "<h3>Two claims</h3>")}
      <h3>How a model is cut</h3>
      ${facts([["#5E5CE6", "Same width", "Hidden size, heads, expert width, top-<i>k</i>, quant groups and vocab head unchanged"],
        ["#FF9500", "Experts first", "Fewer stored experts, the same active ones per token"],
        ["#30B0C7", "Then layers", "Only if it still does not fit, in whole repeating blocks"]])}
      <h3>Claim 1: a fair comparison on one device</h3>
      <p>A layer's cost is set by its hidden size, attention, expert width, active experts per token and quantization. A slice changes none of them, so every engine runs the full model's shapes, kernels and quantization, and the comparison is controlled.</p>
      ${eqs([["Layer cost", "#5E5CE6", "=", `<span class="m-fn">f</span>${mp([mv("Hidden size", "#5E5CE6", "H"), mv("Attention", "#007AFF", "A"), mv("Expert width", "#FF9500", "E"), mv("Top-k", "#FF9500", "K"), mv("Quantization", "#30B0C7", "Q")].join('<span class="m-comma">,</span>'))}`, ["kaplan"]]])}
      ${facts([["#5E5CE6", "Same checkpoint", "Every engine loads the identical cut, unmodified"],
        ["#30B0C7", "Same tokens", "The same token ids in, all 256 tokens out"],
        ["#34C759", "Same model", "Each engine's first token checked against the reference"],
        ["#8E8E93", "Relative Speed", "Shown as each engine against the others on the same slice"]])}
      <h3>Claim 2: a proxy for the full model at scale</h3>
      <p>For a layer cut, the full model's compute is, to first order, the slice's time scaled by the layer ratio, because each kept layer does its full-model work.</p>
      ${eqs([["Layer ratio", "#5E5CE6", "=", `${mv("Full layers", "#FF9500", "L_full")}${mo("÷")}${mv("Slice layers", "#5E5CE6", "L_slice")}`, ["kaplan"]],
        ["Full-model compute", "#FF9500", "≈", `${mv("Layer ratio", "#5E5CE6", "C")}${mo("×")}${mv("Slice time", "#5E5CE6", "T_slice")}`, ["pope"]]])}
      ${facts([["#FF9500", "Expert cuts do not scale", "The same active experts per token, so no inverse expert fraction"],
        ["#007AFF", "Vocabulary head", "Full size on every slice, counted once on its own"],
        ["#8E8E93", "Compute, not latency", "A first-order estimate, not the full model's measured time"]])}
      <p>Across GPUs or nodes, communication and coordination add to that compute, and overlap hides part of them.</p>
      ${eqs([["Distributed time", "#FF9500", "≈", `${mv("Compute", "#FF9500", "T_compute")}${mo("+")}${mv("Communication", "#30B0C7", "T_comm")}${mo("+")}${mv("Overhead", "#8E8E93", "T_overhead")}${mo("−")}${mv("Overlap", "#34C759", "T_overlap")}`, ["valiant"]]])}
      ${facts([["#5E5CE6", "Slice", "The compute baseline, measured here"],
        ["#FF9500", "Layer scaling", "The full model's work, estimated"],
        ["#30B0C7", "Cluster", "Communication, from interconnect bandwidth, latency and topology"],
        ["#34C759", "Engine", "Parallelism, kernel efficiency and how much communication it hides"]])}
      <p>Slices alone do not establish multi-node performance. This model needs calibration against real multi-GPU and multi-node runs.</p>
      <h3>What we do not claim</h3>
      ${facts([["#FF3B30", "Multi-GPU serving", "Not predicted: tensor-parallel <code>all-reduce</code> and expert parallelism decide it"],
        ["#FF3B30", "Validated at scale", "No multi-node number here comes from a slice"],
        ["#8E8E93", "Vocab head share", "Larger than in the full model, which the roofline counts"],
        ["#8E8E93", "Absolute speed", "Hidden: raw tok/s, Best TPS and Efficiency describe the full model"],
        ["#8E8E93", "Accuracy and drafts", "Not run: both need the model's real answers"]])}
      <h3>Real cuts</h3>
      ${repoFiles([["#5E5CE6", "GLM-5.3", "matrix/models.yaml", "78 of 78 layers", "12 of 256 experts, for 80 GB cards"],
        ["#FF9500", "MiMo-V2.6-Flash", "matrix/models.yaml", "48 of 48 layers", "128 of 256 experts, for 141 GB cards"],
        ["#007AFF", "DeepSeek-V4-Flash", "matrix/models.yaml", "43 of 43 layers", "16 of 256 experts"],
        ["#FF2D55", "Kimi-K3", "matrix/models.yaml", "8 of 93 layers", "Two KDA/MLA blocks, 32 of 896 experts"],
        ["#30B0C7", "Qwen3.8-Flash-Next", "matrix/models.yaml", "4 layers", "One linear, linear, linear, full block; 16 of 512 experts"],
        ["#34C759", "Gemma-4-31B", "matrix/models.yaml", "12 of 60 layers", "Two sliding/global blocks, for 24 GB cards"]])}`;

  const addEngine = () => `
      ${lead("An engine joins through a pull request: a few files declare it, and the harness runs it with the same prompts and rules as every other engine.")}
      <h3>What to add</h3>
      ${repoFiles([["#FF2D55", "Declaration", "matrix/engines.yaml", "engines.yaml", "id, os, backends, formats, tiers, recipe, pin, release_source"],
        ["#FF9500", "Name", "src/pie_evals/schema/cell.py", "cell.py", "The engine's id in EngineName"],
        ["#007AFF", "Adapter", "src/pie_evals/node/engines/", "engines/&lt;id&gt;.py", "An Engine subclass with @register, imported in get_engine"],
        ["#5E5CE6", "Recipe", "src/pie_evals/node/engines/recipes/", "recipes/&lt;id&gt;.yaml", "Its default and competitive settings, each with its reason"],
        ["#30B0C7", "Install", "src/pie_evals/node/baselines.py", "baselines.py", "A Python engine's pip spec, installed at its pin"],
        ["#8E8E93", "Known gaps", "matrix/support.yaml", "support.yaml", "What it cannot run, with the error that shows it"],
        ["#FFCC00", "Quality", "src/pie_evals/quality/engines.py", "quality/engines.py", "How it answers the question sets, if it is scored"],
        ["#34C759", "Tests", "tests/test_engines.py", "test_engines.py", "Its command line and how its output is read"],
        ["#AF52DE", "Site", "tools/webdb.py", "webdb.py", "Its name, license, repository and colour"]])}
      <p>A server that speaks OpenAI's <code>/v1/completions</code> can subclass <code>ServedEngine</code> and say only how to start it, as llama.cpp, mlx-lm, Splash and TensorRT-LLM do.</p>
      <h3>Test it locally</h3>
      ${commands([["#30B0C7", "Install", '<code>uv venv &amp;&amp; uv pip install -e ".[dev,orchestrate]"</code>'],
        ["#5E5CE6", "Matrix", "<code>pie-evals check</code>"],
        ["#007AFF", "Tests", '<code>pytest -q -m "not slow"</code>'],
        ["#FF9500", "Plan", "<code>pie-evals jobs --tier nightly --engine &lt;id&gt; --platform &lt;id&gt; --out jobs</code>"],
        ["#34C759", "Measure", "On a GPU, as the next chapter shows"]])}
      ${steps([["#FF2D55", "Pull request", "From your fork, with the files above"], ["#007AFF", "CI", "Lint, unit tests and the matrix check"],
        ["#5E5CE6", "Review", "A maintainer reviews and merges"], ["#FF9500", "Run", "A maintainer starts a tagged run"],
        ["#34C759", "Site", "The tag's rows, on the next rebuild"]], "<h3>From pull request to the site</h3>")}
      <h3>Workflows</h3>
      ${flows([["#007AFF", "Pull request", "ci.yml", "Every pull request that changes code or the matrix"],
        ["#636366", "Pie release", "pie-eval.yml", "The Macs, under the release's tag"],
        ["#FF9500", "Nightly", "nightly.yml", "Daily at 09:00 UTC, capped; untagged, so off the site"],
        ["#5E5CE6", "Weekly", "weekly.yml", "By hand; with a tag, its rows join that release"],
        ["#30B0C7", "Pod import", "pod-import.yml", "Every 10 minutes, from the project's pods, under their tag"],
        ["#34C759", "Site", "pages.yml", "Rebuilt every 5 minutes; the newest run wins a cell"]])}
      <p>Benchmark runs use the repo's secrets and its own machines. GitHub gives a fork's pull request no secrets and lets only people with write access start a workflow, so contributors open a pull request and maintainers schedule the run. A maintainer can try a branch first with <code>gh workflow run pie-eval.yml --ref &lt;branch&gt;</code>, which saves nothing to the database.</p>`;

  const runYourself = () => `
      ${lead("Measure on a machine you rent, with the same harness and the same rules. You pay the provider for what you rent.")}
      <h3>Where to rent</h3>
      ${links([["#76b900", "RunPod", "https://www.runpod.io", "NVIDIA and AMD pods on demand; what this project rents"],
        ["#76b900", "Lambda", "https://lambda.com", "NVIDIA cloud instances, from one GPU to eight"],
        ["#76b900", "Vast.ai", "https://vast.ai", "A marketplace of hosts' GPUs, consumer and datacenter"],
        ["#76b900", "CoreWeave", "https://www.coreweave.com", "Datacenter NVIDIA GPUs, for multi-GPU nodes"],
        ["#4285F4", "Google Cloud TPU", "https://cloud.google.com/tpu", "TPU v5e and v6e; the project's TPU rows run there"],
        ["#76b900", "AWS EC2", "https://aws.amazon.com/ec2/", "NVIDIA GPU instances, and EC2 Mac for Apple Silicon"],
        ["#76b900", "Azure", "https://azure.microsoft.com/en-us/products/virtual-machines/", "NVIDIA and AMD GPU virtual machines"],
        ["#76b900", "Hyperbolic", "https://www.hyperbolic.ai", "Low-cost GPUs on demand"],
        ["#76b900", "TensorDock", "https://www.tensordock.com", "Low-cost consumer and datacenter GPUs"],
        ["#636366", "Scaleway", "https://www.scaleway.com/en/hello-m1/", "Apple Silicon Macs in the cloud"],
        ["#636366", "MacStadium", "https://www.macstadium.com", "Dedicated Apple Silicon Macs"]])}
      <h3>Run the harness</h3>
      ${commands([["#30B0C7", "Install", 'Rust and uv, then in the repo <code>uv venv &amp;&amp; uv pip install -e ".[dev,orchestrate]"</code>'],
        ["#5E5CE6", "Build", "<code>pie-evals-node build --pie-commit &lt;sha&gt; --features cuda</code>, or <code>rocm</code>"],
        ["#007AFF", "Plan", "<code>pie-evals jobs --tier nightly --pie-commit &lt;sha&gt; --platform &lt;id&gt; --engine pie --engine &lt;id&gt; --out jobs</code>"],
        ["#FF9500", "Run", "<code>pie-evals-node run --job jobs/&lt;job&gt;.json --out out/&lt;job&gt; --download</code>"],
        ["#34C759", "Read", "<code>pie-evals collect --tier nightly out/&lt;job&gt;</code>, then <code>pie-evals report --tier nightly</code>"]])}
      <p><code>--platform</code> names your machine in <code>matrix/platforms.yaml</code>; add it there if it is new.</p>
      <h3>Keep it fair</h3>
      ${facts([["#34C759", "Same checkpoint", "Every engine on the same weights, and on the same cut of a slice"],
        ["#FFCC00", "Same precision", "Weights, activations and KV cache as the release declares"],
        ["#007AFF", "Same N", "Same workload and concurrency; sweep N until tok/s grows under 5%"],
        ["#64D2FF", "Cold prompts", "No prefix-cache hits in a throughput run"],
        ["#8E8E93", "One engine per GPU", "Nothing else on the device, the same memory share"],
        ["#5E5CE6", "Slices as ratios", "A slice's tok/s compared between engines, never quoted alone"]])}
      <h3>Share your results</h3>
      <p>The numbers are in <code>out/&lt;job&gt;/records.jsonl</code>, the logs beside them. No workflow imports records from outside: <code>pod-import.yml</code> reads only the project's own pods, and <code>collect.yml</code> only this repo's runs. Zip the folder and attach it to an issue or your pull request, with the machine and the commands you ran. A maintainer reviews it and can measure the cells again on the project's machines to publish them.</p>
      ${links([["#FF2D55", "Open an issue", `${REPO}/issues/new`, "Results, a question or a gap you found"],
        ["#007AFF", "Open a pull request", `${REPO}/pulls`, "An engine, a recipe or a fix"]])}`;

  // Why Trust Us: the safeguards as the workloads' rows, each marked by a small square in its chapter's colour, as the
  // outline marks the chapters; the name and its line, each row opening its chapter
  // every run in one store, its size as the site's export counts it: the runs, and the compute hours behind them
  const db = () => {
    const t = Pie.store.tables.totals || {};
    const runs = t.runs ? `${(Math.floor(t.runs / 1000) * 1000).toLocaleString("en-US")}+ runs` : "Every run";
    const hours = t.machine_s ? `, ${Math.round(t.machine_s / 3600).toLocaleString("en-US")} compute hours` : "";
    return `${runs}${hours}, in one database`;
  };
  const trust = () => {
    const rows = [["#34C759", "Same setup", "Same weights, workloads and settings for every engine", "fairness"],
      ["#8E8E93", "Dedicated machines", "Nothing else runs during a benchmark", "setup"],
      ["#FF9500", "Repeated runs", "Warmup, then rounds until the noise is small", "measurement"],
      ["#007AFF", "Same results", "Every engine checked to compute the same model", "parity"],
      ["#FF3B30", "Limit check", "Above the theoretical maximum is a CI Error", "limit-decode"],
      ["#30B0C7", "One database", db(), "measurement"],
      ["#5E5CE6", "Open source", "Harness, recipes and raw data on GitHub", null]];
    const mark = (colour) => `<span class="trust-tile" style="--tile: ${colour}" aria-hidden="true"></span>`;
    return `<ul class="welcome-list is-trust">${rows.map(([colour, t, d, chapter]) => `<li>${chapter
      ? `<button type="button" data-chapter-go="${chapter}">${mark(colour)}<b>${t}</b><span>${d}</span></button>`
      : `<a href="${REPO}" target="_blank" rel="noopener">${mark(colour)}<b>${t}</b><span>${d}</span></a>`}</li>`).join("")}</ul>`;
  };

  // a chapter's formula tables, from the Roofline and Memory pages they replace
  let viewState = null;
  const tables = (kind) => (viewState && Pie.methods?.chapter ? Pie.methods.chapter(kind, viewState).html : "");
  // a chapter with formula tables: a Limits one (limit-<setup>) or Memory Fit, the kind its tables are drawn for
  const kindOf = (id) => (id === "fit" ? "fit" : id.startsWith("limit-") ? `limit:${id.slice(6)}` : null);
  const keyOf = () => (viewState && Pie.methods?.chapter && kindOf(current) ? Pie.methods.chapter(kindOf(current), viewState).key : current);

  // the outline as the overview draws its own: a heading per group, a coloured square and a name per chapter
  const outline = CHAPTERS.map(([head, items]) => `${head ? `<div class="board-outline-head">${head}</div>` : ""}${items.map(([id, title, colour]) =>
    `<button type="button" class="board-outline-item" data-chapter-go="${id}"><i class="board-outline-dot" style="background: ${colour}" aria-hidden="true"></i><span>${title}</span></button>`).join("")}`).join("");

  // one chapter at a time, as Apple's documentation shows one article a page: the outline picks it, a push past
  // either end turns to the one before or after; the pick is kept across visits
  const LIST = CHAPTERS.flatMap(([, items]) => items);
  const KEY = "pieChapter";
  let current = (() => { try { return localStorage.getItem(KEY); } catch { return null; } })();
  if (!LIST.some(([id]) => id === current)) current = LIST[0][0];


  const place = () => `Chapter ${LIST.findIndex(([id]) => id === current) + 1} of ${LIST.length}`;

  // the chapter a push past an end turns to, named beyond that end in small grey words as the push builds
  const turnCue = (at, way) => (LIST[at] ? `<p class="chapter-turn is-${way}" aria-hidden="true">${way === "next" ? "Next" : "Previous"}: ${LIST[at][1]}<svg viewBox="0 0 16 16"><path d="${way === "next" ? "M4 6.5 8 10.5 12 6.5" : "M4 9.5 8 5.5 12 9.5"}"/></svg></p>` : "");

  const draw = () => {
    const at = LIST.findIndex(([id]) => id === current);
    const [, title, , summary, body] = LIST[at];
    drawn = keyOf();
    // a chapter as the Overview sets a section: its title and line above, the text in a card of the Overview's shape
    element.querySelector(".approach-main").innerHTML = `
      <div class="board-section-head"><div class="board-section-text"><h1 class="board-title">${title}</h1>
        <p class="board-lede">${summary}</p></div></div>
      <article class="board-card method-article${typeof body === "function" ? " has-tables" : ""}">
        <div class="method-pane-body">${typeof body === "function" ? body() : body}</div>
      </article>${turnCue(at - 1, "back")}${turnCue(at + 1, "next")}
`;  // no previous and next links: the outline beside the chapter, or a push past its end, is the way between them
    for (const item of element.querySelectorAll(".board-outline [data-chapter-go]")) item.classList.toggle("is-current", item.dataset.chapterGo === current);
    // the window's subtitle names the chapter's place, as Books does under a title
    if (Pie.toolbar?.elements?.subtitle) Pie.toolbar.elements.subtitle.textContent = place();
    // one fill that glides from the old chapter's row to the new, as the overview's outline moves its own
    const nav = element.querySelector(".board-outline"), on = nav?.querySelector(".is-current");
    if (!nav || !on) return;
    let thumb = nav.querySelector(":scope > .board-outline-thumb");
    if (!thumb) { thumb = document.createElement("span"); thumb.className = "board-outline-thumb"; thumb.setAttribute("aria-hidden", "true"); nav.prepend(thumb); }
    // placed once the page shows: a chapter opened from another page (the Overview's Add Engine) is drawn while the page
    // is still hidden, where every row reads as at the top, so the fill waits a frame or two for the page to appear
    const placeFill = (tries) => {
      const row = nav.querySelector(".is-current");
      if (!row) return;
      if (row.offsetParent === null) { if (tries > 0) requestAnimationFrame(() => placeFill(tries - 1)); return; }
      thumb.style.transform = `translateY(${row.offsetTop}px)`;
      thumb.style.height = `${row.offsetHeight}px`;
    };
    placeFill(120);
    flowPaddles();
  };

  const content = `
    <div class="board-inner approach-inner">
      <nav class="board-outline" aria-label="Chapters">${outline}</nav>
      <div class="board-main approach-main"></div>
    </div>`;

  let drawn = null;  // the chapter as last drawn: a new workload or release draws its tables again

  // a chapter picked in the outline or the links under it opens at its top
  element.addEventListener("click", (event) => {
    // the limit's workload bar: the grid's own setup, so a pick changes both pages
    // the limit's workload pop-up opens the grid's own setup menu, so a pick changes both pages
    const setup = event.target.closest("[data-methods-setup]");
    if (setup) { event.stopPropagation(); Pie.popover.open(setup, "methods:setup", null); return; }
    const mode = event.target.closest("[data-mode]");
    if (mode && viewState) { viewState.platform.mode = mode.dataset.mode; Pie.platform.changed(); return; }
    // a term's source opens its catalog page, as the sidebar would
    const source = event.target.closest("[data-go]");
    if (source) { document.querySelector(`.sidebar-item[data-table="${source.dataset.go}"]`)?.click(); return; }
    // a step carousel's paddle: one step back or on
    const flow = event.target.closest("[data-flow]");
    if (flow) {
      const row = flow.closest(".flow-carousel")?.querySelector(".welcome-flow"), step = row?.firstElementChild;
      if (step) row.scrollBy({ left: Number(flow.dataset.flow) * step.getBoundingClientRect().width, behavior: "smooth" });
      return;
    }
    const go = event.target.closest("[data-chapter-go]");
    if (!go || go.dataset.chapterGo === current) return;
    current = go.dataset.chapterGo;
    try { localStorage.setItem(KEY, current); } catch { /* private windows can refuse storage */ }
    draw();
    element.scrollTop = 0;
  });

  element.addEventListener("scroll", (event) => { if (event.target.classList?.contains("welcome-flow")) flowPaddles(); }, { capture: true, passive: true });
  window.addEventListener("resize", () => flowPaddles(), { passive: true });

  // a row's hover card (the Install Size chapter's engines) in the site's chart tooltip, as the other pages show theirs
  const tooltip = document.getElementById("chart-tooltip");
  element.addEventListener("mousemove", (event) => {
    const target = event.target.closest("[data-tip-html]");
    if (!tooltip) return;
    if (!target) { tooltip.hidden = true; tooltip.classList.remove("is-card"); return; }
    tooltip.innerHTML = target.dataset.tipHtml;
    tooltip.classList.add("is-card");
    tooltip.hidden = false;
    const x = Math.min(event.clientX + 14, window.innerWidth - tooltip.offsetWidth - 8);
    const y = Math.min(event.clientY + 14, window.innerHeight - tooltip.offsetHeight - 8);
    tooltip.style.left = `${Math.max(8, x)}px`;
    tooltip.style.top = `${Math.max(8, y)}px`;
  });
  element.addEventListener("mouseleave", () => { if (tooltip) tooltip.hidden = true; });

  // turning the page by scrolling, as Books turns one: a push on past a chapter's end opens the next at its top, a
  // push back past its start the one before at its bottom. The gesture that brings the chapter to an end only arrives
  // there, its glide counting for nothing; a fresh one, TURN pixels past the end, turns the page, the chapter giving a
  // little and the next one's name showing beyond the end as it builds
  const TURN = 120;  // px of push past the end, or of a finger's travel on a phone
  const QUIET = 140;  // ms with no wheel event that end a gesture: a trackpad's glide sends one every frame
  const GIVE = 24;  // px the chapter gives at the full push, as a rubber band
  const still = matchMedia("(prefers-reduced-motion: reduce)");
  let push = 0, way = 0, give = 0;  // the push so far, its way (1 on, -1 back) and how far the chapter has given
  let turning = false;  // the old chapter leaving and the new one arriving: input waits
  let relaxing = 0, settling = 0;  // timers: a push left alone springs back; the turn's own glide dies away
  // the wheel gesture: its last event, whether it counts, when it came to rest at an end and its smallest step since
  const wheel = { at: -Infinity, spent: false, rest: Infinity, ebb: Infinity };

  const at = () => LIST.findIndex(([id]) => id === current);
  // the chapter at its end (w 1) or its start (w -1): one shorter than the window is at both
  const atEdge = (w) => (w > 0 ? element.scrollTop + element.clientHeight >= element.scrollHeight - 2 : element.scrollTop <= 1);
  // a menu open stays open and text chosen in the chapter stays chosen: no turn under either
  const busy = () => { const chosen = getSelection(); return Pie.popover?.isOpen() || (chosen && !chosen.isCollapsed && element.contains(chosen.anchorNode)); };

  // the push as it builds: the chapter gives toward the end pushed, easing off as it goes, and the cue there fades up
  const show = () => {
    const main = element.querySelector(".approach-main"), p = Math.min(1, push / TURN);
    give = p ? -way * GIVE * (1 - (1 - p) ** 2) : 0;
    main.style.transform = give ? `translateY(${give}px)` : "";
    for (const cue of main.querySelectorAll(".chapter-turn")) cue.style.opacity = cue.classList.contains(way > 0 ? "is-next" : "is-back") ? p : 0;
  };
  const relax = () => { clearTimeout(relaxing); if (!push && !give) return; push = 0; show(); };
  // the push set one way; none where it leads nowhere, the first chapter's start or the last one's end
  const pushTo = (w, amount) => {
    clearTimeout(relaxing);
    if (!LIST[at() + w]) { relax(); return false; }
    way = w;
    push = amount;
    show();
    return true;
  };

  // the turn: the old chapter fades and drifts the way of the push as the new one comes in from the other side;
  // with reduced motion it simply changes
  const turn = (w) => {
    const to = LIST[at() + w], main = element.querySelector(".approach-main");
    clearTimeout(relaxing);
    push = 0;
    if (!to) return;
    turning = true;
    element.classList.add("is-turning");  // the turn's own glide scrolls nothing
    if (tooltip) tooltip.hidden = true;  // a row's hover card goes with its chapter
    // the same way in as a pick in the outline, the new chapter at its top going on and at its bottom going back
    const open = () => {
      Pie.approach.open(to[0]);
      main.style.transition = "none";  // the give goes at once, under the fade
      give = 0;
      main.style.transform = "";
      element.scrollTop = w > 0 ? 0 : element.scrollHeight;
      void main.offsetWidth;
      main.style.transition = "";
    };
    const done = () => { turning = false; settle(); };
    if (still.matches) { open(); done(); return; }
    const leave = main.animate([{ opacity: 1, transform: `translateY(${give}px)` }, { opacity: 0, transform: `translateY(${give - 12 * w}px)` }],
      { duration: 120, easing: "cubic-bezier(.4, 0, 1, 1)", fill: "forwards" });
    leave.onfinish = () => {
      open();
      main.animate([{ opacity: 0, transform: `translateY(${16 * w}px)` }, { opacity: 1, transform: "none" }],
        { duration: 180, easing: "cubic-bezier(.22, 1, .36, 1)" }).onfinish = done;
      leave.cancel();
    };
  };
  // the chapter scrolls again once the glide that turned it has died away: each of its events puts this off again
  const settle = () => {
    clearTimeout(settling);
    settling = setTimeout(() => { if (!turning) element.classList.remove("is-turning"); }, QUIET);
  };

  element.addEventListener("wheel", (event) => {
    if (event.ctrlKey || event.shiftKey) return;  // a pinch zooms; Shift scrolls sideways
    const unit = event.deltaMode === 1 ? 16 : event.deltaMode === 2 ? element.clientHeight : 1;
    const dy = event.deltaY * unit, step = Math.abs(dy), now = event.timeStamp;
    // a new gesture: after a pause, or a swipe cutting short a glide that has rested at an end a while
    const fresh = now - wheel.at > QUIET || (now - wheel.rest > 250 && step > 3 * wheel.ebb + 6);
    wheel.at = now;
    if (fresh) Object.assign(wheel, { rest: Infinity, ebb: Infinity });
    else if (wheel.rest < Infinity) wheel.ebb = Math.min(wheel.ebb, step);
    if (fresh && !turning) element.classList.remove("is-turning");
    else if (element.classList.contains("is-turning")) settle();
    if (turning || step <= Math.abs(event.deltaX * unit) || busy()) return;  // sideways is a carousel's
    const w = Math.sign(dy);
    if (fresh) wheel.spent = !atEdge(w);  // only a gesture that starts at the end counts
    if (!atEdge(w)) { wheel.spent = true; relax(); return; }
    if (wheel.spent) { if (wheel.rest === Infinity) Object.assign(wheel, { rest: now, ebb: step }); return; }  // the gesture that arrived, gliding on
    if (!pushTo(w, (w === way ? push : 0) + step)) return;
    if (push < TURN) { relaxing = setTimeout(relax, 600); return; }
    turn(w);
    Object.assign(wheel, { spent: true, rest: now, ebb: step });  // the rest of this glide turns nothing more
  }, { passive: true });

  // a finger: the same push, counted from where it came down and only if the chapter was at that end then; the page
  // turns as it lifts, and a sideways drag is a carousel's
  let finger = null;
  element.addEventListener("touchstart", (event) => {
    const t = event.touches[0];
    finger = event.touches.length === 1 && !turning && !busy() ? { x: t.clientX, y: t.clientY, on: atEdge(1), back: atEdge(-1), axis: "" } : null;
  }, { passive: true });
  element.addEventListener("touchmove", (event) => {
    if (!finger) return;
    const t = event.touches[0], dx = finger.x - t.clientX, dy = finger.y - t.clientY, w = Math.sign(dy);
    if (!finger.axis && Math.hypot(dx, dy) > 8) finger.axis = Math.abs(dx) > Math.abs(dy) ? "x" : "y";
    if (finger.axis === "x" || event.touches.length > 1) { finger = null; relax(); return; }
    if (w && (w > 0 ? finger.on : finger.back) && atEdge(w)) pushTo(w, Math.abs(dy));
    else relax();
  }, { passive: true });
  element.addEventListener("touchend", () => { if (finger && push >= TURN) turn(way); else relax(); finger = null; }, { passive: true });
  element.addEventListener("touchcancel", () => { finger = null; relax(); }, { passive: true });

  // the keys that scroll a page, pressed at an end: the press that reaches the end only arrives, the next one turns,
  // and a held key's repeats never do
  const KEYS = { PageDown: 1, ArrowDown: 1, " ": 1, PageUp: -1, ArrowUp: -1 };
  document.addEventListener("keydown", (event) => {
    const target = event.target, w = event.key === " " && event.shiftKey ? -1 : KEYS[event.key];
    if (!w || element.hidden || event.repeat || event.defaultPrevented || event.altKey || event.ctrlKey || event.metaKey || (event.shiftKey && event.key !== " ")) return;
    if (target !== document.body && !element.contains(target)) return;  // the sidebar's and the bar's own keys
    if (target.closest("input, textarea, select") || target.isContentEditable || (event.key === " " && target.closest("button, a"))) return;  // typing, or Space pressing a button
    if (turning || busy() || !atEdge(w) || !LIST[at() + w]) return;
    event.preventDefault();
    turn(w);
  });

  Pie.approach = {
    element,
    // a chapter opened from elsewhere (the Overview's welcome): it is the one drawn the next time the page shows
    open(id) {
      if (!LIST.some(([c]) => c === id)) return;
      current = id;
      try { localStorage.setItem(KEY, current); } catch { /* private windows can refuse storage */ }
      if (element.dataset.ready === "1") draw();
    },
    chapters: LIST.length,
    place: () => place(),
    render(state) {
      viewState = state;
      element.hidden = state.table !== "approach";
      if (element.hidden) return;
      if (element.dataset.ready !== "1") {
        element.innerHTML = content + (Pie.board?.footer?.() || "");  // the overview's foot, read once the overview has loaded
        element.dataset.ready = "1";
        // Spec Decode's acceptance, typed in the limit's bar, works out its rows again
        // (not while the field is being typed in, which a redraw would take the focus from)
        Pie.bindSpecField?.(element, () => { if (current.startsWith("limit-") && !document.activeElement?.matches("[data-alpha]")) draw(); });
        element.addEventListener("focusout", (event) => { if (event.target.matches("[data-alpha]") && current.startsWith("limit-")) requestAnimationFrame(draw); });
        draw();
      } else if (keyOf() !== drawn) draw();
    },
  };
})();
