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
  const BOUND = { bandwidth: "Bandwidth-bound: the weights and KV cache read at peak memory bandwidth",
    compute: "Compute-bound: the step's math at the chip's peak FLOPS", interconnect: "Interconnect-bound: the exchange between the GPUs",
    balanced: "Memory and math take about as long" };
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
  // the Summary: where the slower engine's extra time goes, over every cell on view. A cell's extra time is the slower
  // engine's ms over the faster one's in each stage where it is over; each cell counts once, as its shares of that time
  const SUMMARY = "summary";
  const BY_KEY = "pieSummaryBy";
  let summaryBy = (() => { try { const v = localStorage.getItem(BY_KEY); return ["workload", "platform", "engine"].includes(v) ? v : "workload"; } catch { return "workload"; } })();
  // the engine the Summary is narrowed to (null: every engine), kept per browser; the engines on view and their cells, for its menu
  const ENGINE_KEY = "pieSummaryEngine";
  let summaryEngine = (() => { try { return localStorage.getItem(ENGINE_KEY) || null; } catch { return null; } })();
  let summaryEngines = [];
  const CHEVRON = '<svg class="popup-chevron" viewBox="0 0 10 14" aria-hidden="true"><path d="M2 5l3-3 3 3M2 9l3 3 3-3"/></svg>';
  const WORKLOADS = ["decode", "prefill", "batching", "pbatch", "spec"];
  const share = (v) => `${Math.round(100 * v)}%`;
  const cellsWord = (n) => `${n.toLocaleString("en-US")} ${n === 1 ? "cell" : "cells"}`;
  const heatTip = (cell) => `<div class="gap-tip-title"><span>${esc(cell.dataset.heatValue)}</span><span class="gap-tip-gap">of the extra time</span></div>`
    + `<div class="gap-tip-body">${esc(cell.dataset.heatStage)} · ${esc(cell.dataset.heatGroup)}</div><div class="gap-tip-at">${esc(cell.dataset.heatCells)}</div>`;
  let lossCells = [];
  const summaryOf = (cells) => {
    // each verified cell: its shares of the extra time by stage, and the stage it loses most in
    const rows = [];
    for (const c of cells) {
      const p = (Pie.profiles || {})[`${c.hardware}|${c.model}|${c.setup}`];
      if (p?.verdict !== "confirmed" || !p.fastest?.stages || !p.second?.stages) continue;
      const extra = Object.fromEntries(STAGES.map(([k]) => [k, Math.max(0, (p.second.stages[k] || 0) - (p.fastest.stages[k] || 0))]));
      const sum = STAGES.reduce((n, [k]) => n + extra[k], 0);
      if (!(sum > 0)) continue;
      const top = STAGES.reduce((a, [k]) => (extra[k] > extra[a] ? k : a), STAGES[0][0]);
      rows.push({ c, p, extra, share: Object.fromEntries(STAGES.map(([k]) => [k, extra[k] / sum])), top });
    }
    const mean = (list) => Object.fromEntries(STAGES.map(([k]) => [k, list.length ? list.reduce((n, r) => n + r.share[k], 0) / list.length : 0]));
    const overall = mean(rows);
    const ranked = STAGES.filter(([k]) => overall[k] >= 0.005).sort((a, b) => overall[b[0]] - overall[a[0]]);
    const gaps = cells.map((c) => c.gap).sort((a, b) => a - b);
    const mid = gaps.length >> 1;
    const median = gaps.length ? (gaps.length % 2 ? gaps[mid] : (gaps[mid - 1] + gaps[mid]) / 2) : 0;
    // the headline: how many cells, how far behind, and the stage most of the extra time goes to
    const tiles = `<dl class="welcome-stats summary-stats"><div><dt>Cells behind</dt><dd>${cells.length.toLocaleString("en-US")}</dd></div>`
      + `<div><dt>Median gap</dt><dd>${pct(median)}</dd></div><div><dt>Biggest cause</dt><dd>${ranked[0] ? esc(ranked[0][1]) : "–"}</dd></div></dl>`;
    // 1. where the extra time goes: one bar a stage, largest first, scaled to the largest
    const most = Math.max(0.01, ...ranked.map(([k]) => overall[k]));
    const where = `<section class="summary-card"><h2>Where the extra time goes</h2><p class="summary-sub">${summaryEngine ? `${esc(nameOf(summaryEngine))}'s extra time over the faster engine` : "The slower engine's extra time"} by stage, averaged over ${cellsWord(rows.length)} with a verified profile</p>
      ${ranked.map(([k, name, color]) => `<div class="summary-bar"><span class="summary-name"><i style="background: ${color}"></i>${esc(name)}</span><span class="summary-track"><i style="width: ${(100 * overall[k] / most).toFixed(2)}%; background: ${color}" data-stage="${k}" data-stage-value="${share(overall[k])} of the extra time"></i></span><span class="summary-value">${share(overall[k])}</span></div>`).join("")}</section>`;
    // 2. the same split by workload, platform or engine: a heatmap in one blue, darker where more of the extra time goes
    const by = summaryEngine && summaryBy === "engine" ? "workload" : summaryBy;
    const groupOf = by === "engine" ? (r) => [r.c.engine, nameOf(r.c.engine)]
      : by === "platform" ? (r) => { const hw = rowOf("hardware", r.c.hardware); const id = hw && Pie.platformOf?.(hw); return [id || "other", Pie.schema?.[id]?.label || "Other"]; }
      : (r) => [r.c.setup, r.c.label];
    const groups = new Map();
    for (const r of rows) { const [id, label] = groupOf(r); (groups.get(id) || groups.set(id, { label, rows: [] }).get(id)).rows.push(r); }
    const order = [...groups.entries()].sort(([a, x], [b, y]) => (by === "workload" ? WORKLOADS.indexOf(a) - WORKLOADS.indexOf(b) : y.rows.length - x.rows.length));
    const means = new Map(order.map(([id, g]) => [id, mean(g.rows)]));
    const cols = STAGES.filter(([k]) => order.some(([id]) => means.get(id)[k] >= 0.01));
    const peak = Math.max(0.01, ...order.flatMap(([id]) => cols.map(([k]) => means.get(id)[k])));
    const pick = `<span class="platform-compare summary-by" role="group" aria-label="Group by">${[["workload", "Workload"], ["platform", "Platform"], ...(summaryEngine ? [] : [["engine", "Engine"]])].map(([v, l]) => `<button type="button" class="plain-button${v === by ? " is-active" : ""}" aria-pressed="${v === by}" data-summary-by="${v}">${l}</button>`).join("")}</span>`;
    const heat = `<section class="summary-card"><div class="summary-head"><div><h2>By ${by}</h2><p class="summary-sub">Share of the extra time in each stage; each row averages its cells</p></div>${pick}</div>
      <div class="summary-heat-scroll"><table class="summary-heat"><thead><tr><th></th>${cols.map(([, name, color]) => `<th scope="col"><span class="summary-name"><i style="background: ${color}"></i>${esc(name)}</span></th>`).join("")}</tr></thead>
      <tbody>${order.map(([id, g]) => `<tr><th scope="row">${esc(g.label)}<span>${cellsWord(g.rows.length)}</span></th>${cols.map(([k, name]) => { const v = means.get(id)[k]; return `<td data-heat data-heat-value="${share(v)}" data-heat-stage="${esc(name)}" data-heat-group="${esc(g.label)}" data-heat-cells="${cellsWord(g.rows.length)}" style="background: color-mix(in srgb, var(--color-accent) ${Math.round(4 + 66 * v / peak)}%, transparent)">${v >= 0.05 ? share(v) : ""}</td>`; }).join("")}</tr>`).join("")}</tbody></table></div></section>`;
    // 3. the biggest single-stage losses: the stage a cell loses most in, as a share of the slower engine's whole step
    const losses = rows.map((r) => ({ ...r, ms: r.extra[r.top], of: r.extra[r.top] / (r.p.second.stepMs || 1) })).sort((a, b) => b.of - a.of).slice(0, 8);
    lossCells = losses.map((l) => l.c);
    const list = `<section class="summary-card"><h2>Biggest single-stage losses</h2><p class="summary-sub">The stage a cell loses most time in, as a share of the slower engine's step; a row opens its profile</p>
      ${losses.map((l, i) => { const [, name, color] = STAGES.find(([k]) => k === l.top); return `<button type="button" class="summary-loss" data-summary-cell="${i}"><span class="summary-loss-text"><b>${esc(nameOf(l.c.engine))} · ${esc(modelName(l.c.model))} on ${esc(machineName(l.c.hardware))}</b><span>${esc(l.c.label)} · ${esc(name)} +${ms(l.ms)}</span></span><span class="summary-track"><i style="width: ${(100 * Math.min(1, l.of)).toFixed(2)}%; background: ${color}" data-stage="${l.top}" data-stage-value="+${ms(l.ms)}"></i></span><span class="summary-value">${share(l.of)}</span></button>`; }).join("")}</section>`;
    return `${tiles}${rows.length ? `${where}${heat}${list}` : `<p class="reasons-empty">No verified profiles yet.</p>`}`;
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
    // the Summary's engine: one on view, or every engine
    summaryEngines = engines.map(([e, cs]) => [e, cs.length]);
    if (summaryEngine && !engines.some(([e]) => e === summaryEngine)) summaryEngine = null;
    const scoped = summaryEngine ? engines.filter(([e]) => e === summaryEngine) : engines;
    const cells = overview ? scoped.reduce((n, [, cs]) => n + cs.length, 0) : reasons.length;
    const head = overview
      ? `<h1 class="board-title">Summary</h1><p class="board-lede">${summaryEngine ? `${cellsWord(cells)} where ${esc(nameOf(summaryEngine))} trails the fastest engine` : `${cellsWord(cells)} behind across ${engines.length} ${engines.length === 1 ? "engine" : "engines"}`}</p>`
      : `<h1 class="board-title"><i class="board-title-dot" style="background: ${colorOf(id)}" aria-hidden="true"></i>${esc(nameOf(id))} Profile</h1><p class="board-lede">${lede(id, cells)}</p>`;
    const body = overview
      ? (engines.length ? summaryOf(scoped.flatMap(([, cs]) => cs)) : `<p class="reasons-empty">${verifiedOnly ? "No verified cells yet." : "No cells behind."}</p>`)
      : reasons.length ? `<div class="reasons-group">${reasons.map((c) => item(id, c)).join("")}</div>` : `<p class="reasons-empty">${verifiedOnly && all.length ? "No verified cells yet." : "No cells behind."}</p>`;
    // the outline's fill rides from the engine it marked to the one picked, not drawn afresh on the new one
    const was = element.querySelector(".board-outline-thumb")?.style.cssText;
    element.innerHTML = `
      <div class="platform-bar board-bar"><span class="reasons-bar">Found a CI benchmark anomaly?</span><span class="filter reasons-bar-action"><a class="filter-button" href="https://github.com/pie-project/benchmarks" target="_blank" rel="noopener"><svg viewBox="0 0 16 16" aria-hidden="true"><path d="M8 .2a8 8 0 0 0-2.5 15.6c.4 0 .5-.2.5-.4v-1.5c-2.2.5-2.7-1-2.7-1-.4-.9-.9-1.2-.9-1.2-.7-.5.1-.5.1-.5.8.1 1.2.8 1.2.8.7 1.3 1.9.9 2.4.7.1-.5.3-.9.5-1.1-1.8-.2-3.6-.9-3.6-4 0-.9.3-1.6.8-2.1-.1-.2-.4-1 .1-2.1 0 0 .7-.2 2.2.8a7.6 7.6 0 0 1 4 0c1.5-1 2.2-.8 2.2-.8.4 1.1.2 1.9.1 2.1.5.6.8 1.3.8 2.1 0 3.1-1.9 3.8-3.6 4 .3.3.6.8.6 1.5v2.2c0 .2.1.5.6.4A8 8 0 0 0 8 .2z"/></svg>File a PR</a></span></div>
      <div class="board-scroll"><div class="board-inner">
        <nav class="board-outline" aria-label="Engines"><button type="button" class="board-outline-item${overview ? " is-current" : ""}" data-reasons-go="${SUMMARY}"><i class="board-outline-dot" style="background: var(--color-label-tertiary)" aria-hidden="true"></i><span>Summary</span></button><div class="board-outline-head">Profiles</div>${list.map(([e]) => `<button type="button" class="board-outline-item${e === current ? " is-current" : ""}" data-reasons-go="${esc(e)}"><i class="board-outline-dot" style="background: ${colorOf(e)}" aria-hidden="true"></i><span>${esc(nameOf(e))}</span></button>`).join("")}</nav>
        <div class="board-main">
          <div class="board-section-head"><div class="board-section-text">${head}</div>${overview ? `<button class="filter-button board-title-pick summary-engine" type="button" data-reasons-pick="engine" aria-haspopup="menu" aria-label="Engine">${summaryEngine ? `<i class="summary-engine-dot" style="background: ${colorOf(summaryEngine)}" aria-hidden="true"></i>${esc(nameOf(summaryEngine))}` : "All engines"}${CHEVRON}</button>` : ""}
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
  const tooltip = document.getElementById("chart-tooltip");
  let tipFor = null;
  const hideTip = () => {
    if (!tipFor || !tooltip) return;
    tipFor = null;
    tooltip.hidden = true;
    tooltip.classList.remove("is-note", "is-stage-tip");
  };
  element.addEventListener("mousemove", (event) => {
    const seg = event.target.closest("[data-stage], [data-heat]");
    if (!seg || !tooltip || Pie.tapCard?.isTouch()) { hideTip(); return; }
    if (seg !== tipFor) {
      tooltip.innerHTML = seg.dataset.heat != null ? heatTip(seg) : hint(seg.dataset.stage, seg.dataset.stageValue, seg.dataset.stageNote);
      tooltip.classList.remove("is-card", "is-gap-note");
      tooltip.classList.add("is-note", "is-stage-tip");
      tooltip.hidden = false;
      tipFor = seg;
    }
    const x = Math.min(event.clientX + 14, window.innerWidth - tooltip.offsetWidth - 8);
    const y = Math.min(event.clientY + 14, window.innerHeight - tooltip.offsetHeight - 8);
    tooltip.style.left = `${Math.max(8, x)}px`;
    tooltip.style.top = `${Math.max(8, y)}px`;
  });
  element.addEventListener("mouseleave", hideTip);
  element.addEventListener("click", (event) => {
    const seg = event.target.closest("[data-stage], [data-heat]");
    if (seg && Pie.tapCard?.isTouch()) {
      Pie.tapCard.toggle(seg, seg.dataset.heat != null ? heatTip(seg) : hint(seg.dataset.stage, seg.dataset.stageValue, seg.dataset.stageNote), true);
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
    const by = event.target.closest("[data-summary-by]");
    if (by) {
      summaryBy = by.dataset.summaryBy;
      try { localStorage.setItem(BY_KEY, summaryBy); } catch { /* private windows can refuse storage */ }
      draw();
      return;
    }
    // a loss opens its own profile, on its engine's page, as a green grid cell does
    const loss = event.target.closest("[data-summary-cell]");
    if (loss && lossCells[loss.dataset.summaryCell]) {
      hideTip();
      focus = lossCells[loss.dataset.summaryCell];
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
    // the Summary's engine menu: every engine, then each engine on view with its cells behind
    menu: (k) => (k !== "engine" ? [] : [
      { value: "all", label: "All engines", detail: String(summaryEngines.reduce((n, [, c]) => n + c, 0)), selected: !summaryEngine },
      { separator: true },
      ...summaryEngines.map(([e, c]) => ({ value: e, label: nameOf(e), dot: colorOf(e), detail: String(c), selected: e === summaryEngine })),
    ]),
    pick(k, value) {
      if (k !== "engine") return;
      summaryEngine = value === "all" ? null : value;
      try { if (summaryEngine) localStorage.setItem(ENGINE_KEY, summaryEngine); else localStorage.removeItem(ENGINE_KEY); } catch { /* private windows can refuse storage */ }
    },
    render(state) {
      element.hidden = state.table !== "reasons";
      draw();
    },
  };
})();
