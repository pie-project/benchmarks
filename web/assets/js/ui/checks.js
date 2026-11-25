window.Pie = window.Pie || {};

(() => {
  const element = document.getElementById("checks");
  const tooltip = document.getElementById("chart-tooltip");
  const esc = (value) => Pie.format.escape(value ?? "");
  const tables = () => Pie.store.tables;
  const ENGINE_LABELS = { pie: "pie", vllm: "vLLM", mlxlm: "mlx-lm", splash: "Splash", llamacpp: "llama.cpp", sglang: "SGLang" };
  const engineLabel = (id) => ENGINE_LABELS[id] || Pie.store.names.engine(id) || id;
  const hardwareName = (id) => Pie.store.index.hardware[id]?.name || id;
  const isNum = (v) => typeof v === "number" && Number.isFinite(v);
  const pct = (v, d = 1) => (isNum(v) ? `${(v * 100).toFixed(d)}%` : "–");
  const kl = (v) => (!isNum(v) ? "–" : v === 0 ? "0" : v < 0.001 ? v.toExponential(1) : v.toPrecision(2));

  let accuracyPlatform = null;
  let openFor = null;

  const empty = (text) => `<p class="qc-empty">${esc(text)}</p>`;
  const card = (title, rows, off = false, ok = "") => `<div class="tip-title">${esc(title)}</div><div class="tip-rows qc-tip-rows">${rows
    .filter(Boolean).map(([k, v, dim, engine]) => `<div class="tip-row${dim ? " is-slack" : ""}">${engine ? `<span class="tip-dot" style="background: ${Pie.engines.colorOf(engine)}"></span>` : "<span></span>"}<span class="tip-name">${esc(k)}</span><span class="tip-value">${esc(v)}</span></div>`).join("")}</div>${off
    ? `<div class="tip-foot qc-tip-off">${esc(off === true ? "Mismatch" : off)}</div>` : ok ? `<div class="tip-foot qc-tip-ok">${esc(ok)}</div>` : ""}`;

  const layersText = (layers) => (isNum(layers) ? `${layers} layers kept` : layers ? `layers ${layers} kept` : "");

  const failingList = (row) => `
    <div class="qc-pop-head">${esc(hardwareName(row.platform))}: ${esc((row.failing || []).length)} failing</div>
    <ul>${(row.failing || []).map((f) => `<li><code>${esc(f.name)}</code>${f.message ? `<span>${esc(f.message)}</span>` : ""}</li>`).join("") || "<li>No names recorded.</li>"}</ul>`;

  const PLATFORMS = ["mac", "windows", "nvidia", "amd", "tpu", "web"].filter((p) => !Pie.hiddenPlatforms.has(p));
  const familyOf = (row) => { const hw = row.platform && Pie.store.index.hardware[row.platform]; return hw ? Pie.platformOf(hw) : "mac"; };
  const platformLabel = (id) => Pie.schema[id]?.label || id;
  const RANK = { mlxlm: 0, vllm: 0, sglang: 1, splash: 2, llamacpp: 3 };
  const byRank = (a, b) => (RANK[a.arm.engine] ?? 9) - (RANK[b.arm.engine] ?? 9);
  const isOff = (arm) => arm.score_flag === "mismatch";
  const accuracyRows = (state) => {
    const byTag = tables().parity || {};
    const tags = [...new Set([state.release, ...(tables().tags || []).map((t) => t.id), ...Object.keys(byTag)])].filter((t) => byTag[t]?.length);
    const arms = (tag) => byTag[tag].flatMap((row) => row.arms.filter((a) => a.engine !== "pie" && isNum(a.diff)).map((a) => ({ row, arm: a, platform: familyOf(row) })));
    const platforms = PLATFORMS.filter((p) => tags.some((t) => arms(t).some((x) => x.platform === p)));
    if (!platforms.includes(accuracyPlatform)) accuracyPlatform = platforms[0] || null;
    const tag = tags.find((t) => arms(t).some((x) => x.platform === accuracyPlatform));
    return { platforms, tag, items: tag ? arms(tag).filter((x) => x.platform === accuracyPlatform).sort(byRank) : [] };
  };
  const platformBar = (platforms) => platforms.length ? `<span class="platform-compare qc-picker" role="group" aria-label="Platform">${platforms.map((p) =>
    `<button type="button" data-qc-platform="${esc(p)}" class="plain-button${p === accuracyPlatform ? " is-active" : ""}" aria-pressed="${p === accuracyPlatform}">${esc(platformLabel(p))}</button>`).join("")}</span>` : "";

  const deltaChart = (items, bare = false) => {
    const half = (a) => (isNum(a?.ci_low) && isNum(a?.ci_high) ? (a.ci_high - a.ci_low) / 2 : 0);
    const engines = [...new Set(items.map((x) => x.arm.engine))];
    const other = engines.length === 1 ? engineLabel(engines[0]) : "The other engine";
    const rows = items.map(({ row, arm }) => {
      const pie = row.arms.find((a) => a.artifact === (arm.vs || row.pie));
      if (!pie || !isNum(arm.diff)) return null;
      const err = Math.hypot(half(pie), half(arm));
      const title = `${Pie.store.names.model(row.model)} · ${row.task}`;
      return { label: engines.length === 1 ? title : `${title} · ${engineLabel(arm.engine)}`, d: arm.diff * 100, err: err * 100, tol: isNum(arm.tolerance) ? arm.tolerance * 100 : null, flag: isOff(arm),
        tip: card(title, [["pie", pct(pie.score), false, "pie"], [engineLabel(arm.engine), pct(arm.score), false, arm.engine],
          ["Difference", `${arm.diff < 0 ? "+" : arm.diff > 0 ? "−" : ""}${Math.abs(arm.diff * 100).toFixed(1)} pts`, true],
          isNum(arm.tolerance) ? ["Noise", `±${(arm.tolerance * 100).toFixed(1)} pts`, true] : null],
          isOff(arm) ? `Pie scores lower than ${engineLabel(arm.engine)}, beyond noise` : false) };
    }).filter(Boolean).sort((a, b) => Math.abs(b.d) - Math.abs(a.d));
    if (!rows.length) return "";
    const W = 880, L = 210, R = 24, RH = 18, T = 22, H = T + rows.length * RH + 8;
    const span = Math.max(10, Math.ceil(Math.max(...rows.map((r) => Math.abs(r.d) + r.err)) / 5) * 5);
    const x = (v) => L + (W - L - R) * (v + span) / (2 * span);
    const ticks = [-span, -span / 2, 0, span / 2, span].map((v) => `<line class="qc-grid${v === 0 ? " is-zero" : ""}" x1="${x(v)}" x2="${x(v)}" y1="${T - 6}" y2="${H - 4}"/><text class="qc-tick" x="${x(v)}" y="${T - 10}">${v > 0 ? "+" : ""}${v}</text>`).join("");
    const marks = rows.map((r, i) => {
      const y = T + i * RH + RH / 2;
      return `<g class="qc-mark${r.flag ? " is-off" : ""}" data-tip-html="${esc(r.tip)}">
        <rect class="qc-hit" x="0" y="${y - RH / 2}" width="${W}" height="${RH}"/>
        ${r.tol !== null ? `<rect class="qc-band" x="${x(-r.tol)}" y="${y - 5}" width="${x(r.tol) - x(-r.tol)}" height="10" rx="2"/>` : ""}
        <text class="qc-row" x="${L - 12}" y="${y + 4}">${esc(r.label)}</text>
        <line class="qc-err" x1="${x(Math.max(-span, r.d - r.err))}" x2="${x(Math.min(span, r.d + r.err))}" y1="${y}" y2="${y}"/>
        <circle class="qc-dot" cx="${x(r.d)}" cy="${y}" r="4"/>
      </g>`;
    }).join("");
    const svg = `<svg class="qc-chart" viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(`${other} minus Pie, in points`)}">${ticks}${marks}</svg>`;
    if (bare) return `${svg}<p class="qc-chart-key"><span><i class="qc-key-band"></i>Tolerance</span><span><i class="qc-key-dot"></i>Within it</span><span><i class="qc-key-dot is-off"></i>Mismatch</span></p>`;
    return `<div class="qc-chart-card">
      ${svg}
      <p class="qc-chart-key"><span><i class="qc-key-band"></i>Tolerance</span><span><i class="qc-key-dot"></i>Within it</span><span><i class="qc-key-dot is-off"></i>Mismatch</span><span>${esc(other)} minus Pie, in points; right of zero, Pie scores lower</span></p>
    </div>`;
  };

  const QUALITY_MAC = "m5-max-128g";
  const PREFER = { mac: "mlxlm", nvidia: "vllm", amd: "vllm", tpu: "vllm" };
  const byPrefer = (platform, engine) => (a, b) => (engine(b) === PREFER[platform]) - (engine(a) === PREFER[platform]) || (RANK[engine(a)] ?? 9) - (RANK[engine(b)] ?? 9);
  const NOFIT = '<svg class="platform-nofit" viewBox="0 0 16 16" aria-hidden="true"><rect x="2.5" y="2.5" width="11" height="11" rx="2.5"/><path d="M4 12 12 4"/></svg>';
  const scoreOf = (state, mac, model, platform) => {
    const byTag = tables().parity || {};
    for (const tag of new Set([state.release, ...(tables().tags || []).map((t) => t.id), ...Object.keys(byTag)])) {
      for (const row of byTag[tag] || []) {
        if (row.task !== "math500" || row.model !== model || (row.platform || QUALITY_MAC) !== mac) continue;
        const arm = row.arms.filter((a) => a.engine !== "pie" && isNum(a.diff)).sort(byPrefer(platform, (a) => a.engine))[0];
        const pie = arm && row.arms.find((a) => a.artifact === (arm.vs || row.pie));
        if (pie) return { row, arm, pie, tag, d: -arm.diff * 100 };
      }
    }
    return null;
  };
  const klOf = (mac, model, platform) => (tables().quality_parity || [])
    .filter((r) => r.platform === mac && r.model === model && !r.ref_unsupported && isNum(r.kl_mean))
    .sort((a, b) => byPrefer(platform, (r) => r.ref_engine)(a, b) || String(b.date || "").localeCompare(String(a.date || "")))[0] || null;
  const KL_PASS = 0.15, MATH_PASS = 5;
  const gapOf = (mac, model) => (tables().quality_gaps || []).find((g) => [].concat(g.platform).includes(mac) && [].concat(g.model).includes(model))?.reason || "";
  const allowed = (g) => (isNum(g.arm.tolerance) ? g.arm.tolerance * 100 : MATH_PASS);
  const MARK = { pass: '<svg class="qc-mark" viewBox="0 0 16 16" aria-label="Pass"><path d="M3.5 8.5l3 3 6-7"/></svg>', fail: '<svg class="qc-mark" viewBox="0 0 16 16" aria-label="Fail"><path d="M4.5 4.5l7 7M11.5 4.5l-7 7"/></svg>' };
  const gridOf = (state, { platform, macs, models }, layout) => {
    const key = platform.id;
    const tight = Pie.state?.platform?.narrowBy?.[key] ?? (Pie.state?.platform?.narrow ?? true);
    const narrowLabel = tight ? "Show Overall and memory" : "Hide Overall and memory";
    const nofit = (mac, model) => layout.sliced.has(`${mac}|${model}`) || Boolean(layout.grid[mac]?.[model]?.needs) || Boolean(klOf(mac, model, platform.id)?.miniature);
    const at = {};
    for (const mac of macs) for (const model of models) at[`${mac}|${model}`] = nofit(mac, model) ? { kl: gapOf(mac, model) ? null : klOf(mac, model, platform.id) } : { score: gapOf(mac, model) ? null : scoreOf(state, mac, model, platform.id) };
    const fitsNot = new Set((Pie.store.snapshot(state.release) || []).filter((r) => r.engine === "pie" && r.status === "no_fit").map((r) => `${r.hardware}|${r.model}`));
    for (const mac of macs) for (const model of models) {
      const cell = at[`${mac}|${model}`];
      if (!cell.kl && !cell.score && !gapOf(mac, model) && fitsNot.has(`${mac}|${model}`)) at[`${mac}|${model}`] = { kl: undefined };
    }
    const signed = (d) => `${d > 0.05 ? "+" : d < -0.05 ? "−" : ""}${Math.abs(d).toFixed(1)}`;
    const cut = (model) => macs.some((mac) => layout.sliced.has(`${mac}|${model}`));
    const makers = [];
    for (const m of models) {
      const name = Pie.platform.makerName(m);
      const last = makers[makers.length - 1];
      if (last && last.name === name && last.cut === cut(m)) last.n++;
      else makers.push({ name, model: m, n: 1, cut: cut(m) });
    }
    const makerRow = `<tr class="platform-maker-row"><th class="platform-corner"><button type="button" class="platform-narrow" data-narrow="${esc(key)}" aria-pressed="${tight}" aria-label="${narrowLabel}" title="${narrowLabel}"><svg viewBox="0 0 16 16" aria-hidden="true"><path d="M7.5 4 3.5 8l4 4M12.5 4l-4 4 4 4"/></svg></button></th><th class="platform-corner is-overall"></th>${makers.map((k) =>
      `<th class="platform-maker" colspan="${k.n}" scope="colgroup" data-drop="maker" data-id="${esc(k.name)}"><span class="platform-maker-name">${Pie.platform.makerBadge(k.model)}<b>${esc(k.name)}</b><span>${k.n} ${k.n === 1 ? "model" : "models"}</span></span></th>`).join("")}<th class="platform-fill"></th></tr>`;
    const head = `<tr class="platform-head-row"><th class="platform-corner" scope="col">Hardware</th><th class="platform-corner is-overall" scope="col"><span class="platform-model">Overall</span><span class="platform-sub">Passed</span></th>${models.map((m) => {
      const info = Pie.store.index.models[m] || {};
      const size = info.params_b ? `${info.params_b}B${info.active_b && info.active_b !== info.params_b ? ` · ${info.active_b}B` : ""}` : "";
      return `<th scope="col" data-drop="model" data-col="${esc(m)}" data-id="${esc(m)}" data-maker="${esc(Pie.platform.makerName(m))}" data-tip-html="${esc(Pie.platform.modelCard(m))}"><span class="platform-col"><span><span class="platform-model">${esc(Pie.store.names.model(m))}</span><span class="platform-sub">${esc(size)}</span></span></span></th>`;
    }).join("")}<th class="platform-fill"></th></tr>`;
    const hidden = new Set(state.platform.hidden || []);
    const EYE = "M1.5 8s2.4-4.5 6.5-4.5S14.5 8 14.5 8s-2.4 4.5-6.5 4.5S1.5 8 1.5 8z";
    const eye = (mac) => {
      const off = hidden.has(mac);
      const label = off ? "Show this machine's results" : "Hide this machine's results";
      return `<button type="button" class="platform-eye" data-hide-mac="${esc(mac)}" aria-pressed="${off}" aria-label="${label}" title="${label}"><svg viewBox="0 0 16 16" aria-hidden="true"><path d="${EYE}"/>${off ? '<path d="M3 13 13 3"/>' : '<circle cx="8" cy="8" r="2"/>'}</svg></button>`;
    };
    const rowHead = (mac) => {
      const hw = Pie.store.index.hardware[mac];
      return `<th class="platform-row" scope="row" data-hide-mac="${esc(mac)}" data-tip-html="${esc(Pie.platform.specSheet(mac))}"><span class="platform-chip">${Pie.platform.badge(platform.id)}<span class="platform-name">${esc(String(hw?.name || mac).replace(/^Apple\s+/, ""))}</span>${hw?.memory_gib ? `<span class="platform-mem">${hw.memory_gib} GB</span>` : ""}</span></th>`;
    };
    const body = [...macs.filter((mac) => !hidden.has(mac)), ...macs.filter((mac) => hidden.has(mac))].map((mac) => {
      if (hidden.has(mac)) return `<tr class="is-hidden-row">${rowHead(mac)}<td class="is-overall" data-hide-mac="${esc(mac)}">${eye(mac)}</td>${models.map((m) => `<td data-col="${esc(m)}"></td>`).join("")}<td class="platform-fill"></td></tr>`;
      const verdicts = models.map((m) => { const { score: g, kl: r } = at[`${mac}|${m}`]; return r ? r.kl_mean < KL_PASS : g ? Math.abs(g.d) <= allowed(g) : null; }).filter((v) => v !== null);
      const passed = verdicts.filter(Boolean).length, bad = verdicts.length - passed;
      return `<tr>${rowHead(mac)}
        <td class="is-overall" data-hide-mac="${esc(mac)}">${!verdicts.length ? `<span class="platform-cell is-empty">–</span>` : `<span class="platform-cell ${bad ? "is-behind" : "is-same"}"${bad ? ` data-tip="${esc(`${bad} ${bad === 1 ? "model fails" : "models fail"}`)}"` : ""}>${passed}/${verdicts.length}</span>`}${eye(mac)}</td>
        ${models.map((m) => {
          const { score: g, kl: r } = at[`${mac}|${m}`];
          const title = `${Pie.store.names.model(m)} on ${hardwareName(mac)}`;
          if (r) {
            const tip = card(title, [["Compared", `Pie vs ${engineLabel(r.ref_engine)}`], ["Reference on", hardwareName(r.ref_platform || mac), true], ["Model slice", layersText(r.layers) || "Yes", true],
              [r.answer_tokens === 1 ? "First-token KL" : "KL, answer mean", kl(r.kl_mean)], ["Same top token", pct(r.top1_agree)], ["Prompts", `${r.prompts ?? "–"}`, true],
              isNum(r.first_self_kl) ? ["First-token KL", kl(r.first_kl_mean), true] : null,
              isNum(r.first_self_kl) ? [`${engineLabel(r.ref_engine)} against itself`, kl(r.first_self_kl), true] : null,
              r.date ? ["Measured", Pie.format.date(r.date), true] : null]);
            const ok = r.kl_mean < KL_PASS;
            const open = { model: [m], hardware: [mac], task: ["parity"], engine: ["pie", r.ref_engine] };
            return `<td class="is-openable${ok ? "" : " is-over-limit"}" data-col="${esc(m)}" data-open="${esc(JSON.stringify(open))}"><span class="platform-open" aria-hidden="true">See Runs<svg viewBox="0 0 16 16"><path d="M5 11 11 5M6 5h5v5"/></svg></span><span class="platform-cell ${ok ? "is-same" : "is-behind"} is-nofit" data-tip-html="${esc(tip)}">${NOFIT}<span class="platform-main">${MARK[ok ? "pass" : "fail"]}</span></span></td>`;
          }
          if (!g) return `<td data-col="${esc(m)}"><span class="platform-cell is-empty${"kl" in at[`${mac}|${m}`] ? " is-nofit" : ""}"${gapOf(mac, m) ? ` data-tip="${esc(gapOf(mac, m))}"` : ""}>${"kl" in at[`${mac}|${m}`] ? `${NOFIT}N/A` : "–"}</span></td>`;
          const off = Math.abs(g.d) > allowed(g);
          const tip = card(`${title} · MATH-500`, [["Pie", pct(g.pie.score), false, "pie"], [engineLabel(g.arm.engine), pct(g.arm.score), false, g.arm.engine],
            ["Difference", `${signed(g.d)} pts`, true], isNum(g.arm.tolerance) ? ["Noise", `±${(g.arm.tolerance * 100).toFixed(1)} pts`, true] : null, ["Release", g.tag, true]],
            off ? `Pie is more than ${allowed(g).toFixed(1)} points from ${engineLabel(g.arm.engine)}, beyond noise` : false);
          const open = { model: [m], hardware: [mac], task: ["math500"], engine: ["pie", g.arm.engine] };
          return `<td class="is-openable${off ? " is-over-limit" : ""}" data-col="${esc(m)}" data-open="${esc(JSON.stringify(open))}"><span class="platform-open" aria-hidden="true">See Runs<svg viewBox="0 0 16 16"><path d="M5 11 11 5M6 5h5v5"/></svg></span><span class="platform-cell ${off ? "is-behind" : "is-same"}" data-tip-html="${esc(tip)}"><span class="platform-main">${MARK[off ? "fail" : "pass"]}</span></span></td>`;
        }).join("")}<td class="platform-fill"></td></tr>`;
    }).join("");
    const cols = `<colgroup><col class="col-machine"><col class="col-model">${models.map(() => '<col class="col-model">').join("")}<col class="col-fill"></colgroup>`;
    return `<table class="platform-table${tight ? " is-tight" : ""}" style="--cols: ${models.length + 1}">${cols}<thead>${makerRow}${head}</thead><tbody>${body}</tbody></table>`;
  };
  const folded = new Proxy({}, { get: (_, id) => Boolean(Pie.state.platform.collapsed?.[id]) });
  const modelPick = () => {
    const picked = Pie.state.platform.models || [];
    const label = !picked.length ? "All Models" : picked.length <= 2 ? picked.map((id) => Pie.store.names.model(id)).join(", ") : `${picked.length} Models`;
    return `<span class="filter platform-setup"><button class="filter-button" type="button" data-grid-pick="model" aria-haspopup="menu" aria-label="Models">${esc(label)}<svg class="popup-chevron" viewBox="0 0 10 14" aria-hidden="true"><path d="M2 5l3-3 3 3M2 9l3 3 3-3"/></svg></button></span>`;
  };
  const gridPage = (state) => {
    const layout = Pie.platform.render(state, true);
    const sections = layout.sections.filter((g) => PLATFORMS.includes(g.platform?.id));
    shown = sections;
    if (!sections.length) return `<div class="platform-scroll">${empty("No accuracy scores to compare yet.")}</div>`;
    const bar = `<div class="platform-bar"><button type="button" class="plain-button rules-button" data-rules="quality" aria-expanded="false" aria-label="Test Conditions" title="Test Conditions"><svg viewBox="0 0 16 16" aria-hidden="true"><circle cx="8" cy="8" r="6.5"/><path d="M8 7.2v3.6M8 5.2v.1"/></svg><span class="rules-label">Test Conditions</span></button><span class="platform-bar-side is-end"><span class="platform-key" title="The full model does not fit one machine; a mark beside a check is a model slice&#39;s">${NOFIT}Does not fit</span>${modelPick()}</span></div>`;
    return `${bar}<div class="platform-scroll">${sections.map((g, i) => {
      const p = g.platform.id;
      return `<section class="platform-section">
        <div class="platform-group-row platform-section-bar${folded[p] ? " is-collapsed" : ""}" style="--stack: ${i}" data-qc-fold="${esc(p)}" role="button" aria-expanded="${!folded[p]}">
          <span class="platform-group-bar">
            <span class="platform-group-name">${Pie.platform.badge(p)}<b>${esc(g.platform.label)}</b><span>${g.macs.length} ${g.macs.length === 1 ? "machine" : "machines"}, ${g.models.length} ${g.models.length === 1 ? "model" : "models"}</span></span>
            <svg class="platform-disclosure" viewBox="0 0 8 14" aria-hidden="true"><path d="M1.5 1.5 6.5 7l-5 5.5"/></svg>
          </span>
        </div><div class="platform-section-body"${folded[p] ? " hidden" : ""}><div class="platform-section-scroll">${gridOf(state, g, layout)}</div></div></section>`;
    }).join("")}</div>`;
  };

  const closePop = () => {
    openFor = null;
    const pop = element.querySelector(".qc-pop");
    if (pop) pop.hidden = true;
  };

  let openRuns = () => {};
  let shownFor = null;
  let inherited = null;
  let shown = [];
  const wire = () => {
    const wasDrag = Pie.platform.wireColumnDrag(element, () => { Pie.saveView?.(); document.dispatchEvent(new CustomEvent("pie:refresh")); });
    element.addEventListener("click", (event) => {
      if (wasDrag()) return;
      const pick = event.target.closest("[data-grid-pick]");
      if (pick) { event.stopPropagation(); Pie.popover.open(pick, `grid:${pick.dataset.gridPick}`, null); return; }
      const eye = event.target.closest(".platform-eye[data-hide-mac]");
      if (eye) {
        const hidden = new Set(Pie.state.platform.hidden || []);
        const mac = eye.dataset.hideMac;
        if (hidden.has(mac)) hidden.delete(mac); else hidden.add(mac);
        Pie.state.platform.hidden = [...hidden];
        Pie.saveView?.();
        document.dispatchEvent(new CustomEvent("pie:refresh"));
        return;
      }
      const cell = event.target.closest("td[data-open]");
      if (cell) { openRuns(JSON.parse(cell.dataset.open)); return; }
      const narrow = event.target.closest("[data-narrow]");
      if (narrow) {
        if (event.detail) narrow.blur();
        const table = narrow.closest(".platform-table");
        const on = !table.classList.contains("is-tight");
        Pie.state.platform.narrowBy = { ...Pie.state.platform.narrowBy, [narrow.dataset.narrow]: on };
        Pie.saveView?.();
        const label = on ? "Show Overall" : "Hide Overall";
        table.classList.toggle("is-tight", on);
        narrow.setAttribute("aria-pressed", String(on)); narrow.title = label; narrow.setAttribute("aria-label", label);
        return;
      }
      const bar = event.target.closest("[data-qc-fold]");
      if (bar) {
        const id = bar.dataset.qcFold;
        const body = bar.nextElementSibling;
        const fold = !folded[id];
        Pie.state.platform.collapsed = { ...(Pie.state.platform.collapsed || {}), [id]: fold };
        Pie.saveView?.();
        bar.classList.toggle("is-collapsed", fold);
        bar.setAttribute("aria-expanded", String(!fold));
        body.getAnimations().forEach((a) => a.cancel());
        const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
        if (fold) {
          if (reduce) { body.hidden = true; return; }
          body.animate([{ height: `${body.offsetHeight}px` }, { height: "0px" }], { duration: 200, easing: "ease-in-out" }).onfinish = () => { body.hidden = true; };
        } else {
          body.hidden = false;
          if (!reduce) body.animate([{ height: "0px" }, { height: `${body.offsetHeight}px` }], { duration: 200, easing: "ease-in-out" });
        }
        return;
      }
      const platform = event.target.closest("[data-qc-platform]");
      if (platform) {
        accuracyPlatform = platform.dataset.qcPlatform;
        Pie.checks.render(Pie.state);
        return;
      }
      const button = event.target.closest("[data-kernel]");
      const pop = element.querySelector(".qc-pop");
      if (!button) {
        if (!event.target.closest(".qc-pop")) closePop();
        return;
      }
      const index = Number(button.dataset.kernel);
      if (openFor === index) return closePop();
      const rows = [...(tables().quality_kernels || [])].sort((a, b) => hardwareName(a.platform).localeCompare(hardwareName(b.platform)));
      openFor = index;
      pop.innerHTML = failingList(rows[index]);
      pop.hidden = false;
      const box = button.getBoundingClientRect();
      const host = pop.offsetParent.getBoundingClientRect();
      pop.style.top = `${box.bottom - host.top + 6}px`;
      pop.style.left = `${Math.max(0, Math.min(box.left - host.left, host.width - pop.offsetWidth))}px`;
    });
    document.addEventListener("keydown", (event) => { if (event.key === "Escape") closePop(); });
    element.addEventListener("mousemove", (event) => {
      const target = event.target.closest("[data-tip], [data-tip-html]") || event.target.closest("td, th")?.querySelector("[data-tip], [data-tip-html]");
      if (!target) { tooltip.hidden = true; tooltip.classList.remove("is-card", "is-note"); return; }
      if (target.dataset.tipHtml) { tooltip.innerHTML = target.dataset.tipHtml; tooltip.classList.add("is-card"); tooltip.classList.remove("is-note"); }
      else { tooltip.textContent = target.dataset.tip; tooltip.classList.remove("is-card"); tooltip.classList.add("is-note"); }
      tooltip.hidden = false;
      const x = Math.min(event.clientX + 14, window.innerWidth - tooltip.offsetWidth - 8);
      const y = Math.min(event.clientY + 14, window.innerHeight - tooltip.offsetHeight - 8);
      tooltip.style.left = `${Math.max(8, x)}px`;
      tooltip.style.top = `${Math.max(8, y)}px`;
    });
    element.addEventListener("mouseleave", () => { tooltip.hidden = true; });
  };

  Pie.checks = {
    element,
    accuracyBlock(state) {
      const { platforms, items } = accuracyRows(state);
      const chart = deltaChart(items);
      return chart ? `${platformBar(platforms)}${chart}` : "";
    },
    accuracyChart(state) {
      const { platforms, items } = accuracyRows(state);
      return { platforms, platform: accuracyPlatform, label: platformLabel(accuracyPlatform), chart: deltaChart(items, true) };
    },
    pick(platform) { accuracyPlatform = platform; },
    onOpenRuns(handler) { openRuns = handler; },
    inherit(ghosts) { inherited = ghosts; },
    render(state) {
      element.hidden = state.table !== "checks";
      if (element.hidden) { shownFor = null; return; }
      if (element.dataset.ready !== "1") {
        element.dataset.ready = "1";
        wire();
      }
      openFor = null;
      element.innerHTML = gridPage(state);
      if (shownFor !== state.table) Pie.platform.waveIn(element, inherited);
      inherited = null;
      shownFor = state.table;
      return { macs: shown.reduce((n, g) => n + g.macs.length, 0), models: new Set(shown.flatMap((g) => g.models)).size };
    },
  };
})();
