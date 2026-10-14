window.Pie = window.Pie || {};

// Inferlets as a gallery that scales to many: category chips, search from the
// toolbar, and a dense grid of tiles tinted by category (as Shortcuts' gallery and the App Store browse).
(() => {
  const element = document.getElementById("inferlets");
  const esc = (s) => Pie.format.escape(String(s ?? ""));

  // a category's tint (a gradient) and glyph, drawn like SF Symbols: thin strokes, round caps
  const CATEGORIES = {
    speed: { label: "Speed", tint: ["#3b5bfd", "#a855f7"], glyph: '<path d="M4 17 9 12l3 3 8-8"/><path d="M15 7h5v5"/>' },
    memory: { label: "Memory", tint: ["#0ea5e9", "#22c55e"], glyph: '<rect x="4" y="5" width="16" height="4" rx="1.2"/><path d="M6 13h12M6 17h8"/>' },
    structure: { label: "Structure", tint: ["#6366f1", "#0ea5e9"], glyph: '<path d="M8 4c-2 0-2 2-2 4s-1.5 4-2 4c.5 0 2 1 2 4s0 4 2 4M16 4c2 0 2 2 2 4s1.5 4 2 4c-.5 0-2 1-2 4s0 4-2 4"/>' },
    sampling: { label: "Sampling", tint: ["#f97316", "#ec4899"], glyph: '<circle cx="7" cy="8" r="1.6"/><circle cx="16" cy="6" r="1.6"/><circle cx="12" cy="13" r="1.6"/><circle cx="6" cy="17" r="1.6"/><circle cx="17" cy="17" r="1.6"/>' },
    guidance: { label: "Guidance", tint: ["#f59e0b", "#ef4444"], glyph: '<circle cx="12" cy="12" r="8"/><path d="m15.5 8.5-2 5-5 2 2-5z"/>' },
    search: { label: "Search", tint: ["#14b8a6", "#6366f1"], glyph: '<circle cx="7" cy="5" r="2"/><circle cx="7" cy="19" r="2"/><circle cx="17" cy="12" r="2"/><path d="M7 7v10M7 9c0 3 4 3 8 3"/>' },
    watermark: { label: "Watermarks", tint: ["#64748b", "#334155"], glyph: '<path d="M12 3 5 6v5c0 4.5 3 8 7 10 4-2 7-5.5 7-10V6l-7-3z"/>' },
    media: { label: "Media", tint: ["#d946ef", "#8b5cf6"], glyph: '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3 16 5-5 4 4 3-3 6 6"/><circle cx="15.5" cy="9.5" r="1.4"/>' },
  };

  // pie's own example inferlets (pie-project/pie, examples/), each named for the work it does
  const CATALOG = [
    ["prefill-as-you-type", "Prefill as you type", "speed", "Chat · reads the prompt while it is typed", ""],
    ["dflash", "DFlash speculative decoding", "speed", "Long answers · drafts a block, checks it at once", "dflash-speculative-bench"],
    ["mtp", "Multi-token prediction", "speed", "Long answers · the model drafts its own next tokens", "mtp-speculative-decoding"],
    ["cacheback", "Cacheback speculation", "speed", "Repetitive text · drafts from what was already said", "cacheback-speculative-decoding"],
    ["constrained-spec", "Constrained speculation", "speed", "Structured output · drafts only allowed tokens", "constrained-speculative-decoding"],
    ["copy-on-write-fork", "Copy-on-write fork", "memory", "Agents · branches share the context they came from", "rs-fork-probe-py"],
    ["prefix-cache", "Prefix cache", "memory", "Shared system prompts · RAG", "prefix-tree-kv-cache"],
    ["attention-sink", "Attention sink", "memory", "Very long chats · memory stays flat", "attention-sink"],
    ["sliding-window", "Sliding window", "memory", "Long documents · keeps a recent window", "sliding-window-attention"],
    ["snapkv", "SnapKV eviction", "memory", "Long prompts · keeps the tokens that matter", "snapkv-eviction"],
    ["tova", "TOVA attention", "memory", "Long chats · drops the least attended tokens", "tova-attention"],
    ["h2o", "Heavy hitters (H2O)", "memory", "Long chats · keeps the most attended tokens", "trackb-h2o"],
    ["json-schema", "JSON schema decoding", "structure", "Tool calls · always valid JSON", "json-schema-constrained-decoding"],
    ["grammar", "Grammar-aligned decoding", "structure", "Code and DSLs · follows a grammar", "asap-grammar-aligned-decoding"],
    ["token-healing", "Token healing", "structure", "Completions · repairs a cut-off last token", "token-healing"],
    ["mirostat", "Mirostat v2", "sampling", "Creative writing · keeps surprise steady", "mirostat-v2-sampling"],
    ["typical", "Locally typical sampling", "sampling", "Natural prose · picks typical tokens", "locally-typical-sampling"],
    ["tail-free", "Tail-free sampling", "sampling", "Creative writing · trims the unlikely tail", "tail-free-sampling"],
    ["top-a", "Top-a sampling", "sampling", "Creative writing · cutoff that scales with confidence", "top-a-sampling"],
    ["eta", "Eta and epsilon sampling", "sampling", "Open-ended text · entropy-aware cutoff", "eta-epsilon-sampling"],
    ["xtc", "XTC sampling", "sampling", "Fiction · steers away from the obvious", "xtc-sampling"],
    ["entropy-temp", "Entropy-adaptive temperature", "sampling", "Chat · hotter when unsure, cooler when sure", "entropy-adaptive-temperature"],
    ["dry", "DRY repetition penalty", "sampling", "Long answers · stops repeated phrases", "dry-repetition-penalty"],
    ["repetition", "Repetition penalty", "sampling", "Long answers · discourages repeats", "repetition-penalty"],
    ["cfg", "Classifier-free guidance", "guidance", "Following instructions · amplifies the prompt", "classifier-free-guidance"],
    ["contrastive", "Contrastive decoding", "guidance", "Factual answers · contrasts a weaker model", "contrastive-decoding"],
    ["context-aware", "Context-aware decoding", "guidance", "RAG · leans on the given context", "context-aware-decoding"],
    ["consensus", "Consensus decoding", "guidance", "Reliable answers · agrees across samples", "consensus-decoding"],
    ["beam-search", "Beam search", "search", "Translation · keeps the best paths", "beam-search"],
    ["greenlist", "Greenlist watermark", "watermark", "Provenance · marks generated text", "greenlist-watermarking"],
    ["gumbel", "Gumbel watermark", "watermark", "Provenance · invisible, distortion-free mark", "gumbel-watermark"],
    ["synthid", "SynthID tournament", "watermark", "Provenance · tournament-sampled mark", "synthid-tournament-sampling"],
    ["captioning", "Image captioning", "media", "Vision · describes an image", "image-captioning"],
    ["text-to-image", "Text to image", "media", "Images · generates from a prompt", "text-to-image"],
    ["text-to-video", "Text to video", "media", "Video · generates from a prompt", "text-to-video"],
  ].map(([id, name, cat, workload, example]) => ({ id, name, cat, workload, example }));

  // the inferlets switched on and the chosen category, kept for this viewer
  const KEY = "pieInferlets";
  let added = new Set();
  let category = "all";
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

  const tint = (item) => { const t = CATEGORIES[item.cat].tint; return `--c1: ${t[0]}; --c2: ${t[1]}`; };
  const glyph = (item) => `<svg class="store-glyph" viewBox="0 0 24 24" aria-hidden="true">${CATEGORIES[item.cat].glyph}</svg>`;
  const toggle = (item) => `
    <label class="store-toggle" aria-label="Add ${esc(item.name)}">
      <input type="checkbox" role="switch" data-inferlet="${esc(item.id)}"${added.has(item.id) ? " checked" : ""}>
      <span class="store-switch" aria-hidden="true"></span>
    </label>`;
  const tile = (item) => `
    <li class="store-tile" style="${tint(item)}">
      <div class="store-tile-top">${glyph(item)}${toggle(item)}</div>
      <span class="store-name">${esc(item.name)}</span>
      <span class="store-workload">${esc(item.workload)}</span>
    </li>`;

  const shown = (query) => CATALOG
    .filter((item) => category === "all" || item.cat === category)
    .filter((item) => !query || `${item.name} ${item.workload} ${CATEGORIES[item.cat].label}`.toLowerCase().includes(query));

  const draw = (state) => {
    const query = state.query.trim().toLowerCase();
    const list = shown(query);
    const chips = [["all", "All", CATALOG.length], ...Object.entries(CATEGORIES).map(([id, c]) => [id, c.label, CATALOG.filter((i) => i.cat === id).length])];
    element.querySelector("#gal-chips").innerHTML = chips.map(([id, label, n]) =>
      `<button type="button" class="gal-chip${category === id ? " is-active" : ""}" data-category="${id}" aria-pressed="${category === id}">${esc(label)}<span>${n}</span></button>`).join("");
    element.querySelector("#gal-grid").innerHTML = list.length ? list.map(tile).join("")
      : `<li class="gal-empty">No inferlets match${query ? ` “${esc(query)}”` : ""}.</li>`;
  };

  const content = `
    <section class="store-shelf">
      <h2 class="store-shelf-title">My Inferlets</h2>
      <div class="term is-placeholder">
        <div class="term-bar"><span class="term-lights" aria-hidden="true"><i></i><i></i><i></i></span></div>
        <div class="term-body"><div class="term-out is-dim">The playground is in development.</div></div>
      </div>
    </section>
    <section class="store-shelf">
      <div class="gal-chips" id="gal-chips" role="group" aria-label="Categories"></div>
      <ul class="store-list gal-grid" id="gal-grid"></ul>
    </section>`;

  Pie.inferlets = {
    element,
    render(state) {
      element.hidden = state.table !== "inferlets";
      if (element.hidden) return;
      if (element.dataset.ready !== "1") {
        element.innerHTML = `<div class="method-inner">${content}</div>`;
        element.dataset.ready = "1";
        element.addEventListener("change", (event) => {
          const box = event.target.closest("[data-inferlet]");
          if (!box) return;
          if (box.checked) added.add(box.dataset.inferlet);
          else added.delete(box.dataset.inferlet);
          save();
        });
        element.addEventListener("click", (event) => {
          const chip = event.target.closest("[data-category]");
          if (!chip) return;
          category = chip.dataset.category;
          draw(state);
        });
      }
      draw(state);
    },
  };
})();
