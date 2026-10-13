window.Pie = window.Pie || {};

// The method page: the three formulas, and how each engine's first and last token are timed.
(() => {
  const element = document.getElementById("method");

  // how each engine is timed: one client, one clock; only the signal for the first token differs
  const engines = [
    ["pie", "The client starts the benchmark program on pie over a WebSocket. The program sends a <code>t0</code> message the moment it samples the first token; the client stamps its arrival, so the round trip back counts as it does for the others. With drafting, <code>t0</code> is sent before the first draft.",
      "The client stamps the program's last token message."],
    ["llama.cpp", "Streams over its OpenAI-compatible HTTP API. The client stamps the first streamed chunk that carries a token.", "The client stamps the last streamed chunk."],
    ["mlx-lm", "Streams over its OpenAI-compatible HTTP API. The client stamps the first streamed chunk that carries a token.", "The client stamps the last streamed chunk."],
    ["Splash", "Streams over its OpenAI-compatible HTTP API. The client stamps the first streamed chunk that carries a token.", "The client stamps the last streamed chunk."],
  ];

  const content = `
    <header class="method-head mx-head">
      <h1>How we measure</h1>
      <p class="method-lede">One benchmark client times every engine with the same clock. Only how the first token is signalled differs.</p>
    </header>
    <section class="mx-section">
      <div class="mx-formulas">
        <span><b>TTFT</b><code>first token received − request sent</code></span>
        <span><b>Prefill</b><code>prompt tokens ÷ TTFT</code></span>
        <span><b>Decode</b><code>(output tokens − 1) ÷ (last token − first token)</code></span>
      </div>
      <div class="mx-table mx-engines" role="table">
        <div class="mx-tr is-head" role="row"><span role="columnheader">Engine</span><span role="columnheader">First token · TTFT and prefill</span><span role="columnheader">Last token · decode</span></div>
        ${engines.map(([name, first, last]) => `<div class="mx-tr" role="row"><span class="mx-use" role="rowheader">${name}</span><span class="mx-why" role="cell">${first}</span><span class="mx-why" role="cell">${last}</span></div>`).join("")}
      </div>
      <p class="mx-note">Single request: a 512-token prompt and a 256-token answer; each row is the median of the measured requests, warm-up excluded.</p>
    </section>`;

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
