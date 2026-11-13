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
  // what each stage does and where its time usually goes when an engine is slow there: the card a stage shows on hover
  const HINTS = {
    attention: ["Reads the KV cache and scores past tokens", ["No fast kernel for this chip (a fallback)", "KV pages gathered or copied first", "Long contexts, unbatched decode"]],
    dense_matmul: ["Multiplies each layer's weights", ["Weights read below memory bandwidth", "Quantized weights unpacked every step", "Shapes padded to bigger tiles"]],
    moe: ["Routes tokens and runs the chosen experts", ["Experts requantized or unpacked on the fly", "Unused experts read anyway", "One launch per expert, not grouped"]],
    norm_rope_elementwise: ["Normalization, rotary embeddings, elementwise work", ["Many small unfused kernels", "Tables copied to a new layout every step", "Extra fp32 casts"]],
    sampling: ["Picks the next token", ["Full-vocabulary sort or softmax", "Logits copied to the CPU", "Sampling on one CPU thread"]],
    other_gpu: ["Any other kernel, such as copies", ["Weights or caches copied every step", "Host and device transfers", "Cache bookkeeping kernels"]],
    gpu_idle: ["The GPU waits on the host inside the step", ["Host prep slower than the GPU work", "No graph capture or compiled step", "Syncs between kernel launches"]],
  };
  // a profile's third bar: the machine's limit for the cell, the fastest any engine could run it
  const LIMIT = ["limit", "Limit", "transparent"];  // drawn as an outline, no stage's fill
  const BOUND = { bandwidth: "Bandwidth-bound", compute: "Compute-bound", interconnect: "Interconnect-bound", balanced: "Balanced" };
  // value: what the segment measures, already in words (its ms in a profile, its share in the Summary); note: a line under it
  const hint = (k, value, note = "") => {
    const [, name, color] = [...STAGES, LIMIT].find(([key]) => key === k);
    const [does, slow] = k === LIMIT[0] ? ["The theoretical maximum the grid checks every number against: no engine can run this cell faster", []] : HINTS[k];
    return `<div class="gap-tip-title"><span class="stage-tip-name"><i${k === LIMIT[0] ? ' class="is-limit"' : ""} style="background: ${color}"></i>${esc(name)}</span>${value ? `<span class="gap-tip-end gap-tip-gap">${esc(value)}</span>` : ""}</div>`
      + `<div class="gap-tip-body">${esc(does)}</div>${note ? `<div class="gap-tip-at">${esc(note)}</div>` : ""}${slow.length ? `<div class="stage-tip-head">Slow when</div><ul class="stage-tip-list">${slow.map((s) => `<li>${esc(s)}</li>`).join("")}</ul>` : ""}`;
  };
  // the cell's limit in its profile's own unit, from the grid's own theoretical maximum at the shape pie's run had:
  // a token (decode), a prompt (prefill), a wave of prompts (batched prefill), a step of every request (batched decode)
  const limitOf = (c) => {
    const r = c.row;
    if (!r || c.setup === "spec") return null;
    const at = c.setup === "batching" ? Pie.batchedCeiling?.(r.hardware, r.model, r.scheme, r.benchmark, r) : Pie.ceiling?.(r, c.setup);
    const tokens = c.setup === "batching" ? at?.parts?.requests : c.setup === "decode" ? 1 : at?.parts?.tokens;
    return at?.tps && tokens ? { ms: 1000 * tokens / at.tps, bound: at.bound } : null;
  };
  // a model slice's mark, the grid's own: a square cut by a diagonal
  const sliceIcon = (label) => `<svg class="reasons-slice-icon" viewBox="0 0 16 16" role="img" aria-label="${esc(label)}"><title>${esc(label)}</title><rect x="2.5" y="2.5" width="11" height="11" rx="2.5"/><path d="M4 12 12 4"/></svg>`;
  const verified = (c) => (Pie.profiles || {})[`${c.hardware}|${c.model}|${c.setup}`]?.verdict === "confirmed";
  const ms = (v) => `${v >= 100 ? Math.round(v) : v >= 10 ? v.toFixed(1) : v.toFixed(2)} ms`;
  const profileOf = (c) => {
    const p = (Pie.profiles || {})[`${c.hardware}|${c.model}|${c.setup}`];
    if (!p) return `<p class="reasons-item-suggestion">Not measured yet</p>`;
    const total = (side) => STAGES.reduce((n, [k]) => n + (side.stages[k] || 0), 0);
    const limit = limitOf(c);
    const top = Math.max(total(p.fastest), total(p.second), limit?.ms || 0);
    const bar = (side) => `<div class="profile-row"><span class="profile-engine">${esc(nameOf(side.engine))}</span><span class="profile-bar">${STAGES.map(([k, , color]) => side.stages[k] > 0 ? `<i style="width: ${(100 * side.stages[k] / top).toFixed(2)}%; background: ${color}" data-stage="${k}" data-stage-value="${ms(side.stages[k])}"></i>` : "").join("")}</span><span class="profile-total">${ms(total(side))}</span></div>`;
    // the limit as its own bar on the same scale, so each engine's distance from it reads off the bars
    const floor = limit ? `<div class="profile-row is-limit"><span class="profile-engine">Limit</span><span class="profile-bar"><i class="is-limit" style="width: ${(100 * limit.ms / top).toFixed(2)}%" data-stage="limit" data-stage-value="${ms(limit.ms)}" data-stage-note="${esc(BOUND[limit.bound] || "")}"></i></span><span class="profile-total">${ms(limit.ms)}</span></div>` : "";
    const used = STAGES.filter(([k]) => p.fastest.stages[k] > 0 || p.second.stages[k] > 0);
    return `${bar(p.fastest)}${bar(p.second)}${floor}
                <p class="profile-legend">${used.map(([k, name, color]) => `<span data-stage="${k}"><i style="background: ${color}"></i>${name}</span>`).join("")}</p>
                <p class="profile-note">${esc(`${p.unit || ""}${c.miniature ? `, on a model slice (${c.miniature})` : ""}`)}</p>`;
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
  // the Summary, about one engine (Pie unless picked): every profiled cell it was in, set against the other engine there.
  // Two charts: its time in each stage over the other engine's, cell by cell, and how far each step is from the machine's
  // limit, its and the other engine's
  const SUMMARY = "summary";
  const ENGINE_KEY = "pieSummaryEngine";
  let summaryEngine = (() => { try { return localStorage.getItem(ENGINE_KEY) || null; } catch { return null; } })();
  let summaryEngines = [];
  const CHEVRON = '<svg class="popup-chevron" viewBox="0 0 10 14" aria-hidden="true"><path d="M2 5l3-3 3 3M2 9l3 3 3-3"/></svg>';
  const WORKLOADS = [["decode", "Single Decode"], ["prefill", "Single Prefill"], ["batching", "Batched Decode"], ["pbatch", "Batched Prefill"]];
  const cellsWord = (n) => `${n.toLocaleString("en-US")} ${n === 1 ? "cell" : "cells"}`;
  const times = (v) => `${v >= 10 ? Math.round(v) : v >= 1 ? v.toFixed(1) : v.toFixed(2)}×`;
  const median = (list) => { const q = [...list].sort((a, b) => a - b), m = q.length >> 1; return q.length ? (q.length % 2 ? q[m] : (q[m - 1] + q[m]) / 2) : null; };
  // a dot's height in its row: spread by the golden ratio, so dots at one value sit apart and a redraw keeps them still
  const spread = (i) => 22 + 56 * ((i * 0.618034) % 1);
  // a value's place on a log axis from lo to hi, in percent of the row
  const at = (v, lo, hi) => 100 * (Math.log2(Math.min(hi, Math.max(lo, v))) - Math.log2(lo)) / (Math.log2(hi) - Math.log2(lo));
  // the cells an engine was profiled in, each with its side and the other engine's, under the page's two switches
  const pairsOf = (engine) => {
    const out = [];
    for (const c of Pie.platform?.seconds?.(Pie.state) || []) {
      if ((c.engine !== engine && c.rival !== engine) || (!slices && c.miniature)) continue;
      const p = (Pie.profiles || {})[`${c.hardware}|${c.model}|${c.setup}`];
      if (!p?.fastest?.stages || !p?.second?.stages || (verifiedOnly && p.verdict !== "confirmed")) continue;
      const mine = p.fastest.engine === engine ? p.fastest : p.second.engine === engine ? p.second : null;
      if (mine) out.push({ c, p, mine, theirs: mine === p.fastest ? p.second : p.fastest, ahead: mine === p.fastest });
    }
    return out;
  };
  // every dot on the Summary, by its index: what its card says and the cell a click opens
  let dots = [];
  const dotTip = (el) => {
    const d = dots[el.dataset.dot];
    if (!d) return "";
    const { c, mine, theirs } = d.pair;
    const head = `<div class="gap-tip-title"><span>${esc(modelName(c.model))} on ${esc(machineName(c.hardware))}</span><span class="gap-tip-end gap-tip-gap">${esc(d.value)}</span></div>`;
    return `${head}<div class="gap-tip-body">${esc(c.label)}${d.stage ? ` · ${esc(d.stage)}` : ""}</div>`
      + `<div class="gap-tip-at">${esc(nameOf(mine.engine))} ${d.a} · ${esc(nameOf(theirs.engine))} ${d.b}${d.limit ? ` · limit ${d.limit}` : ""}</div>`;
  };
  const summaryOf = (engine) => {
    const pairs = pairsOf(engine);
    dots = [];
    if (!pairs.length) return `<p class="reasons-empty">No profiled cells yet.</p>`;
    const name = esc(nameOf(engine));
    const dot = (pair, x, y, cls, value, extra, style = "") => `<i class="dot ${cls}" style="left: ${x.toFixed(2)}%; top: ${y.toFixed(1)}%${style}" data-dot="${dots.push({ pair, value, ...extra }) - 1}"></i>`;
    // 1. stage by stage: the engine's ms in a stage over the other engine's, one dot a cell, where the stage is 5% or more
    // of the step; left of 1x the engine is faster there, right of it slower
    const LO = 1 / 8, HI = 8;
    let k0 = 0;
    const stageRows = STAGES.map(([k, stageName]) => {
      const pts = pairs.filter(({ mine, theirs }) => (mine.stages[k] || 0) > 0 && (theirs.stages[k] || 0) > 0
        && Math.max(mine.stages[k], theirs.stages[k]) >= 0.05 * Math.max(mine.stepMs, theirs.stepMs));
      if (pts.length < 3) return "";
      const ratios = pts.map(({ mine, theirs }) => mine.stages[k] / theirs.stages[k]);
      const mid = median(ratios), faster = ratios.filter((r) => r < 0.9).length, slower = ratios.filter((r) => r > 1.1).length;
      const said = mid < 0.9 ? `faster in ${faster} of ${pts.length}` : mid > 1.1 ? `slower in ${slower} of ${pts.length}` : `${faster} faster, ${slower} slower`;
      const marks = pts.map((pair, i) => { const r = ratios[i]; return dot(pair, at(r, LO, HI), spread(k0 + i), r < 0.9 ? "is-faster" : r > 1.1 ? "is-slower" : "is-same", times(r),
        { stage: stageName, a: ms(pair.mine.stages[k]), b: ms(pair.theirs.stages[k]) }); }).join("");
      k0 += pts.length;
      return `<div class="dot-row"><span class="dot-label">${esc(stageName)}</span><span class="dot-plot"><span class="dot-one" style="left: 50%"></span>${marks}<b class="dot-median" style="left: ${at(mid, LO, HI).toFixed(2)}%"></b></span><span class="dot-stat"><b>${times(mid)}</b> ${said}</span></div>`;
    }).join("");
    const stageAxis = `<div class="dot-axis"><span></span><span class="dot-scale">${[[0.25, "0.25×"], [0.5, "0.5×"], [1, "1×"], [2, "2×"], [4, "4×"]].map(([v, l]) => `<span style="left: ${at(v, LO, HI)}%">${l}</span>`).join("")}</span><span></span></div>`;
    const stages = `<section class="summary-card"><h2>Stage by stage</h2><p class="summary-sub">${name}'s time in each stage over the other engine's, one dot a cell; the tick is the median. <i class="dot-key is-faster"></i>Faster <i class="dot-key is-slower"></i>Slower</p>${stageAxis}${stageRows}</section>`;
    // 2. how far each step is from the machine's limit: the engine's (filled) and the other engine's (hollow), one pair a
    // cell, joined; 1x is the limit itself
    const LIM_HI = 32;
    let w0 = 0;
    const limitRows = WORKLOADS.map(([setup, label]) => {
      const pts = [];
      for (const pair of pairs.filter((x) => x.c.setup === setup)) {
        const L = limitOf(pair.c);
        if (L?.ms) pts.push({ pair, L: L.ms, m: pair.mine.stepMs / L.ms, t: pair.theirs.stepMs / L.ms });
      }
      if (!pts.length) return "";
      const marks = pts.map(({ pair, L, m, t }, i) => {
        const y = spread(w0 + i), xm = at(m, 1, LIM_HI), xt = at(t, 1, LIM_HI), extra = { a: ms(pair.mine.stepMs), b: ms(pair.theirs.stepMs), limit: ms(L) };
        return `<span class="dot-link" style="left: ${Math.min(xm, xt).toFixed(2)}%; width: ${Math.abs(xm - xt).toFixed(2)}%; top: ${y.toFixed(1)}%"></span>`
          + dot(pair, xt, y, "is-hollow", `${times(t)} the limit`, extra) + dot(pair, xm, y, "is-mine", `${times(m)} the limit`, extra, `; --dot: ${colorOf(engine)}`);
      }).join("");
      w0 += pts.length;
      return `<div class="dot-row"><span class="dot-label">${esc(label)}</span><span class="dot-plot is-limit">${marks}</span><span class="dot-stat"><b>${times(median(pts.map((x) => x.m)))}</b> ${name} · ${times(median(pts.map((x) => x.t)))} others</span></div>`;
    }).join("");
    const limitAxis = `<div class="dot-axis"><span></span><span class="dot-scale">${[[1, "Limit"], [2, "2×"], [4, "4×"], [8, "8×"], [16, "16×"]].map(([v, l]) => `<span style="left: ${at(v, 1, LIM_HI)}%">${l}</span>`).join("")}</span><span></span></div>`;
    const limit = limitRows ? `<section class="summary-card"><h2>Distance from the limit</h2><p class="summary-sub">Each step over the machine's limit: <i class="dot-key" style="--dot: ${colorOf(engine)}"></i>${name} <i class="dot-key is-hollow"></i>the other engine, joined a cell; 1× is the hardware limit</p>${limitAxis}${limitRows}</section>` : "";
    // the headline: the cells, how many it leads, and its median distance from the limit
    const ahead = pairs.filter((x) => x.ahead).length;
    const dist = pairs.map((x) => { const L = limitOf(x.c); return L?.ms ? x.mine.stepMs / L.ms : null; }).filter((v) => v != null);
    const tiles = `<dl class="welcome-stats summary-stats"><div><dt>Cells profiled</dt><dd>${pairs.length.toLocaleString("en-US")}</dd></div>`
      + `<div><dt>Fastest in</dt><dd>${ahead} of ${pairs.length}</dd></div><div><dt>Median distance from the limit</dt><dd>${dist.length ? times(median(dist)) : "–"}</dd></div></dl>`;
    return `${tiles}${stages}${limit}`;
  };
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
    if (current !== SUMMARY && !list.some(([id]) => id === current)) current = SUMMARY;
    const overview = current === SUMMARY;
    const [id, , all] = overview ? [SUMMARY, 0, []] : list.find(([e]) => e === current) || [current, 0, []];
    // a grid cell that opens a model slice's row turns slices back on, so the row it asked for is there
    if (focus && !slices && all.some((c) => c.miniature && keyOf(id, c) === keyOf(focus.engine, focus))) {
      slices = true;
      try { localStorage.setItem(SLICES, "on"); } catch { /* private windows can refuse storage */ }
    }
    if (focus && verifiedOnly && all.some((c) => !verified(c) && keyOf(id, c) === keyOf(focus.engine, focus))) {
      verifiedOnly = false;
      try { localStorage.setItem(VERIFIED, "off"); } catch { /* private windows can refuse storage */ }
    }
    const keep = (c) => (slices || !c.miniature) && (!verifiedOnly || verified(c));
    const reasons = all.filter(keep);
    const engines = list.map(([e, , cs]) => [e, cs.filter(keep)]).filter(([, cs]) => cs.length);
    // the Summary's engine: any engine profiled in a cell on view, Pie unless picked
    if (overview) {
      const ids = new Set();
      for (const c of Pie.platform?.seconds?.(Pie.state) || []) if ((Pie.profiles || {})[`${c.hardware}|${c.model}|${c.setup}`]) ids.add(c.engine).add(c.rival);
      summaryEngines = [...ids].map((e) => [e, pairsOf(e).length]).filter(([, n]) => n).sort(([a, x], [b, y]) => (a === Pie.engines.primary ? -1 : b === Pie.engines.primary ? 1 : y - x));
      if (!summaryEngines.some(([e]) => e === summaryEngine)) summaryEngine = summaryEngines[0]?.[0] || null;
    }
    const cells = overview ? summaryEngines.find(([e]) => e === summaryEngine)?.[1] || 0 : reasons.length;
    const head = overview
      ? `<h1 class="board-title">Summary</h1><p class="board-lede">${summaryEngine ? `${esc(nameOf(summaryEngine))} in ${cellsWord(cells)} profiled against the other fastest engine` : "No profiled cells yet"}</p>`
      : `<h1 class="board-title"><i class="board-title-dot" style="background: ${colorOf(id)}" aria-hidden="true"></i>${esc(nameOf(id))} Profile</h1><p class="board-lede">${lede(id, cells)}</p>`;
    const body = overview
      ? (summaryEngine ? summaryOf(summaryEngine) : `<p class="reasons-empty">No profiled cells yet.</p>`)
      : reasons.length ? `<div class="reasons-group">${reasons.map((c) => item(id, c)).join("")}</div>` : `<p class="reasons-empty">${verifiedOnly && all.length ? "No verified cells yet." : "No cells behind."}</p>`;
    // the outline's fill rides from the engine it marked to the one picked, not drawn afresh on the new one
    const was = element.querySelector(".board-outline-thumb")?.style.cssText;
    element.innerHTML = `
      <div class="platform-bar board-bar"><span class="reasons-bar">Found a CI benchmark anomaly?</span><span class="filter reasons-bar-action"><a class="filter-button" href="https://github.com/pie-project/benchmarks" target="_blank" rel="noopener"><svg viewBox="0 0 16 16" aria-hidden="true"><path d="M8 .2a8 8 0 0 0-2.5 15.6c.4 0 .5-.2.5-.4v-1.5c-2.2.5-2.7-1-2.7-1-.4-.9-.9-1.2-.9-1.2-.7-.5.1-.5.1-.5.8.1 1.2.8 1.2.8.7 1.3 1.9.9 2.4.7.1-.5.3-.9.5-1.1-1.8-.2-3.6-.9-3.6-4 0-.9.3-1.6.8-2.1-.1-.2-.4-1 .1-2.1 0 0 .7-.2 2.2.8a7.6 7.6 0 0 1 4 0c1.5-1 2.2-.8 2.2-.8.4 1.1.2 1.9.1 2.1.5.6.8 1.3.8 2.1 0 3.1-1.9 3.8-3.6 4 .3.3.6.8.6 1.5v2.2c0 .2.1.5.6.4A8 8 0 0 0 8 .2z"/></svg>File a PR</a></span></div>
      <div class="board-scroll"><div class="board-inner">
        <nav class="board-outline" aria-label="Engines"><button type="button" class="board-outline-item${overview ? " is-current" : ""}" data-reasons-go="${SUMMARY}"><i class="board-outline-dot" style="background: var(--color-label-tertiary)" aria-hidden="true"></i><span>Summary</span></button><div class="board-outline-head">Profiles</div>${list.map(([e]) => `<button type="button" class="board-outline-item${e === current ? " is-current" : ""}" data-reasons-go="${esc(e)}"><i class="board-outline-dot" style="background: ${colorOf(e)}" aria-hidden="true"></i><span>${esc(nameOf(e))}</span></button>`).join("")}</nav>
        <div class="board-main">
          <div class="board-section-head"><div class="board-section-text">${head}</div>${overview && summaryEngine ? `<button class="filter-button board-title-pick summary-engine" type="button" data-reasons-pick="engine" aria-haspopup="menu" aria-label="Engine"><i class="summary-engine-dot" style="background: ${colorOf(summaryEngine)}" aria-hidden="true"></i>${esc(nameOf(summaryEngine))}${CHEVRON}</button>` : ""}
          <button type="button" class="board-title-pick reasons-slices" data-reasons-slices role="switch" aria-checked="${slices}">${sliceIcon("Model slices")}<span>Model slices</span><i class="reasons-switch" aria-hidden="true"></i></button>
          <button type="button" class="board-title-pick reasons-slices" data-reasons-verified role="switch" aria-checked="${verifiedOnly}"><svg class="reasons-slice-icon" viewBox="0 0 16 16" aria-hidden="true"><path d="M8 1.6 2.6 3.7v3.8c0 3.3 2.3 6 5.4 7 3.1-1 5.4-3.7 5.4-7V3.7Z"/><path d="M5.5 8.2l1.8 1.8 3.3-3.6"/></svg><span>Verified</span><i class="reasons-switch" aria-hidden="true"></i></button></div>
          ${body}
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
  // a stage's card follows the pointer over its bar segment or its legend entry, in the site's chart tooltip
  // as a macOS popover shows: after the pointer rests a moment on a mark, then still, just under the mark where the
  // pointer is; once one is up, the next mark's card comes at once, until the pointer has been off the marks a moment
  const tooltip = document.getElementById("chart-tooltip");
  const REST = 400, WARM = 300;
  let tipFor = null, pending = null, timer = 0, warmUntil = 0, lastX = 0;
  const hideTip = () => {
    clearTimeout(timer);
    pending = null;
    if (!tipFor || !tooltip) return;
    tipFor = null;
    warmUntil = performance.now() + WARM;
    tooltip.hidden = true;
    tooltip.classList.remove("is-note", "is-stage-tip");
  };
  const showTip = (seg) => {
    tooltip.innerHTML = seg.dataset.dot != null ? dotTip(seg) : hint(seg.dataset.stage, seg.dataset.stageValue, seg.dataset.stageNote);
    tooltip.classList.remove("is-card", "is-gap-note");
    tooltip.classList.add("is-note", "is-stage-tip");
    tooltip.hidden = false;
    tipFor = seg;
    // under the mark, its left edge a little left of the pointer; above the mark where the screen ends below it
    const box = seg.getBoundingClientRect();
    const below = box.bottom + 6;
    const top = below + tooltip.offsetHeight > window.innerHeight - 8 ? box.top - tooltip.offsetHeight - 6 : below;
    tooltip.style.left = `${Math.max(8, Math.min(lastX - 12, window.innerWidth - tooltip.offsetWidth - 8))}px`;
    tooltip.style.top = `${Math.max(8, top)}px`;
  };
  element.addEventListener("mousemove", (event) => {
    lastX = event.clientX;
    const seg = event.target.closest("[data-stage], [data-dot]");
    if (!seg || !tooltip || Pie.tapCard?.isTouch()) { hideTip(); return; }
    if (seg === tipFor || seg === pending) return;
    clearTimeout(timer);
    if (tipFor || performance.now() < warmUntil) { pending = null; showTip(seg); return; }
    pending = seg;
    timer = setTimeout(() => { pending = null; if (seg.isConnected) showTip(seg); }, REST);
  });
  element.addEventListener("mouseleave", hideTip);
  document.addEventListener("scroll", hideTip, { capture: true, passive: true });
  element.addEventListener("click", (event) => {
    const seg = event.target.closest("[data-stage], [data-dot]");
    if (seg && Pie.tapCard?.isTouch()) {
      Pie.tapCard.toggle(seg, seg.dataset.dot != null ? dotTip(seg) : hint(seg.dataset.stage, seg.dataset.stageValue, seg.dataset.stageNote), true);
      return;
    }
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
    const pickButton = event.target.closest("[data-reasons-pick]");
    if (pickButton) {
      event.stopPropagation();
      Pie.popover.open(pickButton, `reasons:${pickButton.dataset.reasonsPick}`, null);
      return;
    }
    // a dot opens its cell's profile, on the slower engine's page, as a green grid cell does
    const hit = event.target.closest("[data-dot]");
    if (hit && dots[hit.dataset.dot]) {
      hideTip();
      focus = dots[hit.dataset.dot].pair.c;
      current = focus.engine;
      try { localStorage.setItem(KEY, current); } catch { /* private windows can refuse storage */ }
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
    // the Summary's engine menu: each engine on view with its cells behind
    menu: (k) => (k !== "engine" ? [] : summaryEngines.map(([e, c]) => ({ value: e, label: nameOf(e), dot: colorOf(e), detail: String(c), selected: e === summaryEngine }))),
    pick(k, value) {
      if (k !== "engine") return;
      summaryEngine = value;
      try { localStorage.setItem(ENGINE_KEY, summaryEngine); } catch { /* private windows can refuse storage */ }
    },
    render(state) {
      element.hidden = state.table !== "reasons";
      draw();
    },
  };
})();
