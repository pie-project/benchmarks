window.Pie = window.Pie || {};

// The method page answers what a reader asks first: what each number measures (one request drawn as a timeline),
// which number matters for their work, what a cell in the tables means, how to run it themselves, and why it is fair.
(() => {
  const element = document.getElementById("method");

  // one request on a timeline: sent, the prompt read (prefill, ending at the first token), the answer streamed (decode)
  const timeline = `
    <figure class="mx-timeline" aria-label="One request: prefill until the first token, then decode">
      <svg viewBox="0 0 720 150" role="img">
        <line class="mx-axis" x1="30" y1="70" x2="700" y2="70"/>
        <rect class="mx-prefill" x="30" y="52" width="210" height="36" rx="8"/>
        <text class="mx-in" x="135" y="75" text-anchor="middle">Reads the prompt</text>
        ${Array.from({ length: 14 }, (_, i) => `<rect class="mx-token" x="${252 + i * 32}" y="56" width="24" height="28" rx="6"/>`).join("")}
        <text class="mx-in is-dark" x="474" y="104" text-anchor="middle">Streams the answer, one token at a time</text>
        <line class="mx-mark" x1="30" y1="34" x2="30" y2="106"/><text class="mx-label" x="30" y="24">Request sent</text>
        <line class="mx-mark is-first" x1="246" y1="34" x2="246" y2="106"/><text class="mx-label is-first" x="246" y="24" text-anchor="middle">First token</text>
        <line class="mx-mark" x1="700" y1="34" x2="700" y2="106"/><text class="mx-label" x="700" y="24" text-anchor="end">Last token</text>
        <path class="mx-brace" d="M30 124v6h216v-6"/><text class="mx-cap" x="138" y="146" text-anchor="middle">TTFT</text>
        <path class="mx-brace is-decode" d="M252 124v6h448v-6"/><text class="mx-cap" x="476" y="146" text-anchor="middle">Decode time</text>
      </svg>
    </figure>`;

  const metric = (name, tone, question, formula, feel) => `
    <div class="mx-metric ${tone}">
      <span class="mx-metric-name">${name}</span>
      <span class="mx-metric-q">${question}</span>
      <code>${formula}</code>
      <span class="mx-metric-feel">${feel}</span>
    </div>`;

  const uses = [
    ["Chatting", "Decode", "How fast the reply streams once it starts."],
    ["Pasting a long document or code", "Prefill · TTFT", "How long before the answer begins."],
    ["Coding agents and tool calls", "TTFT · Decode", "Many short turns: each waits for the first token, then streams."],
    ["Serving many users at once", "Throughput workload", "Tokens per second for each of 32 requests running together."],
  ];

  const commands = `<span class="mx-c"># set up the harness</span>
git clone https://github.com/pie-project/pie-evals && cd pie-evals
uv venv && uv pip install -e ".[orchestrate]"

<span class="mx-c"># plan the Mac cells for a pie commit, run them, then import the results</span>
.venv/bin/pie-evals jobs --tier targeted --pie-commit &lt;sha&gt; --platform m5-max-64g --out jobs
.venv/bin/pie-evals-node run --job jobs/&lt;job&gt;.json --out out/&lt;job&gt; --download
.venv/bin/pie-evals collect --tier targeted out/&lt;job&gt;`;

  const fair = [
    ["Same prompts", "Generated once from a fixed seed and checksummed; every engine gets the same bytes."],
    ["One Mac, one engine at a time", "A lock keeps any other benchmark off the machine while a cell runs."],
    ["Cold cache", "Each prompt is unique and prompt caching is off, so prefill is never a cache hit."],
    ["Same output", "Greedy sampling and the same output length for every engine."],
  ];

  const content = `
    <header class="method-head mx-head">
      <h1>How we measure</h1>
      <p class="method-lede">What each number means, which one matters for your work, and how to check it yourself.</p>
    </header>

    <section class="mx-section">
      <h2>What the numbers measure</h2>
      <p class="mx-lede">Every number comes from timing real requests. Here is one of them.</p>
      ${timeline}
      <div class="mx-metrics">
        ${metric("TTFT", "is-ttft", "How long until the answer starts?", "first token − request sent", "Lower is better. What a short prompt feels like.")}
        ${metric("Prefill", "is-prefill", "How fast is the prompt read?", "prompt tokens ÷ TTFT", "Higher is better. What long prompts feel like.")}
        ${metric("Decode", "is-decode", "How fast does the answer stream?", "(output tokens − 1) ÷ decode time", "Higher is better. What a long answer feels like.")}
      </div>
      <p class="mx-note">Single request: a 512-token prompt and a 256-token answer, the median of 8 requests after a warm-up.</p>
    </section>

    <section class="mx-section">
      <h2>Which number matters for you</h2>
      <div class="mx-table" role="table">
        ${uses.map(([use, number, why]) => `<div class="mx-tr" role="row"><span class="mx-use" role="cell">${use}</span><span class="mx-num" role="cell">${number}</span><span class="mx-why" role="cell">${why}</span></div>`).join("")}
      </div>
    </section>

    <section class="mx-section">
      <h2>Reading a cell</h2>
      <div class="mx-cell-demo">
        <div class="mx-cell-sample"><span class="mx-sample is-behind">↓ 21%</span><span class="mx-sample-meta">Qwen3.6-35B-A3B · M5 Max 128 GB · Decode</span></div>
        <div class="mx-cell-explain">
          <p>pie against the <b>fastest other engine</b> on that Mac, for that model.</p>
          <code>pie ÷ fastest other − 1</code>
          <p>Green and ↑ when pie is faster, red and ↓ when it is slower, ≈ within 2%. For TTFT, faster means it answers sooner. Hover a cell for every engine's number.</p>
        </div>
      </div>
    </section>

    <section class="mx-section">
      <h2>Run it yourself</h2>
      <pre class="mx-code"><code>${commands}</code></pre>
      <p class="mx-note">Needs a Mac on AC power with Rust and uv. llama.cpp, mlx-lm and Splash are fetched at the versions the results name.</p>
    </section>

    <section class="mx-section">
      <h2>Fair by construction</h2>
      <div class="mx-fair">${fair.map(([title, text]) => `<div class="mx-fair-item"><b>${title}</b><span>${text}</span></div>`).join("")}</div>
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
