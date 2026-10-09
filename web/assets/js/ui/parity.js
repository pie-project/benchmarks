window.Pie = window.Pie || {};

(() => {
  const { format, store } = Pie;
  const element = document.getElementById("parity");
  const RANK = { pie: 0, mlxlm: 1, splash: 2, llamacpp: 3, ollama: 4 };

  const pct = (value) => (value == null ? "–" : `${(value * 100).toFixed(1)}%`);
  const pts = (value) => {
    const size = `${Math.abs(value * 100).toFixed(1)} pts`;
    return value > 0 ? `+${size}` : value < 0 ? `−${size}` : `±0.0 pts`;
  };

  // one column per arm, pie first, then by engine; an arm's name is its engine and its weights
  const columns = (rows) => {
    const seen = new Map();
    for (const row of rows) for (const cell of row.arms) if (!seen.has(cell.artifact)) seen.set(cell.artifact, cell);
    return [...seen.values()].sort((a, b) => (RANK[a.engine] ?? 9) - (RANK[b.engine] ?? 9) || a.label.localeCompare(b.label));
  };

  const dot = (engine) => `<span class="parity-dot" style="background: var(--color-engine-${format.escape(engine)}, var(--color-engine-default))"></span>`;

  const badge = (flag) => {
    if (flag === "ok") return `<span class="parity-badge is-ok">ok</span>`;
    if (flag === "mismatch") return `<span class="parity-badge is-mismatch">mismatch</span>`;
    return `<span class="parity-badge is-none">no pie run</span>`;
  };

  // what a mismatch says, in the row: the gap beyond the intervals, or the answers that differ
  const reasons = (row) => {
    const out = [];
    for (const cell of row.arms) {
      if (cell.score_flag === "mismatch") out.push(`${format.escape(cell.label)}: ${pts(cell.diff)} vs pie, beyond ±${pct(cell.tolerance)}`);
      if (cell.agree_flag === "mismatch") out.push(`${format.escape(cell.label)}: answers differ on ${((1 - cell.agree) * 100).toFixed(0)}% of prompts`);
    }
    return out.join("<br>");
  };

  const cellHtml = (cell, pie) => {
    if (!cell) return `<td class="parity-cell is-empty">–</td>`;
    const classes = ["parity-cell"];
    if (cell.score_flag === "mismatch") classes.push("is-mismatch");
    const delta = cell.artifact === pie?.artifact ? "" : `<span class="parity-delta">${pts(cell.diff)} vs pie</span>`;
    let answers = "";
    if (cell.agree != null) {
      answers = `<span class="parity-answers${cell.agree_flag === "mismatch" ? " is-mismatch" : ""}">same answers ${pct(cell.agree)}</span>`;
    } else if (cell.engine === "splash") {
      answers = `<span class="parity-answers">own chat template</span>`;
    } else if (cell.agree_flag === "n/a" && cell.artifact !== pie?.artifact && pie) {
      answers = `<span class="parity-answers">other weights</span>`;
    }
    return `<td class="${classes.join(" ")}" title="${format.escape(cell.label)} · ${format.escape(cell.checkpoint || "")} · ${format.escape(cell.scheme || "")}">
      <span class="parity-score">${pct(cell.score)}</span>
      <span class="parity-ci">95% ${pct(cell.ci_low)}–${pct(cell.ci_high)}</span>
      ${delta}${answers}</td>`;
  };

  const visible = (state, rows) => {
    const query = state.query.trim().toLowerCase();
    return rows.filter((row) => {
      if (state.filters.model?.length && !state.filters.model.includes(row.model)) return false;
      if (state.filters.task?.length && !state.filters.task.includes(row.task)) return false;
      if (!query) return true;
      return [store.names.model(row.model), row.task].some((text) => String(text).toLowerCase().includes(query));
    });
  };

  // one table per model: its own arms as the columns, pie first, then its tasks as the rows
  const modelTable = (name, rows) => {
    const arms = columns(rows);
    const head = `<thead><tr><th>Model</th><th>Task</th>${arms.map((cell) =>
      `<th class="is-numeric">${dot(cell.engine)}${format.escape(cell.label)}<span class="parity-scheme">${format.escape(cell.scheme || "")}</span></th>`).join("")}
      <th>Parity</th></tr></thead>`;
    const body = rows.map((row, index) => {
      const pie = row.arms.find((cell) => cell.engine === "pie");
      const byArt = Object.fromEntries(row.arms.map((cell) => [cell.artifact, cell]));
      const reason = row.flag === "mismatch" ? `<div class="parity-reason">${reasons(row)}</div>` : "";
      return `<tr class="${row.flag === "mismatch" ? "is-mismatch-row" : ""}">
        <td class="parity-model">${index === 0 ? format.escape(name) : ""}</td><td class="is-code">${format.escape(row.task)}</td>
        ${arms.map((col) => cellHtml(byArt[col.artifact], pie)).join("")}
        <td class="parity-flag">${badge(row.flag)}${reason}</td></tr>`;
    }).join("");
    return `<div class="parity-scroll"><table class="parity-table">${head}<tbody>${body}</tbody></table></div>`;
  };

  const render = (state) => {
    const all = (store.tables.parity || {})[state.release] || [];
    element.hidden = state.table !== "quality";
    if (element.hidden) return;
    if (!all.length) {
      element.innerHTML = `<div class="parity-inner"><div class="parity-head"><h2 class="parity-title">Engine parity</h2></div>
        <div class="parity-summary">No quality run under this release yet.</div></div>`;
      return;
    }
    const rows = visible(state, all);
    const mismatches = all.filter((row) => row.flag === "mismatch");
    const compared = all.filter((row) => row.flag !== "no_pie").length;

    const alert = mismatches.length
      ? `<div class="parity-alert" role="status"><strong>Pie disagrees with another engine on ${mismatches.length} of ${compared} compared pairs.</strong>
         Hardware does not change accuracy, so each one points to a bug in pie until shown otherwise.</div>`
      : compared
        ? `<div class="parity-summary">All ${compared} compared pairs agree with pie: scores within their intervals, and answers the same where the weights are the same.</div>`
        : `<div class="parity-summary">No pie score to compare with yet for this release.</div>`;

    const groups = new Map();
    for (const row of rows) {
      if (!groups.has(row.model)) groups.set(row.model, []);
      groups.get(row.model).push(row);
    }
    const tables = [...groups].map(([model, list]) => `<div class="parity-model-block">${modelTable(store.names.model(model), list)}</div>`).join("");

    element.innerHTML = `<div class="parity-inner">
      <div class="parity-head"><h2 class="parity-title">Engine parity</h2>
      <span class="parity-note">Same model, same questions. Each score is compared with pie; the interval is 95%.</span></div>
      ${alert}${tables || `<div class="parity-summary">No scores match these filters.</div>`}</div>`;
  };

  Pie.parity = { element, render };
})();
