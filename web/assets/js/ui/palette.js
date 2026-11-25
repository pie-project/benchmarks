window.Pie = window.Pie || {};

(() => {
  const esc = (text) => Pie.format.escape(text);
  const button = document.getElementById("toolbar-search");
  const back = document.createElement("div");
  back.className = "palette-backdrop";
  back.hidden = true;
  document.body.append(back);
  let app = null;
  let rows = [];
  let at = 0;

  const ICON_SEARCH = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M11 4a7 7 0 1 0 0 14a7 7 0 1 0 0-14ZM16 16l4 4"/></svg>';
  const go = (table) => {
    app.state.table = table;
    app.render();
  };
  const filter = (text) => {
    app.state.query = text;
    const field = document.getElementById("search");
    if (field) field.value = text;
    app.render();
    label();
  };

  const entries = () => {
    const out = [];
    const shown = (id) => Pie.isOpen(id) && Pie.sections.some((s) => s.id === Pie.schema[id]?.section && (!s.login || Pie.signedIn()));
    for (const [id, s] of Object.entries(Pie.schema)) {
      if (!s.label || !shown(id)) continue;
      const section = Pie.sections.find((x) => x.id === s.section)?.label || "";
      out.push({ kind: s.view === "platform" && s.platform ? "Platform" : s.href ? "Link" : "Page", text: s.label, sub: s.href ? new URL(s.href).hostname : section, icon: Pie.icon(id), tint: s.tint,
        run: () => (s.href ? window.open(s.href, "_blank", "noopener") : go(id)) });
    }
    for (const hw of Pie.store.tables.hardware || []) {
      const platform = Pie.platformOf(hw);
      const s = Pie.schema[platform];
      if (!s || !shown(platform)) continue;
      const name = hw.name || hw.full_name || hw.id;
      out.push({ kind: "Machine", text: name, sub: s.short || s.label, icon: Pie.icon(platform), tint: s.tint, run: () => { go(platform); filter(name); } });
    }
    for (const m of Pie.board?.menu("model") || []) {
      out.push({ kind: "Model", text: m.label, sub: "Overview", icon: Pie.icon("models"), run: () => { Pie.board.pick("model", m.value); go("board"); } });
    }
    return out;
  };

  const match = (q) => {
    const words = q.toLowerCase().split(/\s+/).filter(Boolean);
    const all = entries();
    const found = words.length ? all.filter((e) => words.every((w) => `${e.text} ${e.sub} ${e.kind}`.toLowerCase().includes(w))) : all.filter((e) => ["Page", "Platform", "Link"].includes(e.kind));
    const order = ["Page", "Link", "Platform", "Machine", "Model"];
    found.sort((a, b) => (b.text.toLowerCase().startsWith(words[0] || "") - a.text.toLowerCase().startsWith(words[0] || "")) || order.indexOf(a.kind) - order.indexOf(b.kind));
    const list = found.slice(0, 12);
    if (q.trim() && app.filters()) list.push({ kind: "Filter", text: `Filter this page for “${q.trim()}”`, sub: "", icon: ICON_SEARCH, run: () => filter(q.trim()) });
    if (app.state.query && !q.trim()) list.unshift({ kind: "Filter", text: `Clear the filter “${app.state.query}”`, sub: "", icon: ICON_SEARCH, run: () => filter("") });
    return list;
  };

  const draw = () => {
    const list = back.querySelector(".palette-list");
    list.innerHTML = rows.length ? rows.map((r, i) => `
      <li class="palette-row${i === at ? " is-current" : ""}" data-row="${i}" role="option" aria-selected="${i === at}">
        <span class="palette-icon${r.tint ? " is-tile" : ""}"${r.tint ? ` style="--tint: ${r.tint}"` : ""}>${r.icon || ""}</span>
        <span class="palette-text">${esc(r.text)}</span>
        <span class="palette-sub">${esc(r.sub ? `${r.kind} · ${r.sub}` : r.kind)}</span>
      </li>`).join("") : `<li class="palette-empty">No results</li>`;
    list.querySelector(".is-current")?.scrollIntoView({ block: "nearest" });
  };
  const update = (q) => { rows = match(q); at = 0; draw(); };

  const open = () => {
    if (!app) return;
    back.innerHTML = `
      <div class="palette" role="dialog" aria-modal="true" aria-label="Search">
        <label class="palette-field">${ICON_SEARCH}<input type="text" placeholder="Search pages, machines and models" autocomplete="off" spellcheck="false" aria-label="Search" aria-controls="palette-list"><kbd>esc</kbd></label>
        <ul class="palette-list" id="palette-list" role="listbox"></ul>
      </div>`;
    back.hidden = false;
    button.setAttribute("aria-expanded", "true");
    const input = back.querySelector("input");
    input.value = app.state.query || "";
    input.select();
    input.focus();
    update(input.value);
  };
  const close = () => { back.hidden = true; back.innerHTML = ""; button.setAttribute("aria-expanded", "false"); };
  const choose = (i) => { const r = rows[i]; close(); r?.run(); };

  back.addEventListener("input", (event) => update(event.target.value));
  back.addEventListener("mousemove", (event) => {
    const row = event.target.closest("[data-row]");
    if (row && Number(row.dataset.row) !== at) { at = Number(row.dataset.row); draw(); }
  });
  back.addEventListener("click", (event) => {
    if (event.target === back) return close();
    const row = event.target.closest("[data-row]");
    if (row) choose(Number(row.dataset.row));
  });
  back.addEventListener("keydown", (event) => {
    if (event.key === "ArrowDown" || event.key === "ArrowUp") {
      event.preventDefault();
      if (rows.length) { at = (at + (event.key === "ArrowDown" ? 1 : rows.length - 1)) % rows.length; draw(); }
    } else if (event.key === "Enter") {
      event.preventDefault();
      choose(at);
    } else if (event.key === "Escape") {
      event.preventDefault();
      close();
    }
    event.stopPropagation();
  });
  document.addEventListener("keydown", (event) => {
    if (event.key.toLowerCase() === "k" && (event.metaKey || event.ctrlKey) && !event.altKey) {
      event.preventDefault();
      back.hidden ? open() : close();
    }
  }, true);
  button.addEventListener("click", open);

  const label = () => {
    const q = app?.state.query?.trim();
    button.innerHTML = `${ICON_SEARCH}<span class="toolbar-search-text">${q ? esc(q) : `<kbd>${/Mac|iPhone|iPad/.test(navigator.platform) ? "⌘" : "Ctrl "}K</kbd>`}</span>`;
    button.classList.toggle("is-filtered", Boolean(q));
    button.setAttribute("aria-label", q ? `Search, filtered for ${q}` : "Search");
  };

  Pie.palette = {
    bind(hooks) { app = hooks; label(); },
    open,
    isOpen: () => !back.hidden,
    refresh: () => label(),
  };
})();
