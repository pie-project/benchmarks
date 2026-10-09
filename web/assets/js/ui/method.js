window.Pie = window.Pie || {};

(() => {
  const element = document.getElementById("method");

  // one System Settings style pane per topic: icon tile, title, a plain sentence, the definition, then details
  const glyphs = {
    decode: '<path d="M4 17a8 8 0 1 1 16 0"/><path d="m12 17 4-5"/>',
    prefill: '<path d="M5 6h14M5 10h14M5 14h9"/><path d="m16 17 2 2 3-4"/>',
    ttft: '<circle cx="12" cy="13" r="7"/><path d="M12 13V9.5M10 3h4"/>',
    load: '<path d="M12 3v8"/><path d="M7 6.5a7 7 0 1 0 10 0"/>',
    fairness: '<path d="M12 4v16M8 20h8M5 7h14"/><path d="m5 7-2.5 6a2.5 2.5 0 0 0 5 0L5 7zM19 7l-2.5 6a2.5 2.5 0 0 0 5 0L19 7z"/>',
  };

  const tile = (name) => `<span class="method-tile method-tile-${name}"><svg viewBox="0 0 24 24" aria-hidden="true">${glyphs[name]}</svg></span>`;
  const formula = (text, note = "") => `<div class="method-formula"><div class="method-formula-text">${text}</div>${note ? `<div class="method-formula-note">${note}</div>` : ""}</div>`;
  const rows = (items) => `<ul class="method-rows">${items.map(([title, text]) => `<li><span class="method-row-title">${title}</span><span class="method-row-text">${text}</span></li>`).join("")}</ul>`;
  const p = (text, cls = "") => `<p${cls ? ` class="${cls}"` : ""}>${text}</p>`;
  const subhead = (text) => `<h3 class="method-subhead">${text}</h3>`;

  const pane = (name, title, summary, body) => `
    <section class="method-pane" aria-labelledby="method-${name}">
      <header class="method-pane-head">
        ${tile(name)}
        <div>
          <h2 id="method-${name}">${title}</h2>
          <p class="method-summary">${summary}</p>
        </div>
      </header>
      <div class="method-pane-body">${body}</div>
    </section>`;

  const content = `
    <header class="method-head">
      <h1>How we measure</h1>
      <p class="method-lede">Every number on this site comes from the same client, timer and prompts for every engine. These are the definitions.</p>
    </header>

    ${pane("decode", "Decode",
      "Decode is the speed at which tokens are generated after the first one.",
      [
        formula("(output tokens − 1) ÷ (latency − TTFT)", "The output tokens after the first, divided by the time from the first token to the last. TTFT is the time to first token, explained below."),
        p("The row shows the median of the measured requests, in tokens per second. Warm-up requests are not counted."),
      ].join(""))}

    ${pane("prefill", "Prefill",
      "Prefill is how fast the engine reads the prompt before the first token.",
      [
        formula("prompt tokens ÷ TTFT", "For each request."),
        subhead("This is only measured where it can be compared fairly"),
        rows([
          ["Single request at a time", "Under load, requests wait in a queue, so their prefill speed is not a property of the engine."],
          ["Cold cache", "A request that reuses cached prompt work would look faster, so every request has its own prefix and the engine's prompt cache is off. Each row records the cached-token count, and the row is marked unverified if that count is missing."],
          ["Prompt tokens", "Prompt tokens are what the engine actually processed, so engines that tokenize slightly differently are still compared by the work they did."],
        ]),
        p("Prefill rows measured before the cold-cache setup were built with a different definition and are being re-measured.", "method-footnote"),
      ].join(""))}

    ${pane("ttft", "Time to first token",
      "How long you wait before the first word of the answer appears.",
      [
        formula("TTFT = first generated token − request sent", "Measured on the client."),
        rows([
          ["Inter-token latency", "ITL is the gap between consecutive tokens."],
        ]),
      ].join(""))}

    ${pane("load", "Load time",
      "Load time is how long the engine takes to be ready to serve the model, in seconds.",
      [
        rows([
          ["Engines that run a server", "Ollama, llama.cpp, mlx-lm, Splash, pie: the time from starting the server until it answers."],
          ["Other engines", "The first run's extra time over the median run, which is the cost of the first call."],
        ]),
        p("Load time includes reading the weights from disk, so it depends on what the operating system has cached. Compare load times only on the same machine and after the same restart.", "method-footnote"),
      ].join(""))}

    ${pane("fairness", "Fairness",
      "Every engine gets the same work, measured the same way.",
      [
        formula("same prompts · same settings · same client and timer"),
        rows([
          ["Same prompts", "The prompts for a workload are generated once with a fixed seed and stored with a checksum; every engine receives the same bytes."],
          ["Same settings", "The same max output tokens, temperature 0, concurrency and workload definition for every engine."],
          ["Same client and timer", "Every engine is driven by the same benchmark client, so TTFT and token timing are taken the same way."],
          ["Same comparison only", "Results are compared only for the same hardware, model and workload. Each release is pinned to one pie commit, and competitors run their newest release at that time."],
          ["Noise checks", "A row is marked noisy when repeated rounds vary by more than 5%, and each process runs a control check (A/A) that must agree with itself."],
          ["Failures stay visible", "A setup that did not run is kept with its reason, not dropped."],
        ]),
      ].join(""))}`;

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
