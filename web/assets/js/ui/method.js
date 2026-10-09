window.Pie = window.Pie || {};

(() => {
  const element = document.getElementById("method");

  const section = (title, body) => `<section class="method-section"><h2>${title}</h2>${body}</section>`;
  const p = (text) => `<p>${text}</p>`;
  const list = (items) => `<ul>${items.map((item) => `<li>${item}</li>`).join("")}</ul>`;

  const content = `
    <header class="method-head">
      <h1>How we measure</h1>
      <p class="method-lede">Every number on this site comes from the same client, timer and prompts for every engine. These are the definitions.</p>
    </header>
    ${section("Decode", [
      p("Decode is the speed at which tokens are generated after the first one. For each request we take the output tokens after the first, divided by the time from the first token to the last: (output tokens − 1) ÷ (latency − TTFT)."),
      p("The row shows the median of the measured requests, in tokens per second. Warm-up requests are not counted."),
    ].join(""))}
    ${section("Prefill", [
      p("Prefill is how fast the engine reads the prompt before the first token. For each request: prompt tokens ÷ TTFT."),
      p("This is only measured where it can be compared fairly:"),
      list([
        "Single request at a time. Under load, requests wait in a queue, so their prefill speed is not a property of the engine.",
        "Cold cache. A request that reuses cached prompt work would look faster, so every request has its own prefix and the engine's prompt cache is off. Each row records the cached-token count, and the row is marked unverified if that count is missing.",
        "Prompt tokens are what the engine actually processed, so engines that tokenize slightly differently are still compared by the work they did.",
      ]),
      p("Prefill rows measured before the cold-cache setup were built with a different definition and are being re-measured."),
    ].join(""))}
    ${section("TTFT and inter-token latency", [
      p("TTFT is the time from sending a request to receiving its first generated token, measured on the client. Inter-token latency (ITL) is the gap between consecutive tokens."),
    ].join(""))}
    ${section("Load time", [
      p("Load time is how long the engine takes to be ready to serve the model, in seconds."),
      list([
        "Engines that run a server (Ollama, llama.cpp, mlx-lm, Splash, pie): the time from starting the server until it answers.",
        "Other engines: the first run's extra time over the median run, which is the cost of the first call.",
      ]),
      p("Load time includes reading the weights from disk, so it depends on what the operating system has cached. Compare load times only on the same machine and after the same restart."),
    ].join(""))}
    ${section("Fairness", [
      list([
        "Same prompts: the prompts for a workload are generated once with a fixed seed and stored with a checksum; every engine receives the same bytes.",
        "Same settings: the same max output tokens, temperature 0, concurrency and workload definition for every engine.",
        "Same client and timer: every engine is driven by the same benchmark client, so TTFT and token timing are taken the same way.",
        "Same comparison only: results are compared only for the same hardware, model and workload. Each release is pinned to one pie commit, and competitors run their newest release at that time.",
        "Noise checks: a row is marked noisy when repeated rounds vary by more than 5%, and each process runs a control check (A/A) that must agree with itself.",
        "Failures stay visible: a setup that did not run is kept with its reason, not dropped.",
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
