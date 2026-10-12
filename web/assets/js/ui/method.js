window.Pie = window.Pie || {};

(() => {
  const element = document.getElementById("method");

  // one outlined card per topic: a small grey line icon, title, a plain sentence, the definition, then details
  const glyphs = {
    decode: '<path d="M4 17a8 8 0 1 1 16 0"/><path d="m12 17 4-5"/>',
    prefill: '<path d="M5 6h14M5 10h14M5 14h9"/><path d="m16 17 2 2 3-4"/>',
    ttft: '<circle cx="12" cy="13" r="7"/><path d="M12 13V9.5M10 3h4"/>',
    load: '<path d="M12 3v8"/><path d="M7 6.5a7 7 0 1 0 10 0"/>',
    fairness: '<path d="M12 4v16M8 20h8M5 7h14"/><path d="m5 7-2.5 6a2.5 2.5 0 0 0 5 0L5 7zM19 7l-2.5 6a2.5 2.5 0 0 0 5 0L19 7z"/>',
  };

  const icon = (name) => `<svg class="method-icon" viewBox="0 0 24 24" aria-hidden="true">${glyphs[name]}</svg>`;
  const formula = (text, note = "") => `<div class="method-formula"><div class="method-formula-text">${text}</div>${note ? `<div class="method-formula-note">${note}</div>` : ""}</div>`;
  const rows = (items) => `<ul class="method-rows">${items.map(([title, text]) => `<li><span class="method-row-title">${title}</span><span class="method-row-text">${text}</span></li>`).join("")}</ul>`;
  const p = (text, cls = "") => `<p${cls ? ` class="${cls}"` : ""}>${text}</p>`;
  const subhead = (text) => `<h3 class="method-subhead">${text}</h3>`;

  let order = 0;
  const pane = (name, title, summary, body) => `
    <section class="method-pane" style="order: ${order++}" aria-labelledby="method-${name}">
      <header class="method-pane-head">
        ${icon(name)}
        <h2 id="method-${name}">${title}</h2>
        ${summary ? `<p class="method-summary">${summary}</p>` : ""}
      </header>
      <div class="method-pane-body">${body}</div>
    </section>`;

  // Two columns that stack on their own: a card sits right under the card above it in its
  // column, never under the taller card of the column beside it. Cards alternate between
  // the columns in reading order.
  const panes = [
    `${pane("decode", "Decode",
      "Decode is the speed at which tokens are generated after the first one.",
      [
        formula("(output tokens − 1) ÷ (latency − TTFT)", "The output tokens after the first, divided by the time from the first token to the last. TTFT is the time to first token, explained below."),
        p("The row shows the median of the measured requests, in tokens per second. Warm-up requests are not counted."),
      ].join(""))}`,
    `${pane("prefill", "Prefill",
      "Prefill is how fast the engine reads the prompt before the first token.",
      [
        formula("prompt tokens ÷ TTFT", "For each request."),
        subhead("This is only measured where it can be compared fairly"),
        rows([
          ["Single request at a time", "Under load, requests wait in a queue, so their prefill speed is not a property of the engine."],
          ["Cold cache", "A request that reuses cached prompt work would look faster, so every request has its own prefix and the engine's prompt cache is off. Each row records the cached-token count, and the row is marked unverified if that count is missing."],
          ["Prompt tokens", "Prompt tokens are what the engine actually processed, so engines that tokenize slightly differently are still compared by the work they did."],
        ]),
      ].join(""))}`,
    `${pane("ttft", "Time to first token",
      "How long you wait before the first word of the answer appears.",
      [
        formula("TTFT = first token received − request sent"),
        rows([
          ["Ollama", "Streams the answer over HTTP (/api/generate). The client stamps the first streamed chunk that carries a token."],
          ["llama.cpp, mlx-lm, Splash", "Stream over their OpenAI-compatible HTTP API (server-sent events). The client stamps the first chunk that carries a token."],
          ["pie", "Has no HTTP gateway: the client starts the program on pie over its websocket, and the program sends a t0 message the moment the first sampled token reaches it. The client stamps that message's arrival, so pie's TTFT includes the same round trip back to the client as the others'."],
          ["Speculative decoding", "A drafted row is timed the same way: the drafting program sends t0 after the prefill's token, before the first draft."],
          ["Inter-token latency", "ITL is the gap between consecutive tokens: the client's arrival stamps for HTTP engines, and the program's own per-token gaps after t0 for pie. A drafting round hands over its accepted tokens at once, so they arrive 0 ms apart."],
        ]),
      ].join(""))}`,
    `${pane("load", "Load time",
      "Load time is how long the engine takes to be ready to serve the model, in seconds.",
      [
        rows([
          ["Engines that run a server", "Ollama, llama.cpp, mlx-lm, Splash, pie: the time from starting the server until it answers."],
          ["Other engines", "The first run's extra time over the median run, which is the cost of the first call."],
        ]),
        p("Load time includes reading the weights from disk, so it depends on what the operating system has cached. Compare load times only on the same machine and after the same restart.", "method-footnote"),
      ].join(""))}`,
    `${pane("fairness", "Fairness",
      null,
      [
        rows([
          ["Same prompts", "The prompts for a workload are generated once with a fixed seed and stored with a checksum; every engine receives the same bytes."],
          ["Same settings", "The same max output tokens, temperature 0, concurrency and workload definition for every engine."],
          ["Same client and timer", "Every engine is driven by the same benchmark client, so TTFT and token timing are taken the same way."],
          ["Same comparison only", "Results are compared only for the same hardware, model and workload. Each release is pinned to one pie commit, and competitors run their newest release at that time."],
          ["Noise checks", "A row is marked noisy when repeated rounds vary by more than 5%, and each process runs a control check (A/A) that must agree with itself."],
          ["Failures stay visible", "A setup that did not run is kept with its reason, not dropped."],
        ]),
      ].join(""))}`
  ];
  const column = (side) => `<div class="method-col">${panes.filter((_, i) => i % 2 === side).join("")}</div>`;

  const content = `
    <header class="method-head">
      <h1>How we measure</h1>
      <p class="method-lede">Every number on this site comes from the same client, timer and prompts for every engine. These are the definitions.</p>
    </header>

    <div class="method-cols">${column(0)}${column(1)}</div>`;

  Pie.method = {
    element,
    render(state) {
      element.hidden = state.table !== "method";
      if (!element.hidden && element.dataset.ready !== "1") {
        element.innerHTML = `<div class="method-inner">${content}</div>`;
        element.dataset.ready = "1";
      }
    },
  };
})();
