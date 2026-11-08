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

  let accuracyPlatform = null;  // the platform the Accuracy grid shows: its own pie code (Metal, CUDA, XLA, ROCm)
  let openFor = null;  // the kernel row whose failing tests are listed in the popover

  const empty = (text) => `<p class="qc-empty">${esc(text)}</p>`;
  // a hover card in the platform pages' own format: the subject in bold, then a row per figure, its name on the left and
  // its value on the right; a score row carries its engine's dot, the figures under it are dimmed; the verdict closes the
  // card under a rule, red where pie scores lower and green where it holds. Rows are [name, value, dim, engine];
  // carried as HTML in data-tip-html
  const card = (title, rows, off = false, ok = "") => `<div class="tip-title">${esc(title)}</div><div class="tip-rows qc-tip-rows">${rows
    .filter(Boolean).map(([k, v, dim, engine]) => `<div class="tip-row${dim ? " is-slack" : ""}">${engine ? `<span class="tip-dot" style="background: ${Pie.engines.colorOf(engine)}"></span>` : "<span></span>"}<span class="tip-name">${esc(k)}</span><span class="tip-value">${esc(v)}</span></div>`).join("")}</div>${off
    ? `<div class="tip-foot qc-tip-off">${esc(off === true ? "Mismatch" : off)}</div>` : ok ? `<div class="tip-foot qc-tip-ok">${esc(ok)}</div>` : ""}`;
  const range = (a) => (isNum(a?.ci_low) && isNum(a?.ci_high) ? `${pct(a.ci_low)} – ${pct(a.ci_high)}` : "");
  const section = (title, caption, body) => `
    <section class="qc-section">
      <h2>${esc(title)}</h2>
      <p class="qc-caption">${esc(caption)}</p>
      ${body}
    </section>`;

  // a miniature keeps a few of the model's layers: a count, or the kept range ("0-4")
  const layersText = (layers) => (isNum(layers) ? `${layers} layers kept` : layers ? `layers ${layers} kept` : "");
  const miniBadge = (row) => `<span class="qc-badge" title="${esc(["Model slice", layersText(row.layers)].filter(Boolean).join(": "))}">Slice</span>`;

  // ---- parity: a row per model, a column per device ----------------------------------------------------
  const parityTip = (r) => [
    `${engineLabel(r.engine || "pie")} vs ${engineLabel(r.ref_engine)} on ${hardwareName(r.platform)}`,
    `KL mean ${kl(r.kl_mean)}, p50 ${kl(r.kl_p50)}`,
    `KL p99 ${kl(r.kl_p99)}, max ${kl(r.kl_max)}`,
    `Top-1 agreement ${pct(r.top1_agree)}${r.top1_agree_decisive != null ? `, ${pct(r.top1_agree_decisive)} where ${engineLabel(r.ref_engine)} leads by 0.5 nats (${r.decisive_positions})` : ""}`,
    r.ref_top1_p != null ? `${engineLabel(r.ref_engine)} top-1 holds ${pct(r.ref_top1_p)}, its top-20 ${pct(r.ref_topk_mass)}` : "",
    `Exact match ${pct(r.exact_match, 0)}`,
    `${r.positions ?? "–"} positions over ${r.prompts ?? "–"} prompts${r.misaligned_texts ? `, ${r.misaligned_texts} misaligned` : ""}`,
    `Pie ${short(r.version) || "–"}, ${engineLabel(r.ref_engine)} ${r.ref_version || "–"}`,
    r.miniature ? ["Model slice", layersText(r.layers)].filter(Boolean).join(": ") : "",
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
      <thead><tr><th class="qc-lead">Platform</th><th class="qc-num">Passed</th><th class="qc-num">Failed</th><th class="qc-num">Ignored</th><th class="qc-num">Worst error</th><th>Pie</th></tr></thead>
      <tbody>${body}</tbody></table></div>`;
  };

  const failingList = (row) => `
    <div class="qc-pop-head">${esc(hardwareName(row.platform))}: ${esc((row.failing || []).length)} failing</div>
    <ul>${(row.failing || []).map((f) => `<li><code>${esc(f.name)}</code>${f.message ? `<span>${esc(f.message)}</span>` : ""}</li>`).join("") || "<li>No names recorded.</li>"}</ul>`;

  // ---- accuracy: pie beside every engine on the same weights, per platform ------------------------------
  // the platforms whose pie code differs, in the sidebar's order; a row without a platform was scored on the quality Mac
  const PLATFORMS = ["mac", "nvidia", "amd", "tpu", "web"].filter((p) => !Pie.hiddenPlatforms.has(p));
  const familyOf = (row) => { const hw = row.platform && Pie.store.index.hardware[row.platform]; return hw ? Pie.platformOf(hw) : "mac"; };
  const platformLabel = (id) => Pie.schema[id]?.label || id;
  // the closest reference first: an engine on Pie's own weights and chat template (mlx-lm, vLLM), then the rest
  const RANK = { mlxlm: 0, vllm: 0, sglang: 1, splash: 2, llamacpp: 3 };
  const byRank = (a, b) => (RANK[a.arm.engine] ?? 9) - (RANK[b.arm.engine] ?? 9);
  // red only where pie answers worse: its score below the engine's beyond both intervals. Only final answers count:
  // how an answer is worded is not shown (two correct engines round differently and the wording follows)
  const isOff = (arm) => arm.score_flag === "mismatch";
  // the newest release with comparisons on the picked platform; the viewer's release first. Only arms compared with
  // pie (same weights, same machine) count: the rest have no gap
  const accuracyRows = (state) => {
    const byTag = tables().parity || {};
    // the releases first; then a device's own quality tag (0.5.3-b5-amd), so a platform scored apart still shows
    const tags = [...new Set([state.release, ...(tables().tags || []).map((t) => t.id), ...Object.keys(byTag)])].filter((t) => byTag[t]?.length);
    const arms = (tag) => byTag[tag].flatMap((row) => row.arms.filter((a) => a.engine !== "pie" && isNum(a.diff)).map((a) => ({ row, arm: a, platform: familyOf(row) })));
    const platforms = PLATFORMS.filter((p) => tags.some((t) => arms(t).some((x) => x.platform === p)));
    if (!platforms.includes(accuracyPlatform)) accuracyPlatform = platforms[0] || null;
    const tag = tags.find((t) => arms(t).some((x) => x.platform === accuracyPlatform));
    return { platforms, tag, items: tag ? arms(tag).filter((x) => x.platform === accuracyPlatform).sort(byRank) : [] };
  };
  const platformBar = (platforms) => platforms.length ? `<span class="platform-compare qc-picker" role="group" aria-label="Platform">${platforms.map((p) =>
    `<button type="button" data-qc-platform="${esc(p)}" class="plain-button${p === accuracyPlatform ? " is-active" : ""}" aria-pressed="${p === accuracyPlatform}">${esc(platformLabel(p))}</button>`).join("")}</span>` : "";

  const flagTag = (flag) => (flag === "mismatch" ? '<span class="qc-flag is-mismatch">Mismatch</span>'
    : flag === "ok" ? '<span class="qc-flag is-ok">Match</span>' : '<span class="qc-flag">–</span>');

  // the gap at a glance: one row per model and task, a dot at the reference's score minus pie's (in points), a line for
  // its 95% range (both intervals combined) and a grey band for the tolerance; a dot outside its band is a mismatch
  const deltaChart = (items, bare = false) => {
    const half = (a) => (isNum(a?.ci_low) && isNum(a?.ci_high) ? (a.ci_high - a.ci_low) / 2 : 0);
    const engines = [...new Set(items.map((x) => x.arm.engine))];
    // one engine names itself in the key; several name the engine on each row
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

  const accuracyTable = (state) => {
    const { platforms, tag, items } = accuracyRows(state);
    if (!items.length) return empty("No accuracy scores to compare yet.");
    const body = items.map(({ row, arm }) => {
      const pie = row.arms.find((a) => a.artifact === (arm.vs || row.pie));
      const other = engineLabel(arm.engine);
      const flag = isOff(arm) ? "mismatch" : arm.score_flag;
      const tip = [`Pie ${pie ? `${pct(pie.score)} (95% ${pct(pie.ci_low)} to ${pct(pie.ci_high)}, n ${pie.n})` : "not run"}`,
        `${other} ${pct(arm.score)} (95% ${pct(arm.ci_low)} to ${pct(arm.ci_high)}, n ${arm.n})`,
        row.platform ? `On ${hardwareName(row.platform)}` : "",
        isNum(arm.tolerance) ? `Allowed gap ±${(arm.tolerance * 100).toFixed(1)} pts` : ""].filter(Boolean).join("\n");
      return `
      <tr data-tip="${esc(tip)}">
        <th class="qc-lead" scope="row"><span>${esc(Pie.store.names.model(row.model))}</span></th>
        <td>${esc(row.task)}</td>
        <td class="qc-num">${pie ? pct(pie.score) : "–"}</td>
        <td>${esc(other)}</td>
        <td class="qc-num">${pct(arm.score)}</td>
        <td class="qc-num${arm.score_flag === "mismatch" ? " is-off" : ""}">${isNum(arm.diff) ? `${arm.diff > 0 ? "+" : arm.diff < 0 ? "−" : ""}${(Math.abs(arm.diff) * 100).toFixed(1)}` : "–"}</td>
        <td>${flagTag(flag)}</td>
      </tr>`;
    }).join("");
    return `${platforms.length > 1 ? platformBar(platforms) : ""}${deltaChart(items)}
      <div class="qc-scroll"><table class="qc-table qc-accuracy">
        <thead><tr><th class="qc-lead">Model</th><th>Task</th><th class="qc-num">Pie</th><th>Engine</th><th class="qc-num">Its score</th><th class="qc-num">Delta</th><th>Parity</th></tr></thead>
        <tbody>${body}</tbody></table></div>
      <p class="qc-foot">Release ${esc(tag)}, ${esc(platformLabel(accuracyPlatform))}. Delta is the engine minus Pie, in points. Only engines on Pie's weights and machine are compared. A mismatch is pie scoring lower by more than both 95% intervals together; only the final answers count.</p>`;
  };

  // the page: the Performance page's grid, its machines down the side and its models across under their makers, as
  // platform.js lays them out; a model that fits a machine shows Pie's MATH-500 score and its gap to one engine on the
  // same weights and machine, a model slice the KL divergence of Pie's first token from that engine's
  const QUALITY_MAC = "m5-max-128g";  // a score without a platform ran on the quality Mac, as tools/webdb.py says
  const PREFER = { mac: "mlxlm", nvidia: "vllm", amd: "vllm", tpu: "vllm" };  // the one engine each platform sets Pie against
  const byPrefer = (platform, engine) => (a, b) => (engine(b) === PREFER[platform]) - (engine(a) === PREFER[platform]) || (RANK[engine(a)] ?? 9) - (RANK[engine(b)] ?? 9);
  const NOFIT = '<svg class="platform-nofit" viewBox="0 0 16 16" aria-hidden="true"><rect x="2.5" y="2.5" width="11" height="11" rx="2.5"/><path d="M4 12 12 4"/></svg>';
  // a machine's MATH-500 comparison: the viewer's release first, then the newest that scored the model there
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
  // a model slice's first-token KL on a machine: the newest parity row there, its preferred engine first
  const klOf = (mac, model, platform) => (tables().quality_parity || [])
    .filter((r) => r.platform === mac && r.model === model && !r.ref_unsupported && isNum(r.kl_mean))
    .sort((a, b) => byPrefer(platform, (r) => r.ref_engine)(a, b) || String(b.date || "").localeCompare(String(a.date || "")))[0] || null;
  // pass or fail per cell: a slice passes when its first-token distribution stays within 0.15 nats of the reference
  // engine's (kernel and rounding noise sits near 0.001, a wrong layer or template well above 0.15); a full model passes
  // when Pie's MATH-500 score is within 5 points of the reference engine's
  const KL_PASS = 0.15, MATH_PASS = 5;
  // a cell no run can fill says why (support.yaml quality_gaps)
  const gapOf = (mac, model) => (tables().quality_gaps || []).find((g) => [].concat(g.platform).includes(mac) && [].concat(g.model).includes(model))?.reason || "";
  // a full model's allowance: the run's own noise, 5 points only where a run has no noise figure
  const allowed = (g) => (isNum(g.arm.tolerance) ? g.arm.tolerance * 100 : MATH_PASS);
  const MARK = { pass: '<svg class="qc-mark" viewBox="0 0 16 16" aria-label="Pass"><path d="M3.5 8.5l3 3 6-7"/></svg>', fail: '<svg class="qc-mark" viewBox="0 0 16 16" aria-label="Fail"><path d="M4.5 4.5l7 7M11.5 4.5l-7 7"/></svg>' };
  const gridOf = (state, { platform, macs, models }, layout) => {
    // each platform's grid folds its Overall column on its own, the one choice shared with that platform's Performance grid
    const key = platform.id;
    const tight = Pie.state?.platform?.narrowBy?.[key] ?? (Pie.state?.platform?.narrow ?? true);
    const narrowLabel = tight ? "Show Overall and memory" : "Hide Overall and memory";
    // a model slice is what the Performance page marks so: a slice ran there, or the model does not fit
    const nofit = (mac, model) => layout.sliced.has(`${mac}|${model}`) || Boolean(layout.grid[mac]?.[model]?.needs) || Boolean(klOf(mac, model, platform.id)?.miniature);
    const at = {};
    for (const mac of macs) for (const model of models) at[`${mac}|${model}`] = nofit(mac, model) ? { kl: klOf(mac, model, platform.id) } : { score: scoreOf(state, mac, model, platform.id) };
    const signed = (d) => `${d > 0.05 ? "+" : d < -0.05 ? "−" : ""}${Math.abs(d).toFixed(1)}`;
    // a maker's slices and its full models are two bands, as the Performance page splits them
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
    // a machine's eye hides its row, as on Performance: greyed, emptied and moved last, the same machines hidden on both
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
            const tip = card(title, [["Compared", `Pie vs ${engineLabel(r.ref_engine)}`], ["Model slice", layersText(r.layers) || "Yes", true],
              // KL between the two engines' next-token distributions on the same prompts: the first token alone, or older runs' mean over the answer
              [r.answer_tokens === 1 ? "First-token KL" : "KL, answer mean", kl(r.kl_mean)], ["Same top token", pct(r.top1_agree)], ["Prompts", `${r.prompts ?? "–"}`, true],
              r.date ? ["Measured", Pie.format.date(r.date), true] : null]);
            const ok = r.kl_mean < KL_PASS;
            const open = { model: [m], task: [r.task], engine: ["pie", r.ref_engine] };
            return `<td class="is-openable${ok ? "" : " is-over-limit"}" data-col="${esc(m)}" data-open="${esc(JSON.stringify(open))}"><span class="platform-open" aria-hidden="true">See Runs<svg viewBox="0 0 16 16"><path d="M5 11 11 5M6 5h5v5"/></svg></span><span class="platform-cell ${ok ? "is-same" : "is-behind"} is-nofit" data-tip-html="${esc(tip)}">${NOFIT}<span class="platform-main">${MARK[ok ? "pass" : "fail"]}</span></span></td>`;
          }
          if (!g) return `<td data-col="${esc(m)}"><span class="platform-cell is-empty${"kl" in at[`${mac}|${m}`] ? " is-nofit" : ""}"${gapOf(mac, m) ? ` data-tip="${esc(gapOf(mac, m))}"` : ""}>${"kl" in at[`${mac}|${m}`] ? NOFIT : ""}–</span></td>`;
          // what answers "is quality hurt?": both scores, the difference, how much of it is noise, and a verdict in words
          const off = Math.abs(g.d) > allowed(g);
          const tip = card(`${title} · MATH-500`, [["Pie", pct(g.pie.score), false, "pie"], [engineLabel(g.arm.engine), pct(g.arm.score), false, g.arm.engine],
            ["Difference", `${signed(g.d)} pts`, true], isNum(g.arm.tolerance) ? ["Noise", `±${(g.arm.tolerance * 100).toFixed(1)} pts`, true] : null, ["Release", g.tag, true]],
            off ? `Pie is more than ${allowed(g).toFixed(1)} points from ${engineLabel(g.arm.engine)}, beyond noise` : false);
          // a click opens Quality's runs for this model and task, with the engines this cell compares
          const open = { model: [m], task: ["math500"], engine: ["pie", g.arm.engine] };
          // a cross sits on the grid's CI Error red, as a cell above its limit does on Performance
          return `<td class="is-openable${off ? " is-over-limit" : ""}" data-col="${esc(m)}" data-open="${esc(JSON.stringify(open))}"><span class="platform-open" aria-hidden="true">See Runs<svg viewBox="0 0 16 16"><path d="M5 11 11 5M6 5h5v5"/></svg></span><span class="platform-cell ${off ? "is-behind" : "is-same"}" data-tip-html="${esc(tip)}"><span class="platform-main">${MARK[off ? "fail" : "pass"]}</span></span></td>`;
        }).join("")}<td class="platform-fill"></td></tr>`;
    }).join("");
    const cols = `<colgroup><col class="col-machine"><col class="col-model">${models.map(() => '<col class="col-model">').join("")}<col class="col-fill"></colgroup>`;
    return `<table class="platform-table${tight ? " is-tight" : ""}" style="--cols: ${models.length + 1}">${cols}<thead>${makerRow}${head}</thead><tbody>${body}</tbody></table>`;
  };
  // every platform at once, as the compare pages stack theirs: a header bar that folds it, over its own grid; folded
  // or open as on Performance, the one choice for both pages
  const folded = new Proxy({}, { get: (_, id) => Boolean(Pie.state.platform.collapsed?.[id]) });
  const gridPage = (state) => {
    const layout = Pie.platform.render(state, true);
    const sections = layout.sections.filter((g) => PLATFORMS.includes(g.platform?.id));
    shown = sections;  // counted under the page's title
    if (!sections.length) return `<div class="platform-scroll">${empty("No accuracy scores to compare yet.")}</div>`;
    // the Performance page's bar, with only its info button: what a cell compares and what passes
    const bar = `<div class="platform-bar"><button type="button" class="plain-button rules-button" data-rules="quality" aria-expanded="false" aria-label="Test Conditions" title="Test Conditions"><svg viewBox="0 0 16 16" aria-hidden="true"><circle cx="8" cy="8" r="6.5"/><path d="M8 7.2v3.6M8 5.2v.1"/></svg><span class="rules-label">Test Conditions</span></button><span class="platform-bar-side is-end"><span class="platform-key" title="The full model does not fit one machine; a mark beside a check is a model slice&#39;s">${NOFIT}Does not fit</span></span></div>`;
    return `${bar}<div class="platform-scroll">${sections.map((g) => {
      const p = g.platform.id;
      return `<section class="platform-section">
        <div class="platform-group-row platform-section-bar${folded[p] ? " is-collapsed" : ""}" data-qc-fold="${esc(p)}" role="button" aria-expanded="${!folded[p]}">
          <span class="platform-group-bar">
            <span class="platform-group-name">${Pie.platform.badge(p)}<b>${esc(g.platform.label)}</b><span>${g.macs.length} ${g.macs.length === 1 ? "machine" : "machines"}, ${g.models.length} ${g.models.length === 1 ? "model" : "models"}</span></span>
            <svg class="platform-disclosure" viewBox="0 0 8 14" aria-hidden="true"><path d="M1.5 1.5 6.5 7l-5 5.5"/></svg>
          </span>
        </div><div class="platform-section-body"${folded[p] ? " hidden" : ""}><div class="platform-section-scroll">${gridOf(state, g, layout)}</div></div></section>`;
    }).join("")}</div>`;
  };

  const page = (state) => `
    <div class="method-inner qc-inner">
      <header class="method-head qc-head">
        <h1>Quality</h1>
        <p class="method-lede">Whether Pie computes what a reference engine computes, on the same weights and the same device.</p>
      </header>
      ${section("Parity", "KL divergence of Pie's next-token distribution from the reference engine's, mean over answer positions, and how often both pick the same top token.",
        `<div class="qc-banner" role="note"${(tables().quality_parity || []).length ? "" : " hidden"}>Model slices: layers removed to fit one device. For engine-to-engine comparison only, not real model speed.</div>${parityTable()}`)}
      ${section("Kernels", "Pie's kernel tests on each backend, against reference implementations.", kernelsTable())}
      ${section("Accuracy", "Benchmark scores of Pie beside every engine that ran the same weights on the same machine, per platform.", accuracyTable(state))}
      <div class="qc-pop" role="dialog" hidden></div>
    </div>`;

  const closePop = () => {
    openFor = null;
    const pop = element.querySelector(".qc-pop");
    if (pop) pop.hidden = true;
  };

  let openRuns = () => {};
  let shownFor = null;  // the page last drawn, so only a page switch rolls the grid in
  let inherited = null;
  let shown = [];  // the platform sections last drawn  // the grid page left behind, to leave as this one's marks rise
  const wire = () => {
    // makers and models drag as on Performance, the one order kept for both pages
    const wasDrag = Pie.platform.wireColumnDrag(element, () => { Pie.saveView?.(); document.dispatchEvent(new CustomEvent("pie:refresh")); });
    element.addEventListener("click", (event) => {
      if (wasDrag()) return;
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
        // this platform's grid alone; the others keep theirs
        const table = narrow.closest(".platform-table");
        const on = !table.classList.contains("is-tight");
        Pie.state.platform.narrowBy = { ...Pie.state.platform.narrowBy, [narrow.dataset.narrow]: on };
        Pie.saveView?.();
        const label = on ? "Show Overall" : "Hide Overall";
        table.classList.toggle("is-tight", on);
        narrow.setAttribute("aria-pressed", String(on)); narrow.title = label; narrow.setAttribute("aria-label", label);
        return;
      }
      // a platform's bar folds its grid in place, sliding, as the compare pages fold theirs
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
    // a cell's details follow the pointer in the site's chart tooltip
    element.addEventListener("mousemove", (event) => {
      // over the whole cell, its padding too, as on Performance
      const target = event.target.closest("[data-tip], [data-tip-html]") || event.target.closest("td, th")?.querySelector("[data-tip], [data-tip-html]");
      // an HTML card in the platform pages' card format; a plain note as text
      if (!target) { tooltip.hidden = true; tooltip.classList.remove("is-card"); return; }
      if (target.dataset.tipHtml) { tooltip.innerHTML = target.dataset.tipHtml; tooltip.classList.add("is-card"); }
      else { tooltip.textContent = target.dataset.tip; tooltip.classList.remove("is-card"); }
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
    // the accuracy gap, for the Overview's last section: the platform pick and the chart
    accuracyBlock(state) {
      const { platforms, items } = accuracyRows(state);
      const chart = deltaChart(items);
      return chart ? `${platformBar(platforms)}${chart}` : "";
    },
    // the same chart bare, for a card of the Overview's own, with the platforms it can show
    accuracyChart(state) {
      const { platforms, items } = accuracyRows(state);
      return { platforms, platform: accuracyPlatform, label: platformLabel(accuracyPlatform), chart: deltaChart(items, true) };
    },
    pick(platform) { accuracyPlatform = platform; },
    // a cell's click: the Quality runs, filtered to its model, task and engines
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
      element.innerHTML = gridPage(state);  // the grid alone; page() keeps Parity, Kernels and the table
      // the page opened from the sidebar rolls its marks in on the Performance grids' wave
      if (shownFor !== state.table) Pie.platform.waveIn(element, inherited);
      inherited = null;
      shownFor = state.table;
      return { macs: shown.reduce((n, g) => n + g.macs.length, 0), models: new Set(shown.flatMap((g) => g.models)).size };
    },
  };
})();
