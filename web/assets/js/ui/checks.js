window.Pie = window.Pie || {};

// Quality checks: does pie compute what a reference engine computes? Three tables, each from the quality store.
// Parity: the token distributions of pie against vLLM (mlx-lm on a Mac), same weights, same device, per model and
// platform. Kernels: each backend's kernel tests. Accuracy: pie's benchmark scores beside another engine's on one model.
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
  // KL divergence in nats: tiny on a faithful engine, so small values read in scientific notation
  const kl = (v) => (!isNum(v) ? "–" : v === 0 ? "0" : v < 0.001 ? v.toExponential(1) : v.toPrecision(2));
  const err = (v) => (!isNum(v) ? "–" : v === 0 ? "0" : v < 0.001 || v >= 1000 ? v.toExponential(1) : v.toPrecision(2));
  const short = (v) => (v ? String(v).slice(0, 9) : "");

  let accuracyEngine = null;  // the engine the Accuracy table sets beside pie; vLLM when it has arms
  let openFor = null;  // the kernel row whose failing tests are listed in the popover

  const empty = (text) => `<p class="qc-empty">${esc(text)}</p>`;
  // a hover card as a Mac info panel reads: the subject in bold, then a row per figure, its name in grey on the left and
  // its value on the right, a mismatch last in red; carried as HTML in data-tip-html
  const card = (title, rows, off = false) => `<div class="board-tip-battle qc-tip"><div class="board-tip-head">${esc(title)}</div>${rows
    .filter(Boolean).map(([k, v]) => `<div class="board-tip-row"><span>${esc(k)}</span><b>${esc(v)}</b></div>`).join("")}${off ? `<div class="qc-tip-off">Mismatch</div>` : ""}</div>`;
  const range = (a) => (isNum(a?.ci_low) && isNum(a?.ci_high) ? `${pct(a.ci_low)} – ${pct(a.ci_high)}` : "");
  const section = (title, caption, body) => `
    <section class="qc-section">
      <h2>${esc(title)}</h2>
      <p class="qc-caption">${esc(caption)}</p>
      ${body}
    </section>`;

  // a miniature keeps a few of the model's layers: a count, or the kept range ("0-4")
  const layersText = (layers) => (isNum(layers) ? `${layers} layers kept` : layers ? `layers ${layers} kept` : "");
  const miniBadge = (row) => `<span class="qc-badge" title="${esc(["Miniature", layersText(row.layers)].filter(Boolean).join(": "))}">Miniature</span>`;

  // ---- parity: a row per model, a column per device ----------------------------------------------------
  const parityTip = (r) => [
    `${engineLabel(r.engine || "pie")} vs ${engineLabel(r.ref_engine)} on ${hardwareName(r.platform)}`,
    `KL mean ${kl(r.kl_mean)}, p50 ${kl(r.kl_p50)}`,
    `KL p99 ${kl(r.kl_p99)}, max ${kl(r.kl_max)}`,
    `Top-1 agreement ${pct(r.top1_agree)}`,
    `Exact match ${pct(r.exact_match, 0)}`,
    `${r.positions ?? "–"} positions over ${r.prompts ?? "–"} prompts${r.misaligned_texts ? `, ${r.misaligned_texts} misaligned` : ""}`,
    `pie ${short(r.version) || "–"}, ${engineLabel(r.ref_engine)} ${r.ref_version || "–"}`,
    r.miniature ? ["Miniature model", layersText(r.layers)].filter(Boolean).join(": ") : "",
    r.date ? `Measured ${Pie.format.date(r.date)}` : "",
  ].filter(Boolean).join("\n");

  const parityTable = () => {
    const rows = tables().quality_parity || [];
    if (!rows.length) return empty("No parity runs yet.");
    const platforms = [...new Set(rows.map((r) => r.platform))]
      .sort((a, b) => hardwareName(a).localeCompare(hardwareName(b)));
    const models = new Map();
    for (const r of rows) {
      const key = r.artifact;
      if (!models.has(key)) models.set(key, { artifact: r.artifact, model: r.model, cells: {} });
      models.get(key).cells[r.platform] = r;
    }
    const ordered = [...models.values()].sort((a, b) => Pie.store.names.model(a.model).localeCompare(Pie.store.names.model(b.model)) || a.artifact.localeCompare(b.artifact));
    const refs = (p) => [...new Set(rows.filter((r) => r.platform === p).map((r) => engineLabel(r.ref_engine)))].join(", ");
    const head = `<tr><th class="qc-lead">Model</th>${platforms.map((p) => `<th><span>${esc(hardwareName(p))}</span><small>vs ${esc(refs(p))}</small></th>`).join("")}</tr>`;
    const cell = (r) => (!r ? '<td class="qc-none">–</td>' : r.ref_unsupported ? `
      <td class="qc-cell qc-unsupported" data-tip="${esc(`${engineLabel(r.ref_engine)} cannot run this model\n${r.ref_unsupported}${r.pie_ok ? "\npie runs it" : ""}`)}" aria-label="${esc(engineLabel(r.ref_engine))} cannot run this model">
        ${Pie.icon("unsupported")}
        ${r.miniature ? miniBadge(r) : ""}
      </td>` : `
      <td class="qc-cell" data-tip="${esc(parityTip(r))}">
        <span class="qc-figure">${kl(r.kl_mean)}<span class="qc-sep">/</span>${pct(r.top1_agree)}</span>
        ${r.miniature ? miniBadge(r) : ""}
      </td>`);
    const body = ordered.map((m) => `
      <tr>
        <th class="qc-lead" scope="row"><span>${esc(Pie.store.names.model(m.model))}</span><code>${esc(m.artifact)}</code></th>
        ${platforms.map((p) => cell(m.cells[p])).join("")}
      </tr>`).join("");
    return `<div class="qc-scroll"><table class="qc-table qc-parity"><thead>${head}</thead><tbody>${body}</tbody></table></div>`;
  };

  // ---- kernels: a row per device -----------------------------------------------------------------------
  const kernelsTable = () => {
    const rows = [...(tables().quality_kernels || [])].sort((a, b) => hardwareName(a.platform).localeCompare(hardwareName(b.platform)));
    if (!rows.length) return empty("No kernel test runs yet.");
    const body = rows.map((r, i) => {
      const failing = r.failing || [];
      const failed = r.failed ?? failing.length;
      const worst = r.worst;
      return `
      <tr>
        <th class="qc-lead" scope="row"><span>${esc(hardwareName(r.platform))}</span><code>${esc(r.artifact)}</code></th>
        <td class="qc-num">${esc(r.passed ?? "–")}</td>
        <td class="qc-num">${failed
          ? `<button class="qc-failed" type="button" data-kernel="${i}" aria-haspopup="dialog">${esc(failed)} failed</button>`
          : `<span class="qc-ok">0</span>`}</td>
        <td class="qc-num qc-quiet">${esc(r.ignored ?? "–")}</td>
        <td class="qc-num"${worst?.name ? ` data-tip="${esc(`${worst.name}\nmax abs ${err(worst.max_abs)}, max rel ${err(worst.max_rel)}`)}"` : ""}>${worst ? `${err(worst.max_abs)}${isNum(worst.max_rel) ? `<span class="qc-quiet"> abs, ${err(worst.max_rel)} rel</span>` : ""}` : "–"}</td>
        <td class="qc-quiet"><code>${esc(short(r.version))}</code>${r.date ? ` ${esc(Pie.format.date(r.date))}` : ""}</td>
      </tr>`;
    }).join("");
    return `<div class="qc-scroll"><table class="qc-table qc-kernels">
      <thead><tr><th class="qc-lead">Platform</th><th class="qc-num">Passed</th><th class="qc-num">Failed</th><th class="qc-num">Ignored</th><th class="qc-num">Worst error</th><th>pie</th></tr></thead>
      <tbody>${body}</tbody></table></div>`;
  };

  const failingList = (row) => `
    <div class="qc-pop-head">${esc(hardwareName(row.platform))}: ${esc((row.failing || []).length)} failing</div>
    <ul>${(row.failing || []).map((f) => `<li><code>${esc(f.name)}</code>${f.message ? `<span>${esc(f.message)}</span>` : ""}</li>`).join("") || "<li>No names recorded.</li>"}</ul>`;

  // ---- accuracy: pie beside another engine, per model and task -------------------------------------------
  // the newest release whose parity rows carry the picked engine; the viewer's release first
  const accuracyRows = (state) => {
    const byTag = tables().parity || {};
    const tags = [state.release, ...(tables().tags || []).map((t) => t.id)].filter((t) => byTag[t]?.length);
    const arms = (tag) => byTag[tag].flatMap((row) => row.arms.filter((a) => a.engine !== "pie").map((a) => ({ row, arm: a })));
    const engines = [...new Set(tags.flatMap((t) => arms(t).map((x) => x.arm.engine)))]
      .sort((a, b) => (a === "vllm" ? -1 : b === "vllm" ? 1 : engineLabel(a).localeCompare(engineLabel(b))));
    if (!engines.includes(accuracyEngine)) accuracyEngine = engines[0] || null;
    const tag = tags.find((t) => arms(t).some((x) => x.arm.engine === accuracyEngine));
    return { engines, tag, items: tag ? arms(tag).filter((x) => x.arm.engine === accuracyEngine) : [] };
  };

  const flagTag = (flag) => (flag === "mismatch" ? '<span class="qc-flag is-mismatch">Mismatch</span>'
    : flag === "ok" ? '<span class="qc-flag is-ok">Match</span>' : '<span class="qc-flag">–</span>');

  // the gap at a glance: one row per model and task, a dot at the reference's score minus pie's (in points), a line for
  // its 95% range (both intervals combined) and a grey band for the tolerance; a dot outside its band is a mismatch
  const deltaChart = (items, other, bare = false) => {
    const half = (a) => (isNum(a?.ci_low) && isNum(a?.ci_high) ? (a.ci_high - a.ci_low) / 2 : 0);
    const rows = items.map(({ row, arm }) => {
      const pie = row.arms.find((a) => a.artifact === (arm.vs || row.pie));
      if (!pie || !isNum(arm.diff)) return null;
      const err = Math.hypot(half(pie), half(arm));
      const flag = arm.score_flag === "mismatch" || arm.agree_flag === "mismatch";
      return { label: `${Pie.store.names.model(row.model)} · ${row.task}`, d: arm.diff * 100, err: err * 100, tol: isNum(arm.tolerance) ? arm.tolerance * 100 : null, flag,
        tip: card(`${Pie.store.names.model(row.model)} · ${row.task}`, [["pie", pct(pie.score)], [other, pct(arm.score)],
          ["Gap", `${arm.diff > 0 ? "+" : arm.diff < 0 ? "−" : ""}${Math.abs(arm.diff * 100).toFixed(1)} ± ${(err * 100).toFixed(1)} pts`], isNum(arm.tolerance) ? ["Tolerance", `±${pct(arm.tolerance)}`] : null], flag) };
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
    const svg = `<svg class="qc-chart" viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(`${other} minus pie, in points`)}">${ticks}${marks}</svg>`;
    if (bare) return `${svg}<p class="qc-chart-key"><span><i class="qc-key-band"></i>Tolerance</span><span><i class="qc-key-dot"></i>Within it</span><span><i class="qc-key-dot is-off"></i>Mismatch</span></p>`;
    return `<div class="qc-chart-card">
      ${svg}
      <p class="qc-chart-key"><span><i class="qc-key-band"></i>Tolerance</span><span><i class="qc-key-dot"></i>Within it</span><span><i class="qc-key-dot is-off"></i>Mismatch</span><span>${esc(other)} minus pie, in points; right of zero, pie scores lower</span></p>
    </div>`;
  };

  const accuracyTable = (state) => {
    const { engines, tag, items } = accuracyRows(state);
    if (!items.length) return empty("No accuracy scores to compare yet.");
    const picker = engines.length > 1 ? `
      <span class="platform-compare qc-picker" role="group" aria-label="Engine">${engines.map((e) =>
        `<button type="button" data-engine="${esc(e)}" class="plain-button${e === accuracyEngine ? " is-active" : ""}" aria-pressed="${e === accuracyEngine}">${esc(engineLabel(e))}</button>`).join("")}</span>` : "";
    const other = engineLabel(accuracyEngine);
    const body = items.map(({ row, arm }) => {
      const pie = row.arms.find((a) => a.artifact === (arm.vs || row.pie));
      const flag = arm.score_flag === "mismatch" || arm.agree_flag === "mismatch" ? "mismatch" : arm.score_flag;
      const tip = [`pie ${pie ? `${pct(pie.score)} (95% ${pct(pie.ci_low)} to ${pct(pie.ci_high)}, n ${pie.n})` : "not run"}`,
        `${other} ${pct(arm.score)} (95% ${pct(arm.ci_low)} to ${pct(arm.ci_high)}, n ${arm.n})`,
        isNum(arm.tolerance) ? `Tolerance ${pct(arm.tolerance)}` : "",
        isNum(arm.agree) ? `Same answer as pie on ${pct(arm.agree, 0)} of prompts` : ""].filter(Boolean).join("\n");
      return `
      <tr data-tip="${esc(tip)}">
        <th class="qc-lead" scope="row"><span>${esc(Pie.store.names.model(row.model))}</span></th>
        <td>${esc(row.task)}</td>
        <td class="qc-num">${pie ? pct(pie.score) : "–"}</td>
        <td class="qc-num">${pct(arm.score)}</td>
        <td class="qc-num${arm.score_flag === "mismatch" ? " is-off" : ""}">${isNum(arm.diff) ? `${arm.diff > 0 ? "+" : arm.diff < 0 ? "−" : ""}${(Math.abs(arm.diff) * 100).toFixed(1)}` : "–"}</td>
        <td>${flagTag(flag)}</td>
      </tr>`;
    }).join("");
    return `${picker}${deltaChart(items, other)}
      <div class="qc-scroll"><table class="qc-table qc-accuracy">
        <thead><tr><th class="qc-lead">Model</th><th>Task</th><th class="qc-num">pie</th><th class="qc-num">${esc(other)}</th><th class="qc-num">Delta</th><th>Parity</th></tr></thead>
        <tbody>${body}</tbody></table></div>
      <p class="qc-foot">Release ${esc(tag)}. Delta is ${esc(other)} minus pie, in points. A mismatch is a gap wider than both 95% intervals together, or under 95% identical answers on the same weights.</p>`;
  };

  // the page: one grid in the platform pages' style, the benchmark tasks down the side and the models across under
  // their makers; each cell pie's score with its gap to the engine picked in the bar, red where it is a mismatch
  const engineBar = (engines) => engines.length ? `<span class="platform-compare qc-picker" role="group" aria-label="Engine">${engines.map((e) =>
    `<button type="button" data-engine="${esc(e)}" class="plain-button${e === accuracyEngine ? " is-active" : ""}" aria-pressed="${e === accuracyEngine}">pie vs ${esc(engineLabel(e))}</button>`).join("")}</span>` : "";
  const gridPage = (state) => {
    const { engines, tag, items } = accuracyRows(state);
    const other = engineLabel(accuracyEngine);
    const models = [...new Set(items.map((x) => x.row.model))]
      .sort((a, b) => Pie.platform.makerName(a).localeCompare(Pie.platform.makerName(b)) || Pie.store.names.model(a).localeCompare(Pie.store.names.model(b)));
    const tasks = [...new Set(items.map((x) => x.row.task))].sort();
    const at = {};
    for (const x of items) at[`${x.row.task}|${x.row.model}`] = x;
    const gap = (x) => {
      const pie = x?.row.arms.find((a) => a.artifact === (x.arm.vs || x.row.pie));
      return pie && isNum(x.arm.diff) ? { pie, d: -x.arm.diff * 100, off: x.arm.score_flag === "mismatch" || x.arm.agree_flag === "mismatch" } : null;
    };
    const signed = (d) => `${d > 0.05 ? "+" : d < -0.05 ? "−" : ""}${Math.abs(d).toFixed(1)}`;
    const median = (list) => { const v = list.filter(isNum).sort((a, b) => a - b); return v.length ? v[v.length >> 1] : null; };
    const makers = [];
    for (const m of models) {
      const name = Pie.platform.makerName(m);
      if (makers.length && makers[makers.length - 1].name === name) makers[makers.length - 1].n++;
      else makers.push({ name, model: m, n: 1 });
    }
    const makerRow = `<tr class="platform-maker-row"><th class="platform-corner"></th><th class="platform-corner is-overall"></th>${makers.map((k) =>
      `<th class="platform-maker" colspan="${k.n}" scope="colgroup"><span class="platform-maker-name">${Pie.platform.makerBadge(k.model)}<b>${esc(k.name)}</b><span>${k.n} ${k.n === 1 ? "model" : "models"}</span></span></th>`).join("")}<th class="platform-fill"></th></tr>`;
    const head = `<tr class="platform-head-row"><th class="platform-corner" scope="col">Task</th><th class="platform-corner is-overall" scope="col"><span class="platform-model">Overall</span><span class="platform-sub">Median gap</span></th>${models.map((m) => {
      const info = Pie.store.index.models[m] || {};
      const size = info.params_b ? `${info.params_b}B${info.active_b && info.active_b !== info.params_b ? ` · ${info.active_b}B active` : ""}` : "";
      return `<th scope="col"><span class="platform-col"><span><span class="platform-model">${esc(Pie.store.names.model(m))}</span><span class="platform-sub">${esc(size)}</span></span></span></th>`;
    }).join("")}<th class="platform-fill"></th></tr>`;
    const body = tasks.map((task) => {
      const o = median(models.map((m) => gap(at[`${task}|${m}`])?.d));
      return `<tr><th class="platform-row" scope="row"><span class="platform-chip"><span>${esc(task)}</span></span></th>
        <td class="is-overall">${o === null ? `<span class="platform-cell is-empty">–</span>` : `<span class="platform-cell ${Math.abs(o) < 0.05 ? "is-even" : o > 0 ? "is-ahead" : "is-behind"}">${signed(o)}</span>`}</td>
        ${models.map((m) => {
          const x = at[`${task}|${m}`];
          const g = gap(x);
          if (!g) return `<td><span class="platform-cell is-empty"${x ? ` data-tip="${esc(`${other} ${pct(x.arm.score)}\npie not run`)}"` : ""}>–</span></td>`;
          const tip = card(`${Pie.store.names.model(m)} · ${task}`, [["pie", pct(g.pie.score)], ["95% range", range(g.pie)], [other, pct(x.arm.score)], ["95% range", range(x.arm)],
            isNum(x.arm.tolerance) ? ["Tolerance", `±${pct(x.arm.tolerance)}`] : null], g.off);
          return `<td><span class="platform-cell ${g.off ? "is-behind" : "is-even"}" data-tip-html="${esc(tip)}"><span class="platform-main">${pct(g.pie.score)}<span class="qc-gap${g.off ? " is-off" : ""}">${signed(g.d)}</span></span></span></td>`;
        }).join("")}<td class="platform-fill"></td></tr>`;
    }).join("");
    const cols = `<colgroup><col class="col-machine"><col class="col-model">${models.map(() => '<col class="col-model">').join("")}<col class="col-fill"></colgroup>`;
    return `<div class="platform-bar">${engineBar(engines)}</div>
      <div class="platform-scroll">${items.length ? `<table class="platform-table" style="--cols: ${models.length + 1}">${cols}<thead>${makerRow}${head}</thead><tbody>${body}</tbody></table>` : empty("No accuracy scores to compare yet.")}</div>`;
  };

  const page = (state) => `
    <div class="method-inner qc-inner">
      <header class="method-head qc-head">
        <h1>Quality</h1>
        <p class="method-lede">Whether pie computes what a reference engine computes, on the same weights and the same device.</p>
      </header>
      ${section("Parity", "KL divergence of pie's next-token distribution from the reference engine's, mean over answer positions, and how often both pick the same top token.",
        `<div class="qc-banner" role="note"${(tables().quality_parity || []).length ? "" : " hidden"}>Miniature models: layers removed to fit one device. For engine-to-engine comparison only, not real model speed.</div>${parityTable()}`)}
      ${section("Kernels", "pie's kernel tests on each backend, against reference implementations.", kernelsTable())}
      ${section("Accuracy", "Benchmark scores of pie beside another engine on the same model.", accuracyTable(state))}
      <div class="qc-pop" role="dialog" hidden></div>
    </div>`;

  const closePop = () => {
    openFor = null;
    const pop = element.querySelector(".qc-pop");
    if (pop) pop.hidden = true;
  };

  const wire = () => {
    element.addEventListener("click", (event) => {
      const engine = event.target.closest("[data-engine]");
      if (engine) {
        accuracyEngine = engine.dataset.engine;
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
    // a cell's details follow the pointer in the site's chart tooltip
    element.addEventListener("mousemove", (event) => {
      const target = event.target.closest("[data-tip], [data-tip-html]");
      if (!target) { tooltip.hidden = true; tooltip.classList.remove("is-board"); return; }
      if (target.dataset.tipHtml) { tooltip.innerHTML = target.dataset.tipHtml; tooltip.classList.add("is-board"); }
      else { tooltip.textContent = target.dataset.tip; tooltip.classList.remove("is-board"); }
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
    // the accuracy gap, for the Overview's last section: the engine pick and the chart
    accuracyBlock(state) {
      const { engines, items } = accuracyRows(state);
      const chart = deltaChart(items, engineLabel(accuracyEngine));
      return chart ? `${engineBar(engines)}${chart}` : "";
    },
    // the same chart bare, for a card of the Overview's own, with the engines it can be set against
    accuracyChart(state) {
      const { engines, items } = accuracyRows(state);
      return { engines, engine: accuracyEngine, label: engineLabel(accuracyEngine), chart: deltaChart(items, engineLabel(accuracyEngine), true) };
    },
    pick(engine) { accuracyEngine = engine; },
    render(state) {
      element.hidden = state.table !== "checks";
      if (element.hidden) return;
      if (element.dataset.ready !== "1") {
        element.dataset.ready = "1";
        wire();
      }
      openFor = null;
      element.innerHTML = gridPage(state);  // the grid alone; page() keeps Parity, Kernels and the table
    },
  };
})();
