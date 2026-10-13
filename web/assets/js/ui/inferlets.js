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
    <label class="store-toggle"${item.example ? "" : ' title="Not available yet"'}>${label ? `<span>${label}</span>` : ""}
      <input type="checkbox" role="switch" data-inferlet="${esc(item.id)}"${added.has(item.id) ? " checked" : ""}${item.example ? "" : " disabled"}>
      <span class="store-switch" aria-hidden="true"></span>
    </label>`;


  // an App Store row: icon, a name over one quiet line (workload · what it buys), one control on the right
  const row = (item) => `
    <li class="store-row" title="${esc(item.benefit)}">
      ${icon(item.kind, item.glyph, " is-large")}
      <div class="store-text">
        <span class="store-name">${esc(item.name)}</span>
        <span class="store-workload">${esc(item.workload)} · <b>${esc(item.stat)}</b></span>
      </div>
      ${item.example ? toggle(item) : '<span class="store-soon">Soon</span>'}
    </li>`;

  const content = `
    <header class="method-head store-head">
      <h1>Inferlet Marketplace</h1>
    </header>
    <section class="store-shelf">
      <ul class="store-list">${shelf.map(row).join("")}</ul>
    </section>
    <section class="store-shelf">
      <h2 class="store-shelf-title">Playground</h2>
      <div class="term" id="term">
        <div class="term-bar"><span class="term-lights" aria-hidden="true"><i></i><i></i><i></i></span></div>
        <div class="term-body" id="term-body"></div>
        <label class="term-line"><span class="term-prompt">pie&gt;</span><input id="term-input" type="text" autocomplete="off" spellcheck="false" aria-label="Playground command"></label>
      </div>
    </section>`;

  // the playground: a terminal over the inferlets switched on. The site has no engine to run them on,
  // so `run` writes the commands that run one on your own machine.
  const playground = () => {
    const body = element.querySelector("#term-body");
    const input = element.querySelector("#term-input");
    const print = (text, cls = "") => {
      const line = document.createElement("div");
      line.className = `term-out ${cls}`;
      line.textContent = text;
      body.append(line);
      body.scrollTop = body.scrollHeight;
    };
    const byId = (id) => all().find((item) => item.id === id);
    const help = () => print([
      "help                      show these commands",
      "ls                        inferlets added to the playground",
      'run <inferlet> "prompt"   the commands that run it on your Mac',
      "clear                     clear the window",
    ].join("\n"), "is-dim");
    const ls = () => {
      const list = [...added].map(byId).filter(Boolean);
      print(list.length ? list.map((item) => `${item.id.padEnd(26)}${item.name}`).join("\n") : "No inferlets yet. Switch one on above.", list.length ? "" : "is-dim");
    };
    const run = (args) => {
      const match = /^(\S+)\s*(?:"([^"]*)"|(.*))?$/.exec(args.trim());
      const item = match && byId(match[1]);
      if (!item) return print(`Unknown inferlet: ${args.trim().split(/\s+/)[0] || "(none)"}. Try ls.`, "is-error");
      if (!added.has(item.id)) return print(`${item.name} is not added. Switch it on above first.`, "is-error");
      const prompt = (match[2] ?? match[3] ?? "").trim() || "The capital of France is";
      print([
        `# ${item.name}: run it on your Mac`,
        "curl -fsSL https://pie-project.org/install.sh | bash",
        "pie model import Qwen/Qwen3.5-0.8B",
        "git clone https://github.com/pie-project/pie && cd pie",
        `pie run examples/${item.example} -- --prompt ${JSON.stringify(prompt)}`,
      ].join("\n"), "is-code");
    };
    print("Welcome to the pie playground. Type help to begin.", "is-dim");
    input.addEventListener("keydown", (event) => {
      if (event.key !== "Enter") return;
      const command = input.value.trim();
      input.value = "";
      if (!command) return;
      print(`pie> ${command}`, "is-echo");
      const [verb, ...rest] = command.split(/\s+/);
      if (verb === "help") help();
      else if (verb === "ls") ls();
      else if (verb === "run") run(command.slice(3));
      else if (verb === "clear") body.innerHTML = "";
      else print(`Unknown command: ${verb}. Type help.`, "is-error");
    });
    element.querySelector("#term").addEventListener("click", (event) => {
      if (!event.target.closest("input")) input.focus();
    });
    element.addEventListener("change", (event) => {
      const box = event.target.closest("[data-inferlet]");
      if (!box) return;
      const item = byId(box.dataset.inferlet);
      if (box.checked) added.add(item.id);
      else added.delete(item.id);
      save();
      print(`${box.checked ? "Added" : "Removed"} ${item.name}.`, "is-dim");
    });
  };

  Pie.inferlets = {
    element,
    render(state) {
      element.hidden = state.table !== "inferlets";
      if (!element.hidden && element.dataset.ready !== "1") {
        element.innerHTML = `<div class="method-inner">${content}</div>`;
        element.dataset.ready = "1";
        playground();
      }
    },
  };
})();
