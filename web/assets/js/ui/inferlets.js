window.Pie = window.Pie || {};

// Inferlets, laid out like an app store: a shelf of programs. Each names the work it is for and what it buys.
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


  const shelf = [
    { id: "prefill-as-you-type", kind: "is-prefill", glyph: "type", name: "Prefill as you type", workload: "Chat",
      benefit: "Reads the prompt while it is typed, so the answer starts at Enter.", stat: "~0 ms TTFT", example: "" },
    { id: "copy-on-write-fork", kind: "is-prefix", glyph: "fork", name: "Copy-on-write fork", workload: "Agents",
      benefit: "Branches share the context they came from and store only what they add.", stat: "8 branches", example: "rs-fork-probe-py" },
    { id: "speculative-decoding", kind: "is-speculative", glyph: "draft", name: "Speculative decoding", workload: "Chat · long answers",
      benefit: "A drafter proposes tokens and the model checks them in one pass.", stat: "1.5× decode",
      note: "Measured: Qwen3.8-27B on M5 Max 128 GB, against plain decoding", preview: false, example: "dflash-speculative-bench" },
    { id: "prefix-cache", kind: "is-prefix", glyph: "prefix", name: "Prefix cache", workload: "Shared system prompts · RAG",
      benefit: "A prompt many requests share is read once.", stat: "10× prefill", preview: true, example: "prefix-tree-kv-cache" },
    { id: "json-schema", kind: "is-tools", glyph: "json", name: "JSON schema decoding", workload: "Tool calls · structured output",
      benefit: "Only tokens the schema allows can be sampled.", stat: "100% valid", preview: true, example: "json-schema-constrained-decoding" },
    { id: "attention-sink", kind: "is-sink", glyph: "sink", name: "Attention sink", workload: "Very long chats",
      benefit: "Keeps the first tokens and a recent window, so memory stays flat.", stat: "Flat memory", preview: true, example: "attention-sink" },
  ];

  // the inferlets switched on, kept for this viewer: they are what the playground below can run
  const KEY = "pieInferlets";
  let added = new Set();
  try {
    added = new Set(JSON.parse(localStorage.getItem(KEY) || "[]"));
  } catch {
    // storage refused: start with none
  }
  const save = () => {
    try {
      localStorage.setItem(KEY, JSON.stringify([...added]));
    } catch {
      // private windows can refuse storage
    }
  };
  const all = () => shelf;
  const toggle = (item, label = "") => `
    <label class="store-toggle">${label ? `<span>${label}</span>` : ""}
      <input type="checkbox" role="switch" data-inferlet="${esc(item.id)}"${added.has(item.id) ? " checked" : ""}>
      <span class="store-switch" aria-hidden="true"></span>
    </label>`;


  // a tile in a full-width grid: icon and switch on top, then the name, the workload and the figure
  const row = (item) => `
    <li class="store-tile" title="${esc(item.benefit)}">
      <div class="store-tile-top">${icon(item.kind, item.glyph)}${toggle(item)}</div>
      <span class="store-name">${esc(item.name)}</span>
      <span class="store-workload">${esc(item.workload)}</span>
    </li>`;

  const content = `
    <header class="method-head store-head">
      <h1>Marketplace</h1>
      <p class="welcome-tagline">Inferlets</p>
    </header>
    <section class="store-shelf">
      <ul class="store-list">${shelf.map(row).join("")}</ul>
    </section>
    <section class="store-shelf">
      <h2 class="store-shelf-title">Playground</h2>
      <div class="term is-placeholder">
        <div class="term-bar"><span class="term-lights" aria-hidden="true"><i></i><i></i><i></i></span></div>
        <div class="term-body"><div class="term-out is-dim">The playground is in development. Soon you can try the inferlets you switch on right here.</div></div>
      </div>
    </section>`;

  // the switches are remembered for this viewer; the playground that will run them is in development
  const remember = () => element.addEventListener("change", (event) => {
    const box = event.target.closest("[data-inferlet]");
    if (!box) return;
    if (box.checked) added.add(box.dataset.inferlet);
    else added.delete(box.dataset.inferlet);
    save();
  });

  Pie.inferlets = {
    element,
    render(state) {
      element.hidden = state.table !== "inferlets";
      if (!element.hidden && element.dataset.ready !== "1") {
        element.innerHTML = `<div class="method-inner">${content}</div>`;
        element.dataset.ready = "1";
        remember();
      }
    },
  };
})();
