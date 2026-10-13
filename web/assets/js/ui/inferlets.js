window.Pie = window.Pie || {};

// Inferlets, laid out like an app store: two featured programs on the welcome banner's gradients,
// then a shelf of the rest. Each names the work it is for and what it buys.
(() => {
  const element = document.getElementById("inferlets");
  const esc = (s) => Pie.format.escape(String(s ?? ""));
  const REPO = "https://github.com/pie-project/pie/tree/main/examples/";

  // icon glyphs, drawn like SF Symbols: thin strokes, round caps
  const GLYPH = {
    type: '<path d="M4 7h16M4 12h10M4 17h7"/><path d="M18 14v6"/>',
    fork: '<circle cx="7" cy="5" r="2"/><circle cx="7" cy="19" r="2"/><circle cx="17" cy="12" r="2"/><path d="M7 7v10M7 9c0 3 4 3 8 3"/>',
    draft: '<path d="M4 17 9 12l3 3 8-8"/><path d="M15 7h5v5"/>',
    prefix: '<rect x="4" y="5" width="16" height="4" rx="1.2"/><path d="M6 13h12M6 17h8"/>',
    json: '<path d="M8 4c-2 0-2 2-2 4s-1.5 4-2 4c.5 0 2 1 2 4s0 4 2 4M16 4c2 0 2 2 2 4s1.5 4 2 4c-.5 0-2 1-2 4s0 4-2 4"/>',
    sink: '<path d="M4 12h3l2-5 3 10 2-5h6"/>',
  };
  const icon = (kind, glyph, size = "") => `<span class="store-icon ${kind}${size}" aria-hidden="true"><svg viewBox="0 0 24 24">${GLYPH[glyph]}</svg></span>`;

  const featured = [
    {
      kind: "is-prefill", glyph: "type", kicker: "New way to chat", name: "Prefill as you type",
      title: "The answer starts before you press Enter.",
      body: "Reads the prompt while it is still being typed, so the only work left at Enter is the last few words.",
      stat: "~0 ms", statLabel: "time to first token after Enter", preview: true, example: "",
    },
    {
      kind: "is-prefix", glyph: "fork", kicker: "Built for agents", name: "Copy-on-write fork",
      title: "Branch a conversation without copying it.",
      body: "Every branch shares the cached context it came from and only stores what it adds, so an agent can try many paths at once.",
      stat: "8 branches", statLabel: "for the memory of about one", preview: true, example: "rs-fork-probe-py",
    },
  ];

  const shelf = [
    { kind: "is-speculative", glyph: "draft", name: "Speculative decoding", workload: "Chat · long answers",
      benefit: "A drafter proposes tokens and the model checks them in one pass.", stat: "1.5× decode",
      note: "Measured: Qwen3.8-27B on M5 Max 128 GB, against plain decoding", preview: false, example: "dflash-speculative-bench" },
    { kind: "is-prefix", glyph: "prefix", name: "Prefix cache", workload: "Shared system prompts · RAG",
      benefit: "A prompt many requests share is read once.", stat: "10× prefill", preview: true, example: "prefix-tree-kv-cache" },
    { kind: "is-tools", glyph: "json", name: "JSON schema decoding", workload: "Tool calls · structured output",
      benefit: "Only tokens the schema allows can be sampled.", stat: "100% valid", preview: true, example: "json-schema-constrained-decoding" },
    { kind: "is-sink", glyph: "sink", name: "Attention sink", workload: "Very long chats",
      benefit: "Keeps the first tokens and a recent window, so memory stays flat.", stat: "Flat memory", preview: true, example: "attention-sink" },
  ];

  const get = (item) => item.example
    ? `<a class="store-get" href="${REPO}${esc(item.example)}" target="_blank" rel="noopener">Get</a>`
    : `<span class="store-get is-soon">Soon</span>`;

  const feature = (item) => `
    <article class="store-feature ${item.kind}">
      <p class="store-kicker">${esc(item.kicker)}</p>
      <h2>${esc(item.title)}</h2>
      <p class="store-body">${esc(item.body)}</p>
      <div class="store-stat"><b>${esc(item.stat)}</b><span>${esc(item.statLabel)}</span></div>
      <div class="store-app">${icon(item.kind, item.glyph)}<span class="store-app-name">${esc(item.name)}</span>${get(item)}</div>
    </article>`;

  const row = (item) => `
    <li class="store-row">
      ${icon(item.kind, item.glyph, " is-large")}
      <div class="store-text">
        <span class="store-name">${esc(item.name)}</span>
        <span class="store-workload">${esc(item.workload)}</span>
        <span class="store-benefit">${esc(item.benefit)}</span>
      </div>
      <div class="store-side">
        <span class="store-chip"${item.note ? ` title="${esc(item.note)}"` : ""}>${esc(item.stat)}</span>
        ${get(item)}
      </div>
    </li>`;

  const content = `
    <header class="method-head store-head">
      <h1>Inferlet Marketplace</h1>
      <p class="method-lede">Programs that run on pie, each made for one kind of work.</p>
    </header>
    <div class="store-features">${featured.map(feature).join("")}</div>
    <section class="store-shelf">
      <h2 class="store-shelf-title">More inferlets</h2>
      <ul class="store-list">${shelf.map(row).join("")}</ul>
    </section>`;

  Pie.inferlets = {
    element,
    render(state) {
      element.hidden = state.table !== "inferlets";
      if (!element.hidden && element.dataset.ready !== "1") {
        element.innerHTML = `<div class="method-inner">${content}</div>`;
        element.dataset.ready = "1";
      }
    },
  };
})();
