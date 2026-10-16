window.Pie = window.Pie || {};

// The methodology page: what each workload is, how one request is timed, how rounds become a cell, and what is still open.
(() => {
  const element = document.getElementById("methodology");

  const rows = (items) => `<ul class="method-rows">${items.map(([title, text]) =>
    `<li><span class="method-row-title">${title}</span><span class="method-row-text">${text}</span></li>`).join("")}</ul>`;
  const formula = (text) => `<div class="method-formula"><span class="method-formula-text">${text}</span></div>`;
  const pane = (title, summary, body) => `
    <section class="method-pane">
      <h2>${title}</h2>
      <p class="method-summary">${summary}</p>
      <div class="method-pane-body">${body}</div>
    </section>`;

  const workloads = pane("Workloads", "Every engine runs the same three shapes on the same Mac.", rows([
    ["Single stream", "About 555 prompt tokens in, at most 256 out. Eight measured requests, one at a time. Gives prefill, decode and TTFT."],
    ["Throughput", "128 requests, 32 in flight, about 128 tokens in and at most 128 out. Gives output tokens per second."],
    ["Control A/A", "pie only. A short repeat run that checks the process is quiet before its numbers count."],
  ]));

  const equal = pane("Held equal", "What every engine gets, so only the engine differs.", rows([
    ["Sampling", "Greedy (temperature 0), thinking off, the same system prompt and chat template."],
    ["Cold prompts", "Each request carries a unique tag, so no engine can reuse a cached prefix. Prefix caches are off, and every engine gets the same prompts."],
    ["Warmup", "Two requests on other prompts before measuring, to absorb compilation and first-touch costs."],
    ["Output length", "Every engine stops where the model ends its answer; the length is a cap."],
  ]));

  const clock = pane("The clock", "One request, as the benchmark client sees it.", `
    <div class="method-timeline" aria-label="Send, then TTFT until the first token, then the decode window until the stream closes">
      <span class="is-ttft">TTFT</span><span class="is-decode">decode window</span>
    </div>
    <div class="method-timeline-marks"><span>request sent</span><span>first token</span><span>stream closes</span></div>
    ${formula('prefill <span class="op">=</span> prompt tokens <span class="op">÷</span> TTFT')}
    ${formula('decode <span class="op">=</span> (output tokens <span class="op">−</span> 1) <span class="op">÷</span> (end <span class="op">−</span> TTFT)')}
    ${formula('throughput <span class="op">=</span> all output tokens <span class="op">÷</span> wall time')}
    <p>Each single-stream number is the median over the measured requests. TTFT includes request handling, tokenization and scheduling, so prefill reads slightly below the raw kernel rate for every engine.</p>`);

  const rounds = pane("Rounds", "How repeated runs become one row.", rows([
    ["Three rounds", "Single stream runs three rounds. If they spread by more than 2%, up to two more run and the last three are kept."],
    ["The median round", "The row is the whole round whose decode is the median, so its prefill and TTFT come from that round too."],
    ["Noisy", "A row still spreading over 2% (5% for throughput) is marked noisy."],
  ]));

  const machine = pane("The machine", "Checks before every test, so nothing else shares the GPU.", rows([
    ["One job per Mac", "A machine lock keeps two benchmark jobs from running at once."],
    ["Idle GPU", "The GPU must stay at or under 5% for 10 seconds before a test starts, otherwise the test gives no numbers."],
    ["Cool-down", "Before single stream, the Mac idles 60 seconds and waits for a nominal thermal state."],
  ]));

  const cell = pane("Reading a cell", "The percentage on a platform page.", `
    ${formula('gain <span class="op">=</span> pie <span class="op">÷</span> best other engine <span class="op">−</span> 1')}
    ${rows([
      ["Per cell", "For one Mac, one model and one metric, against whichever other engine is fastest there."],
      ["Even", "Under 4.5% either way is shown in grey: within run-to-run spread."],
      ["Overall", "A Mac’s overall number is the median gain across its models."],
    ])}`);

  const open = pane("Known limitations", "What the numbers do not yet control.", rows([
    ["pie restarts each round", "pie’s server starts fresh every round, while the other servers stay warm."],
    ["Engines run in sequence", "Engines are not interleaved, so heat and time differ slightly between them. Quick reruns of named models skip the cool-down."],
    ["Decode ends at stream close", "End-of-request overhead is counted as decode time."],
    ["Output length not compared", "Engines may stop at different lengths for the same prompt."],
    ["Speculation", "Splash always drafts with its own model; pie drafts only on DFlash rows; mlx-lm and llama.cpp do not draft."],
    ["Load time", "Measured but not shown: a server can report ready before its weights are resident."],
  ]));

  const content = `
    <header class="method-head">
      <h1>Methodology</h1>
      <p class="method-lede">How every number on this site is measured, and what the measurement does not yet capture.</p>
    </header>
    <div class="method-cols">
      <div class="method-col">${workloads}${clock}${machine}</div>
      <div class="method-col">${equal}${rounds}${cell}</div>
    </div>
    ${open}`;

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
