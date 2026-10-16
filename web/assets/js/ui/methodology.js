window.Pie = window.Pie || {};

// The Methods page: one continuous note, as a paper reads. The roofline bound, its regimes, prefill, the layers below the ceiling, and agents.
(() => {
  const element = document.getElementById("methodology");

  const eq = (...lines) => `<pre class="methods-eq">${lines.join("\n")}</pre>`;
  const table = (head, body) => `<table class="methods-table">
      <thead><tr>${head.map((cell) => `<th>${cell}</th>`).join("")}</tr></thead>
      <tbody>${body.map((row) => `<tr>${row.map((cell) => `<td>${cell}</td>`).join("")}</tr>`).join("")}</tbody>
    </table>`;
  const cite = (href, name) => `<a href="${href}" target="_blank" rel="noopener">${name}</a>`;

  // attainable FLOP/s against arithmetic intensity, log-log: the sloped memory roof meets the flat compute roof at the ridge
  const plot = `
    <figure class="methods-figure">
      <svg viewBox="0 0 640 330" role="img" aria-label="Roofline: attainable compute rises with arithmetic intensity until the ridge, then stays flat at peak compute. Decode at one request sits on the sloped, memory-bound part; batched decode and prefill sit on the flat, compute-bound part.">
        <path class="axis" d="M50 20V290H630"/>
        <path class="ridge" d="M372 60V290"/>
        <path class="roof" d="M142 290 372 60H625"/>
        <circle cx="152" cy="280" r="5"/><circle cx="430" cy="60" r="5"/><circle cx="590" cy="60" r="5"/>
        <text x="60" y="30">attainable FLOP/s (log)</text>
        <text x="630" y="314" text-anchor="end">arithmetic intensity, FLOP per byte (log)</text>
        <text x="170" y="284">decode, one request</text>
        <text x="430" y="48" text-anchor="middle">batched decode</text>
        <text x="590" y="48" text-anchor="middle">prefill</text>
        <text x="380" y="270">ridge = FLOPS ÷ BW</text>
        <text x="212" y="160" class="label" transform="rotate(-45 212 160)">memory-bound</text>
        <text x="500" y="80" class="label">compute-bound</text>
      </svg>
      <figcaption><b>Figure 1.</b> The roofline. Left of the ridge a step is limited by bandwidth; right of it, by compute.</figcaption>
    </figure>`;

  const content = `
    <article class="methods">
      <header>
        <p class="methods-eyebrow">Methods</p>
        <h1>The roofline of LLM inference</h1>
        <p class="methods-lede">What bounds tokens per second, and which layers sit between that bound and what a workload actually gets.</p>
      </header>

      <h2><span>1</span>The bound on one step</h2>
      <p>Each step of the model takes at least the slowest of three times:</p>
      ${eq("step time ≥ max( bytes moved ÷ memory bandwidth,",
           "                 arithmetic ÷ peak compute,",
           "                 bytes exchanged ÷ interconnect )",
           "tokens/s  = tokens produced per step ÷ step time")}
      <p>The interconnect term applies only when a model spans several GPUs. The ratio of arithmetic to bytes is the step’s <i>arithmetic intensity</i>; where it equals peak compute ÷ bandwidth, the two roofs meet (${cite("https://doi.org/10.1145/1498765.1498785", "Williams et al., 2009")}).</p>
      ${plot}

      <h2><span>2</span>Decoding B requests</h2>
      <p>Decode B requests at once, each with C tokens of context. The weights are read once per step and shared by all B; each request reads its own cache.</p>
      ${eq("bytes      ≈ W + B · C · k",
           "arithmetic ≈ 2 · P · B",
           "max tok/s  = B ÷ max( (W + B·C·k) ÷ BW,  2·P·B ÷ FLOPS )")}
      ${table(["Symbol", "Meaning"], [
        ["W", "active weight bytes, read once per step"],
        ["k", "cache bytes per token of context"],
        ["P", "active parameters"],
        ["BW, FLOPS", "memory bandwidth and peak compute of the device"],
      ])}

      <h2><span>3</span>Three regimes</h2>
      <p>Which term of the bound dominates depends on the batch and the context length.</p>
      ${table(["Workload", "Limited by", "Ceiling"], [
        ["One request, short context", "memory bandwidth (weights)", "BW ÷ W"],
        ["Many requests, short context", "compute", "FLOPS ÷ 2P"],
        ["Long context, any batch", "memory bandwidth (the cache)", "BW ÷ (C·k) per request, so batching stops helping"],
      ])}

      <h2><span>4</span>Prefill is compute-bound</h2>
      <p>Reading the prompt handles hundreds of tokens per weight read, so prefill sits far right of the ridge:</p>
      ${eq("prefill tok/s ≈ FLOPS ÷ 2P")}
      <p>The workload that reaches the ceiling is a dense model with short contexts, large batches (or prefill) and no idle time. That is the clean benchmark case, where engines get closest to the ceiling.</p>

      <h2><span>5</span>What the number depends on</h2>
      <p>Seven layers lie between the hardware and a finished task. Layers 1–2 set the ceiling, layer 3 is efficiency within one step, and layers 4–7 decide how much of the ceiling a workload actually reaches.</p>
      ${table(["", "Layer", "What it sets", "Further reading"], [
        ["1", "Hardware", "bandwidth, compute, memory capacity, interconnect", ""],
        ["2", "Model shape", "active parameters (P, W), cache bytes per token (k), MoE sparsity, linear-attention layers", cite("https://arxiv.org/abs/2412.06464", "Gated DeltaNet")],
        ["3", "Forward pass", "the share of the ceiling each step achieves: the kernels", `${cite("https://arxiv.org/abs/2205.14135", "FlashAttention")}, ${cite("https://arxiv.org/abs/2408.11743", "Marlin")}`],
        ["4", "Batch formation", "tokens per step: concurrent requests, branches, speculative tokens; capped by memory and latency targets", `${cite("https://arxiv.org/abs/2309.06180", "PagedAttention")}, ${cite("https://arxiv.org/abs/2403.02310", "Sarathi-Serve")}, ${cite("https://arxiv.org/abs/2401.15077", "EAGLE")}`],
        ["5", "Time utilization", "idle gaps between steps and during tool calls", `${cite("https://arxiv.org/abs/2502.13965", "Autellix")}, ${cite("https://arxiv.org/abs/2402.01869", "InferCept")}`],
        ["6", "Reuse", "prefill avoided through caching", `${cite("https://arxiv.org/abs/2312.07104", "SGLang")}, ${cite("https://arxiv.org/abs/2411.19379", "Marconi")}`],
        ["7", "Usefulness", "tokens that actually help finish the task", cite("https://arxiv.org/abs/2412.20993", "Certaindex")],
      ])}

      <h2><span>6</span>Adjusting the bound for agents</h2>
      <p>The basic bound assumes an endless supply of short, independent requests. Agents break that in five ways, and each adds a term:</p>
      ${table(["What agents change", "The term to add"], [
        ["Long, growing contexts (30–100k tokens)", "Memory capacity caps the batch: B ≤ (memory − W) ÷ (C·k). Few long conversations fit, and the cache term C·k dominates the bytes, so the step is memory-bound again even with batching."],
        [`Mostly prefill (about 21× a chatbot’s, per ${cite("https://arxiv.org/abs/2606.16824", "CacheWise")})`, "Time splits between compute-bound prefill and memory-bound decode, weighted by the workload’s mix."],
        ["Tool waits", "Multiply by the duty cycle (1 − tool fraction), unless other work fills the gap."],
        ["Repeated history", "Multiply prefill cost by (1 − reuse rate)."],
        ["Sequential steps with latency targets", "One agent cannot batch with itself. The batch comes only from parallel agents or branches, and latency targets cap it."],
      ])}
      <p>For agents the useful ceiling is therefore roughly:</p>
      ${eq("useful tok/s ≈ min( compute ceiling,",
           "                    bandwidth ceiling with long-context cache,",
           "                    memory-capacity ceiling )",
           "               × (1 − idle share) × reuse factor × usefulness")}
      <p>For hybrid models such as Qwen3.6 and Qwen3.8, k is small, because most layers keep a fixed-size state instead of a growing cache. That loosens the capacity limit for long agent contexts, and it is why state checkpointing in the manner of ${cite("https://arxiv.org/abs/2411.19379", "Marconi")} matters.</p>
    </article>`;

  Pie.methodology = {
    element,
    render(state) {
      element.hidden = state.table !== "methodology";
      if (!element.hidden && element.dataset.ready !== "1") {
        element.innerHTML = content;
        element.dataset.ready = "1";
      }
    },
  };
})();
