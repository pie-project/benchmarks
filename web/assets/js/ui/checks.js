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
    const cell = (r) => (!r ? '<td class="qc-none">–</td>' : `
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

  const accuracyTable = (state) => {
    const { engines, tag, items } = accuracyRows(state);
    if (!items.length) return empty("No accuracy scores to compare yet.");
    const picker = engines.length > 1 ? `
      <div class="view-toggle qc-picker" role="group" aria-label="Engine">${engines.map((e) =>
        `<button type="button" data-engine="${esc(e)}" class="${e === accuracyEngine ? "is-active" : ""}" aria-pressed="${e === accuracyEngine}">${esc(engineLabel(e))}</button>`).join("")}</div>` : "";
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
    return `${picker}
      <div class="qc-scroll"><table class="qc-table qc-accuracy">
        <thead><tr><th class="qc-lead">Model</th><th>Task</th><th class="qc-num">pie</th><th class="qc-num">${esc(other)}</th><th class="qc-num">Delta</th><th>Parity</th></tr></thead>
        <tbody>${body}</tbody></table></div>
      <p class="qc-foot">Release ${esc(tag)}. Delta is ${esc(other)} minus pie, in points. A mismatch is a gap wider than both 95% intervals together, or under 95% identical answers on the same weights.</p>`;
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
      const target = event.target.closest("[data-tip]");
      if (!target) { tooltip.hidden = true; return; }
      tooltip.textContent = target.dataset.tip;
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
    render(state) {
      element.hidden = state.table !== "checks";
      if (element.hidden) return;
      if (element.dataset.ready !== "1") {
        element.dataset.ready = "1";
        wire();
      }
      openFor = null;
      element.innerHTML = page(state);
    },
  };
})();
