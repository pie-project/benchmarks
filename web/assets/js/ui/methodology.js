window.Pie = window.Pie || {};

// The methodology page: the roofline that bounds tokens per second, its three regimes, and the layers between that ceiling and a real workload.
(() => {
  const element = document.getElementById("methodology");

  const rows = (items) => `<ul class="method-rows">${items.map(([title, text]) =>
    `<li><span class="method-row-title">${title}</span><span class="method-row-text">${text}</span></li>`).join("")}</ul>`;
  // a formula strip; several lines keep their line breaks and read left to right
  const formula = (...lines) => `<div class="method-formula"><span class="method-formula-text${lines.length > 1 ? " is-lines" : ""}">${lines.join("<br>")}</span></div>`;
  const op = (text) => `<span class="op">${text}</span>`;
  const pane = (title, summary, body) => `
    <section class="method-pane">
      <h2>${title}</h2>
      <p class="method-summary">${summary}</p>
      <div class="method-pane-body">${body}</div>
    </section>`;

  const roofline = pane("The roofline", "Each step of the model takes at least the slowest of three times.", `
    ${formula(
      `step time ${op("≥")} max( bytes moved ${op("÷")} memory bandwidth,`,
      `                 arithmetic ${op("÷")} peak compute,`,
      `                 bytes exchanged ${op("÷")} interconnect )`,
      `tokens/s  ${op("=")} tokens produced per step ${op("÷")} step time`,
    )}
    <p>The interconnect term applies only when a model spans several GPUs.</p>`);

  const decode = pane("Decoding B requests", "Each request has C tokens of context. The weights are read once per step and shared by all B requests.", `
    ${formula(
      `bytes      ${op("≈")} W ${op("+")} B ${op("·")} C ${op("·")} k`,
      `arithmetic ${op("≈")} 2 ${op("·")} P ${op("·")} B`,
      `max tok/s  ${op("=")} B ${op("÷")} max( (W ${op("+")} B·C·k) ${op("÷")} BW,  2·P·B ${op("÷")} FLOPS )`,
    )}
    ${rows([
      ["W", "Active weight bytes, read once per step."],
      ["k", "Cache bytes per token of context."],
      ["P", "Active parameters."],
    ])}`);

  const regimes = pane("Three regimes", "Which term of the bound dominates depends on the batch and the context length.", rows([
    ["One request, short context", "Limited by memory bandwidth (the weights). Ceiling: BW ÷ W."],
    ["Many requests, short context", "Limited by compute. Ceiling: FLOPS ÷ 2P."],
    ["Long context, any batch", "Limited by memory bandwidth (the cache). Ceiling: BW ÷ (C·k) per request, so batching stops helping."],
  ]));

  const prefill = pane("Prefill is compute-bound", "Reading the prompt handles hundreds of tokens per weight read.", `
    ${formula(`prefill tok/s ${op("≈")} FLOPS ${op("÷")} 2P`)}
    <p>The workload that reaches the ceiling is a dense model with short contexts, large batches (or prefill) and no idle time. That is the clean benchmark case, where engines get closest to the ceiling.</p>`);

  const cake = pane("What the number depends on", "Seven layers, from the hardware to the task.", `
    ${rows([
      ["1 · Hardware", "Bandwidth, compute, memory capacity, interconnect."],
      ["2 · Model shape", "Active parameters (P, W), cache bytes per token (k), MoE sparsity, linear-attention layers (a fixed-size state instead of a growing cache)."],
      ["3 · Forward pass", "What share of the ceiling each step achieves: the kernels."],
      ["4 · Batch formation", "How many tokens each step carries: concurrent requests, branches, speculative tokens. Capped by memory capacity and latency targets."],
      ["5 · Time utilization", "Idle gaps between steps and during tool calls."],
      ["6 · Reuse", "Prefill avoided through caching."],
      ["7 · Usefulness", "Tokens that actually help finish the task."],
    ])}
    <p>Layers 1–2 set the ceiling, layer 3 is efficiency within one step, and layers 4–7 decide how much of the ceiling a workload actually reaches.</p>`);

  const agents = pane("Agentic workloads", "The basic bound assumes an endless supply of short, independent requests. Agents break that in five ways.", `
    ${rows([
      ["Long, growing contexts (30–100k tokens)", "Memory capacity caps the batch: B ≤ (memory − W) ÷ (C·k). Few long conversations fit, and the cache term C·k dominates the bytes, so the step is memory-bound again even with batching."],
      ["Mostly prefill (about 21× a chatbot’s prompt reading, per CacheWise)", "Time splits between compute-bound prefill and memory-bound decode, weighted by the workload’s mix."],
      ["Tool waits", "Multiply by the duty cycle (1 − tool fraction), unless other work fills the gap."],
      ["Repeated history", "Multiply prefill cost by (1 − reuse rate)."],
      ["Sequential steps with latency targets", "One agent cannot batch with itself. The batch comes only from parallel agents or branches, and latency targets cap it."],
    ])}
    <p class="method-subhead">The useful ceiling for agents</p>
    ${formula(
      `useful tok/s ${op("≈")} min( compute ceiling,`,
      `                    bandwidth ceiling with long-context cache,`,
      `                    memory-capacity ceiling )`,
      `               ${op("×")} (1 ${op("−")} idle share) ${op("×")} reuse factor ${op("×")} usefulness`,
    )}
    <p>For hybrid models such as Qwen3.6 and Qwen3.8, k is small, because most layers keep a fixed-size state instead of a growing cache. That loosens the capacity limit for long agent contexts, and it is why Marconi-style state checkpointing matters.</p>`);

  const content = `
    <header class="method-head">
      <h1>Methodology</h1>
      <p class="method-lede">What bounds tokens per second, and what each number on this site depends on.</p>
    </header>
    ${roofline}${decode}${regimes}${prefill}${cake}${agents}`;

  Pie.methodology = {
    element,
    render(state) {
      element.hidden = state.table !== "methodology";
      if (!element.hidden && element.dataset.ready !== "1") {
        element.innerHTML = `<div class="method-inner">${content}</div>`;
        element.dataset.ready = "1";
      }
    },
  };
})();
