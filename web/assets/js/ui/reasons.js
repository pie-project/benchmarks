window.Pie = window.Pie || {};

// Suggestions: on each cell only the two fastest engines are compared, and the slower of the two gets the suggestion:
// Pie where it trails the fastest engine, the other engine where Pie leads it; grouped by engine, written once both are profiled
(() => {
  const element = document.getElementById("reasons");
  const esc = (text) => Pie.format.escape(String(text ?? ""));
  const nameOf = (id) => `${Pie.store.names?.engine?.(id) || id}${id.endsWith("-webgpu") ? " Web" : ""}`;
  const colorOf = (id) => Pie.engines.colorOf(id);

  // every cell where an engine is the slower of the two fastest, one row each, under that engine; no shared conclusion
  const groups = () => {
    const primary = Pie.engines.primary;
    const by = new Map([[primary, []]]);
    for (const g of Pie.platform?.seconds?.(Pie.state) || []) (by.get(g.engine) || by.set(g.engine, []).get(g.engine)).push(g);
    return [...by].map(([id, cells]) => [id, cells.length, cells.sort((x, y) => y.gap - x.gap)])
      .sort(([a, x], [b, y]) => (a === primary ? -1 : b === primary ? 1 : y - x));
  };
  const lede = (id, cells) => `${cells.toLocaleString("en-US")} ${cells === 1 ? "cell" : "cells"} behind`;
  const pct = (v) => `${Math.round(v * 100)}%`;
  const rowOf = (table, id) => (Pie.store.rows(table) || []).find((r) => r.id === id);
  const modelName = (id) => rowOf("models", id)?.name || id;
  const machineName = (id) => {
    const h = rowOf("hardware", id);
    if (!h) return id;
    const name = String(h.name || id).replace(/^Apple /, "");
    return h.class === "mac" && h.memory_gib ? `${name} ${h.memory_gib} GB` : name;
  };
  // a cell's profile: each engine's step split into the same stages, as one bar each on a shared scale, and the verdict
  const STAGES = [["attention", "Attention", "#5E5CE6"], ["dense_matmul", "Dense matmul", "#0A84FF"], ["moe", "MoE", "#30B0C7"],
    ["norm_rope_elementwise", "Norm and rope", "#34C759"], ["sampling", "Sampling", "#FF9F0A"], ["other_gpu", "Other GPU", "#AF52DE"], ["gpu_idle", "GPU idle", "#AEAEB2"]];
  // a model slice's mark, the grid's own: a square cut by a diagonal
  const sliceIcon = (label) => `<svg class="reasons-slice-icon" viewBox="0 0 16 16" role="img" aria-label="${esc(label)}"><title>${esc(label)}</title><rect x="2.5" y="2.5" width="11" height="11" rx="2.5"/><path d="M4 12 12 4"/></svg>`;
  const verified = (c) => (Pie.profiles || {})[`${c.hardware}|${c.model}|${c.setup}`]?.verdict === "confirmed";
  const ms = (v) => `${v >= 100 ? Math.round(v) : v >= 10 ? v.toFixed(1) : v.toFixed(2)} ms`;
  const profileOf = (c) => {
    const p = (Pie.profiles || {})[`${c.hardware}|${c.model}|${c.setup}`];
    if (!p) return `<p class="reasons-item-suggestion">Not measured yet</p>`;
    const total = (side) => STAGES.reduce((n, [k]) => n + (side.stages[k] || 0), 0);
    const top = Math.max(total(p.fastest), total(p.second));
    const bar = (side) => `<div class="profile-row"><span class="profile-engine">${esc(nameOf(side.engine))}</span><span class="profile-bar">${STAGES.map(([k, name, color]) => side.stages[k] > 0 ? `<i style="width: ${(100 * side.stages[k] / top).toFixed(2)}%; background: ${color}" title="${esc(`${name}: ${ms(side.stages[k])}`)}"></i>` : "").join("")}</span><span class="profile-total">${ms(total(side))}</span></div>`;
    const used = STAGES.filter(([k]) => p.fastest.stages[k] > 0 || p.second.stages[k] > 0);
    return `${bar(p.fastest)}${bar(p.second)}
                <p class="profile-legend">${used.map(([, name, color]) => `<span><i style="background: ${color}"></i>${name}</span>`).join("")}</p>
                <p class="profile-note">${esc(p.unit || "")}</p>`;
  };
  const keyOf = (engine, c) => `${engine}|${c.hardware}|${c.model}|${c.setup}`;
  // a row as a disclosure: the cell, its gap and setup; a click opens its profile and the suggestion
  const item = (id, c) => `
            <details class="reasons-item" data-reason-key="${esc(keyOf(id, c))}">
              <summary class="reasons-item-summary">
                ${verified(c)
                  ? `<span class="reasons-item-status is-verified" role="img" aria-label="Verified" title="Verified: a profile of both engines agrees with the benchmark"><svg viewBox="0 0 16 16" aria-hidden="true"><path class="shield" d="M8 1.6 2.6 3.7v3.8c0 3.3 2.3 6 5.4 7 3.1-1 5.4-3.7 5.4-7V3.7Z"/><path class="mark" d="M5.5 8.2l1.8 1.8 3.3-3.6"/></svg></span>`
                  : `<span class="reasons-item-status" aria-hidden="true"></span>`}
                <div class="reasons-item-text"><h2 class="reasons-item-title">${c.miniature ? sliceIcon(`Model slice: ${c.miniature}`) : ""}${esc(modelName(c.model))} on ${esc(machineName(c.hardware))}</h2>
                <p class="reasons-item-meta">${esc(c.label)}</p></div>
                <span class="reasons-item-gap">${pct(c.gap)} slower</span><svg class="reasons-item-chevron" viewBox="0 0 16 16" aria-hidden="true"><path d="M6 4l4 4-4 4"/></svg>
              </summary>
              <div class="reasons-item-body">${profileOf(c)}</div>
            </details>`;
  let focus = null;
  let shownCount = 0;
  const countText = () => `${shownCount.toLocaleString("en-US")} ${shownCount === 1 ? "profile" : "profiles"}`;
  const KEY = "pieSuggestionsEngine";
  let current = (() => { try { return localStorage.getItem(KEY); } catch { return null; } })();
  // model slices on or off, as the viewer left it: off keeps only the cells measured on the full model
  const SLICES = "pieSuggestionsSlices";
  let slices = (() => { try { return localStorage.getItem(SLICES) !== "off"; } catch { return true; } })();
  // verified only on or off, as the viewer left it, on until turned off: on keeps only the cells a profile of both engines confirms
  const VERIFIED = "pieSuggestionsVerifiedOnly";
  let verifiedOnly = (() => { try { return localStorage.getItem(VERIFIED) !== "off"; } catch { return true; } })();

  // one engine a page, as the Bench Book shows one chapter: the outline down the left picks it
  const draw = () => {
    if (element.hidden) return;
    // verified only, the outline lists the engines with a verified row, so no page opens empty
    const kept = (cells) => cells.some((c) => verified(c) && (slices || !c.miniature));
    const list = verifiedOnly && groups().some(([, , cells]) => kept(cells)) ? groups().filter(([, , cells]) => kept(cells)) : groups();
    if (!list.some(([id]) => id === current)) current = list[0]?.[0] || Pie.engines.primary;
    const [id, , all] = list.find(([e]) => e === current) || [current, 0, []];
    // a grid cell that opens a model slice's row turns slices back on, so the row it asked for is there
    if (focus && !slices && all.some((c) => c.miniature && keyOf(id, c) === keyOf(focus.engine, focus))) {
      slices = true;
      try { localStorage.setItem(SLICES, "on"); } catch { /* private windows can refuse storage */ }
    }
    if (focus && verifiedOnly && all.some((c) => !verified(c) && keyOf(id, c) === keyOf(focus.engine, focus))) {
      verifiedOnly = false;
      try { localStorage.setItem(VERIFIED, "off"); } catch { /* private windows can refuse storage */ }
    }
    const reasons = all.filter((c) => (slices || !c.miniature) && (!verifiedOnly || verified(c)));
    const cells = reasons.length;
    // the outline's fill rides from the engine it marked to the one picked, not drawn afresh on the new one
    const was = element.querySelector(".board-outline-thumb")?.style.cssText;
    element.innerHTML = `
      <div class="platform-bar board-bar"><span class="reasons-bar">Found a CI benchmark anomaly?</span><span class="filter reasons-bar-action"><a class="filter-button" href="https://github.com/pie-project/benchmarks" target="_blank" rel="noopener"><svg viewBox="0 0 16 16" aria-hidden="true"><path d="M8 .2a8 8 0 0 0-2.5 15.6c.4 0 .5-.2.5-.4v-1.5c-2.2.5-2.7-1-2.7-1-.4-.9-.9-1.2-.9-1.2-.7-.5.1-.5.1-.5.8.1 1.2.8 1.2.8.7 1.3 1.9.9 2.4.7.1-.5.3-.9.5-1.1-1.8-.2-3.6-.9-3.6-4 0-.9.3-1.6.8-2.1-.1-.2-.4-1 .1-2.1 0 0 .7-.2 2.2.8a7.6 7.6 0 0 1 4 0c1.5-1 2.2-.8 2.2-.8.4 1.1.2 1.9.1 2.1.5.6.8 1.3.8 2.1 0 3.1-1.9 3.8-3.6 4 .3.3.6.8.6 1.5v2.2c0 .2.1.5.6.4A8 8 0 0 0 8 .2z"/></svg>File a PR</a></span></div>
      <div class="board-scroll"><div class="board-inner">
        <nav class="board-outline" aria-label="Engines">${list.map(([e]) => `<button type="button" class="board-outline-item${e === current ? " is-current" : ""}" data-reasons-go="${esc(e)}"><i class="board-outline-dot" style="background: ${colorOf(e)}" aria-hidden="true"></i><span>${esc(nameOf(e))}</span></button>`).join("")}</nav>
        <div class="board-main">
          <div class="board-section-head"><div class="board-section-text"><h1 class="board-title"><i class="board-title-dot" style="background: ${colorOf(id)}" aria-hidden="true"></i>${esc(nameOf(id))} Profile</h1>
          <p class="board-lede">${lede(id, cells)}</p></div>
          <button type="button" class="board-title-pick reasons-slices" data-reasons-slices role="switch" aria-checked="${slices}">${sliceIcon("Model slices")}<span>Model slices</span><i class="reasons-switch" aria-hidden="true"></i></button>
          <button type="button" class="board-title-pick reasons-slices" data-reasons-verified role="switch" aria-checked="${verifiedOnly}"><svg class="reasons-slice-icon" viewBox="0 0 16 16" aria-hidden="true"><path d="M8 1.6 2.6 3.7v3.8c0 3.3 2.3 6 5.4 7 3.1-1 5.4-3.7 5.4-7V3.7Z"/><path d="M5.5 8.2l1.8 1.8 3.3-3.6"/></svg><span>Verified</span><i class="reasons-switch" aria-hidden="true"></i></button></div>
          ${reasons.length ? `<div class="reasons-group">${reasons.map((c) => item(id, c)).join("")}</div>` : `<p class="reasons-empty">${verifiedOnly && all.length ? "No verified cells yet." : "No cells behind."}</p>`}
        </div>
      </div></div>`;
    // under the window's title, how many suggestions the engine on view has
    shownCount = cells;
    if (Pie.toolbar?.elements?.subtitle && Pie.state.table === "reasons") Pie.toolbar.elements.subtitle.textContent = countText();
    const nav = element.querySelector(".board-outline"), on = nav?.querySelector(".is-current");
    if (nav && on) {
      const thumb = document.createElement("span");
      thumb.className = "board-outline-thumb";
      thumb.setAttribute("aria-hidden", "true");
      nav.prepend(thumb);
      if (was) { thumb.style.cssText = was; void thumb.offsetHeight; }
      const place = (tries) => {
        if (on.offsetParent === null) { if (tries > 0) requestAnimationFrame(() => place(tries - 1)); return; }
        thumb.style.transform = `translateY(${on.offsetTop}px)`;
        thumb.style.height = `${on.offsetHeight}px`;
      };
      place(120);
    }
    if (focus) {
      const target = element.querySelector(`[data-reason-key="${CSS.escape(keyOf(focus.engine, focus))}"]`);
      focus = null;
      if (target) {
        target.open = true;
        target.scrollIntoView({ block: "center" });
        target.classList.add("is-focus");
        setTimeout(() => target.classList.remove("is-focus"), 1400);
      }
    }
  };

  // a row opens and closes as a Mac disclosure does: its body grows or folds, the chevron turns, and one row is open at a time
  const still = () => window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
  const fold = (row, open) => {
    const body = row.querySelector(".reasons-item-body");
    row.getAnimations?.({ subtree: true }).forEach((a) => a.cancel());
    if (open) row.open = true;
    if (still() || !body?.animate) { row.open = open; return; }
    const height = `${body.scrollHeight}px`;
    const frames = open ? [{ height: "0px", opacity: 0 }, { height, opacity: 1 }] : [{ height, opacity: 1 }, { height: "0px", opacity: 0 }];
    const run = body.animate(frames, { duration: open ? 260 : 200, easing: open ? "cubic-bezier(.2, .8, .2, 1)" : "cubic-bezier(.4, 0, .6, 1)" });
    if (!open) run.onfinish = () => { row.open = false; };
  };
  element.addEventListener("click", (event) => {
    const summary = event.target.closest(".reasons-item-summary");
    if (summary) {
      event.preventDefault();
      const row = summary.parentElement;
      const opening = !row.open || row.classList.contains("is-closing");
      for (const other of element.querySelectorAll(".reasons-item[open]")) if (other !== row) fold(other, false);
      fold(row, opening);
      return;
    }
    if (event.target.closest("[data-reasons-slices]")) {
      slices = !slices;
      try { localStorage.setItem(SLICES, slices ? "on" : "off"); } catch { /* private windows can refuse storage */ }
      draw();
      return;
    }
    if (event.target.closest("[data-reasons-verified]")) {
      verifiedOnly = !verifiedOnly;
      try { localStorage.setItem(VERIFIED, verifiedOnly ? "on" : "off"); } catch { /* private windows can refuse storage */ }
      draw();
      return;
    }
    const go = event.target.closest("[data-reasons-go]");
    if (!go) return;
    current = go.dataset.reasonsGo;
    try { localStorage.setItem(KEY, current); } catch { /* private windows can refuse storage */ }
    draw();
  });

  Pie.reasons = {
    element,
    shown: () => countText(),
    // set by a green grid cell before it opens this page on its reason: that engine's page, scrolled to it
    focus(cell) { focus = cell || null; if (focus) current = focus.engine; },
    render(state) {
      element.hidden = state.table !== "reasons";
      draw();
    },
  };
})();
