window.Pie = window.Pie || {};

(() => {
  const element = document.getElementById("inferlets");

  // Each demo card names what the inferlet does and only claims what the results can show.
  // Anything still being measured says so in its status line.
  const demos = [
    {
      kind: "is-speculative",
      label: "Speculative decoding",
      title: "Draft ahead, verify in one pass.",
      body: "A drafter proposes a block of tokens and the target model checks them together, so several tokens can land per step. Runs as the dflash-speculative-bench inferlet.",
      status: "Decode speedup in progress on Apple Silicon. Not yet stable on every prompt length.",
      cta: "See the method",
      go: "method",
    },
    {
      kind: "is-prefix",
      label: "Prefix caching",
      title: "Share the prompt, pay for it once.",
      body: "Requests that start with the same system prompt or document reuse one cached prefix instead of recomputing it. Runs as the prefix-tree-kv-cache inferlet.",
      status: "Workload defined in the suite. No published results yet.",
      cta: "See the results",
      go: "results",
    },
    {
      kind: "is-prefill",
      label: "Long-context prefill",
      title: "Long prompts without the wait.",
      body: "Prefill for prompts from 2k to 32k tokens, measured as time to first token against the other engines. Runs as the prefill-rows inferlet.",
      status: "Prefill shapes defined in the suite. No published results yet.",
      cta: "See the results",
      go: "results",
    },
  ];

  const offers = [
    {
      title: "Private cloud deployment",
      body: "Run pie on your own cloud account or on-prem GPUs. Prompts and weights stay inside your network.",
    },
    {
      title: "Constrained decoding, built with us",
      body: "We build a constrained-decoding inferlet for your grammar or JSON schema and benchmark it on your model before you commit.",
    },
    {
      title: "Benchmark pilot",
      body: "We measure pie against your current engine on your model and hardware, and share the full method so you can check it.",
    },
    {
      title: "Dedicated GPU endpoints",
      body: "Reserved GPU capacity for your inferlets, with monitoring and a named engineer for support.",
    },
  ];

  const card = (demo) => `
    <article class="inferlet-card ${demo.kind}">
      <div>
        <p class="inferlet-kicker">${demo.label}</p>
        <h2>${demo.title}</h2>
        <p>${demo.body}</p>
        <span class="inferlet-status">${demo.status}</span>
      </div>
      <button class="inferlet-link" type="button" data-go="${demo.go}">${demo.cta}</button>
    </article>`;

  const offer = (item) => `
    <div class="enterprise-card">
      <h3>${item.title}</h3>
      <p>${item.body}</p>
      <a href="https://github.com/pie-project/pie-evals/issues/new" target="_blank" rel="noopener">Get in touch</a>
    </div>`;

  const content = `
    <header class="method-head">
      <h1>Inferlets</h1>
      <p class="method-lede">Programs that run on pie. Each one is a demo you can try, measure and build on.</p>
    </header>
    <div class="inferlet-grid">${demos.map(card).join("")}</div>
    <header class="enterprise-head">
      <h2>For cloud and enterprise teams</h2>
      <p>Pie is open source. We work with teams that want it in production: deployment, custom inferlets and support.</p>
    </header>
    <div class="enterprise-grid">${offers.map(offer).join("")}</div>`;

  Pie.inferlets = {
    element,
    render(state) {
      element.hidden = state.table !== "inferlets";
      if (!element.hidden && element.dataset.ready !== "1") {
        element.innerHTML = `<div class="method-inner">${content}</div>`;
        // each card's button opens the page it names, as the sidebar item does
        element.querySelectorAll("[data-go]").forEach((button) =>
          button.addEventListener("click", (event) =>
            document.querySelector(`.sidebar-item[data-table="${event.currentTarget.dataset.go}"]`)?.click()));
        element.dataset.ready = "1";
      }
    },
  };
})();
