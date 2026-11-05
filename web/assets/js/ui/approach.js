window.Pie = window.Pie || {};

// Methodology: how the benchmark is run, written as prose, a chapter at a time, with the overview's outline down
// the left; a chapter added to CHAPTERS joins the outline and the previous and next links.
(() => {
  const element = document.getElementById("approach");

  // [outline group, [id, title, colour, summary, body]]
  const CHAPTERS = [
    ["Setup", [
      ["setup", "Test Setup", "#8E8E93", "The machines, engines and versions behind every number.", `<p class="approach-empty">This chapter is being written.</p>`],
      ["workloads", "Workloads", "#30B0C7", "Decode, prefill, batching and speculative decoding, and what each measures.", `<p class="approach-empty">This chapter is being written.</p>`],
      ["fairness", "Fairness", "#34C759", "How every engine gets the same weights, settings and chance.", `<p class="approach-empty">This chapter is being written.</p>`],
      ["measurement", "Measurement", "#FF9500", "Rounds, warmup, noise and how a cell's number is chosen.", `<p class="approach-empty">This chapter is being written.</p>`],
    ]],
    ["Models", [
      ["slices", "Model Slices", "#5E5CE6", "Single-device architectural proxies.", `
        <p>We use single-device model slices to benchmark frontier architectures continuously without the cost and energy of multi-GPU clusters. Frontier models now exceed 400B to 800B parameters and require up to eight datacenter GPUs just to load into memory. Benchmarking these full checkpoints across every engine, hardware SKU, and software release creates a combinatorial matrix that is too expensive and energy-intensive to run continuously.</p>
        <p>A model slice shrinks a model's memory footprint to fit one device while keeping its per-layer execution identical to the full model. A naive alternative is to benchmark a smaller model from the same family, such as an 8B model in place of a 400B model. However, smaller models use narrower hidden dimensions and fewer attention heads, which trigger completely different GPU kernel schedules. Instead, we slice the full model directly under three rules:</p>
        <ol class="method-list">
          <li><b>Keep layer width unchanged.</b> We preserve the exact hidden dimension, expert intermediate width, attention head layout, active experts per token (top-<i>k</i>), quantization group size, and vocabulary head. Every matrix multiplication and attention kernel runs with the exact tensor shapes of the full model.</li>
          <li><b>Prune inactive experts before cutting layers.</b> In sparse Mixture-of-Experts (MoE) models, each token activates only <i>k</i> out of <i>E</i> experts. We first reduce the stored expert pool (<i>E′</i> &lt; <i>E</i>) while keeping <i>k</i> fixed (for example, keeping all 78 layers and 40B active parameters of GLM-5.3 on 80 GB GPUs). For single-request decoding, this cuts static memory without changing the active parameters, memory reads, or FLOPs per layer. When the model still exceeds device memory, we reduce the number of layers (<i>L′</i> &lt; <i>L</i>, such as 8 of 93 layers for Kimi-K3).</li>
          <li><b>Cut layers in multiples of the repeating block.</b> Modern architectures interleave different layer types, such as three linear-attention layers per full-attention layer in Qwen3.8. We retain an integer multiple of this repeating block so that the slice keeps the exact ratio of attention and expert layers.</li>
        </ol>
        <p>Model slices accurately capture relative engine speed on a single device. Transformer inference executes repeating layer blocks sequentially. Running <i>L′</i> layers exercises the same kernels, KV-cache paging, and scheduling paths as running <i>L</i> layers. A model slice directly matches the single-device workload of a pipeline-parallel stage and closely approximates the per-device compute and memory regime of a tensor-parallel shard.</p>
        <p>We restrict model slices to workloads where speed does not depend on output quality. Removing layers or experts breaks the model's language quality, which raises two potential issues. First, a sliced model may emit an end-of-sequence token early; we prevent this by disabling early termination (<code>ignore_eos</code>) and forcing every run to generate all 256 tokens. Second, nonsensical outputs invalidate workloads that depend on token probabilities, such as speculative decoding and accuracy benchmarks. We therefore evaluate model slices only on Raw Decode and Prefill, where execution time depends strictly on tensor shapes and sequence length.</p>
        <h3>Limitations</h3>
        <p>Because model slices run on a single device, they do not measure multi-GPU communication overhead such as tensor-parallel <code>all-reduce</code>. In addition, because we do not scale the vocabulary output head, it accounts for a larger share of total work in a slice than in the full model (our roofline model accounts for this explicitly). Finally, a slice's raw token rate (<code>tok/s</code>) is not the full model's speed. We never report model slices in Best TPS or full-model Kernel Efficiency; we use them strictly for Relative Speed, where all engines run the exact same slice head-to-head.</p>`],
      // the former Memory page, its formulas drawn by methods.js
      ["fit", "Memory Fit", "#AF52DE", "How we decide whether a model fits a machine.", () => `
        <p>Before a model runs on a machine, we check that it fits: its weights at their precision, with headroom for the KV cache and the engine's own buffers, against the memory the machine lets its GPU use. Where a model does not fit, the grid shows a crossed circle instead of a number.</p>
        ${tables("fit")}`],
    ]],
    ["Limits", [
      // the former Roofline page: the limit for the workload picked in its bar
      ["limit", "Theoretical Limit", "#FF3B30", "The roofline ceiling each engine is measured against.", () => `
        <p>Kernel Efficiency compares an engine's measured speed with the most the machine could deliver: the slower of reading every byte a step needs from memory and doing every operation it needs at the chip's peak rate. Pick a workload to see how its limit is worked out, each term defined and its source cited.</p>
        ${tables("limit")}`],
    ]],
    ["Quality", [
      ["parity", "Parity Checks", "#007AFF", "How we confirm every engine computes the same model.", `<p class="approach-empty">This chapter is being written.</p>`],
      ["accuracy", "Accuracy", "#FFCC00", "Benchmark scores on the same weights and machine.", `<p class="approach-empty">This chapter is being written.</p>`],
    ]],
  ];

  // a chapter's formula tables, from the Roofline and Memory pages they replace
  let viewState = null;
  const tables = (kind) => (viewState && Pie.methods?.chapter ? Pie.methods.chapter(kind, viewState).html : "");
  const keyOf = () => (viewState && Pie.methods?.chapter && (current === "limit" || current === "fit") ? Pie.methods.chapter(current, viewState).key : current);

  // the outline as the overview draws its own: a heading per group, a coloured square and a name per chapter
  const outline = CHAPTERS.map(([head, items]) => `<div class="board-outline-head">${head}</div>${items.map(([id, title, colour]) =>
    `<button type="button" class="board-outline-item" data-chapter-go="${id}"><i class="board-outline-dot" style="background: ${colour}" aria-hidden="true"></i><span>${title}</span></button>`).join("")}`).join("");

  // one chapter at a time, as Apple's documentation shows one article a page: the outline picks it, the links under
  // it step to the one before and after; the pick is kept across visits
  const LIST = CHAPTERS.flatMap(([, items]) => items);
  const KEY = "pieChapter";
  let current = (() => { try { return localStorage.getItem(KEY); } catch { return null; } })();
  if (!LIST.some(([id]) => id === current)) current = LIST[0][0];

  // the chapters before and after as small picks under the card, as the Overview sets its picks
  const step = (chapter, label, cls) => chapter ? `<button type="button" class="filter-button board-card-pick approach-step ${cls}" aria-label="${label}: ${chapter[1]}" data-chapter-go="${chapter[0]}">${cls === "is-previous" ? "‹ " : ""}${chapter[1]}${cls === "is-next" ? " ›" : ""}</button>` : "<span></span>";

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
      </article>
      ${LIST.length > 1 ? `<nav class="approach-steps" aria-label="Chapters">${step(LIST[at - 1], "Previous", "is-previous")}${step(LIST[at + 1], "Next", "is-next")}</nav>` : ""}`;
    for (const item of element.querySelectorAll(".board-outline [data-chapter-go]")) item.classList.toggle("is-current", item.dataset.chapterGo === current);
    // one fill that glides from the old chapter's row to the new, as the overview's outline moves its own
    const nav = element.querySelector(".board-outline"), on = nav?.querySelector(".is-current");
    if (!nav || !on) return;
    let thumb = nav.querySelector(":scope > .board-outline-thumb");
    if (!thumb) { thumb = document.createElement("span"); thumb.className = "board-outline-thumb"; thumb.setAttribute("aria-hidden", "true"); nav.prepend(thumb); }
    thumb.style.transform = `translateY(${on.offsetTop}px)`;
    thumb.style.height = `${on.offsetHeight}px`;
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
    const mode = event.target.closest("[data-mode]");
    if (mode && viewState) { viewState.platform.mode = mode.dataset.mode; Pie.platform.changed(); return; }
    // a term's source opens its catalog page, as the sidebar would
    const source = event.target.closest("[data-go]");
    if (source) { document.querySelector(`.sidebar-item[data-table="${source.dataset.go}"]`)?.click(); return; }
    const go = event.target.closest("[data-chapter-go]");
    if (!go || go.dataset.chapterGo === current) return;
    current = go.dataset.chapterGo;
    try { localStorage.setItem(KEY, current); } catch { /* private windows can refuse storage */ }
    draw();
    element.scrollTop = 0;
  });

  Pie.approach = {
    element,
    chapters: LIST.length,
    render(state) {
      viewState = state;
      element.hidden = state.table !== "approach";
      if (element.hidden) return;
      if (element.dataset.ready !== "1") {
        element.innerHTML = content;
        element.dataset.ready = "1";
        // Spec Decode's acceptance, typed in the limit's bar, works out its rows again
        // (not while the field is being typed in, which a redraw would take the focus from)
        Pie.bindSpecField?.(element, () => { if (current === "limit" && !document.activeElement?.matches("[data-alpha]")) draw(); });
        element.addEventListener("focusout", (event) => { if (event.target.matches("[data-alpha]") && current === "limit") requestAnimationFrame(draw); });
        draw();
      } else if (keyOf() !== drawn) draw();
    },
  };
})();
