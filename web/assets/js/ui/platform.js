window.Pie = window.Pie || {};

// A platform page: its machines down, the suite's models across, each cell the picked engine against the
// fastest other engine on that machine (single request). Hovering a cell lists every engine's number.
(() => {
  const element = document.getElementById("platform");
  const tooltip = document.getElementById("chart-tooltip");
  const esc = (s) => Pie.format.escape(String(s ?? ""));
  const names = () => Pie.store.names;

  const METRICS = [
    { id: "decode", label: "Decode", key: "decode_tok_s", unit: "tok/s", higher: true },
    { id: "prefill", label: "Prefill", key: "prefill_tok_s", unit: "tok/s", higher: true },
    { id: "ttft", label: "TTFT", key: "ttft_ms_p50", unit: "ms", higher: false },
  ];
  let onChange = () => {};

  const macName = (id) => {
    const hw = Pie.store.index.hardware[id];
    if (!hw) return id;
    return `${String(hw.name).replace(/^Apple\s+/, "")}${hw.memory_gib ? ` ${hw.memory_gib} GB` : ""}`;
  };
  const value = (n, unit) => {
    const v = n >= 100 ? Math.round(n).toLocaleString() : n.toLocaleString(undefined, { maximumFractionDigits: 1 });
    return `${v} ${unit}`;
  };
  const signed = (p) => {
    const pct = Math.round(p * 100);
    return pct > 0 ? `+${pct}%` : pct < 0 ? `−${Math.abs(pct)}%` : "0%";
  };

  // pie's advantage over the best other engine: a speed ratio, or the inverse for a time
  const cell = (rows, metric, base) => {
    const pie = rows.find((r) => r.engine === base && r[metric.key]);
    const others = rows.filter((r) => r.engine !== base && r[metric.key]);
    if (!pie || !others.length) return null;
    const best = others.reduce((a, b) => ((metric.higher ? b[metric.key] > a[metric.key] : b[metric.key] < a[metric.key]) ? b : a));
    const gain = metric.higher ? pie[metric.key] / best[metric.key] - 1 : best[metric.key] / pie[metric.key] - 1;
    return { pie, best, gain, all: [pie, ...others] };
  };

  const tint = (gain) => {
    const strength = Math.min(Math.abs(gain) / 0.5, 1);
    return `--strength: ${(0.14 + 0.46 * strength).toFixed(2)}`;
  };

  const tip = (mac, model, metric, c) => {
    const order = [...c.all].sort((a, b) => (metric.higher ? b[metric.key] - a[metric.key] : a[metric.key] - b[metric.key]));
    return [`${names().model(model)} on ${macName(mac)}`, `${metric.label}, single request`,
      ...order.map((r) => `${names().engine(r.engine)}  ${value(r[metric.key], metric.unit)}${r === c.best ? "  (fastest other)" : ""}`)].join("\n");
  };

  Pie.platform = {
    element,

    onChange(handler) {
      onChange = handler;
    },

    // returns the number of machines and models shown, for the toolbar subtitle
    render(state) {
      const metric = METRICS.find((m) => m.id === state.platform.metric) || METRICS[0];
      const base = Pie.engines.primary;
      const snapshot = Pie.store.snapshot(state.release).filter((r) => r.workload === "single");
      const rows = snapshot.filter(Pie.store.isMeasured);
      const macs = Pie.store.tables.hardware.map((hw) => hw.id);
      const query = state.query.trim().toLowerCase();
      const models = Pie.store.tables.models.map((m) => m.id).filter((id) => Pie.store.inSuite(id))
        .filter((id) => !query || names().model(id).toLowerCase().includes(query));
      const noFit = Pie.store.tables.no_fit || {};

      const cells = [];
      const body = macs.map((mac) => `<tr><th class="platform-row" scope="row">${esc(macName(mac))}</th>${models.map((model) => {
        const here = rows.filter((r) => r.hardware === mac && r.model === model);
        const c = cell(here, metric, base);
        if (c) {
          cells.push(c.gain);
          return `<td><span class="platform-cell ${c.gain >= 0 ? "is-ahead" : "is-behind"}" style="${tint(c.gain)}" data-tip="${esc(tip(mac, model, metric, c))}">${signed(c.gain)}</span></td>`;
        }
        const needs = noFit[mac]?.[model]?.[base];
        // why there is nothing: too big, or the reason the results table gives for pie's row
        const own = snapshot.find((r) => r.hardware === mac && r.model === model && r.engine === base);
        const why = needs ? `Doesn't fit: needs about ${Math.round(needs)} GB` : own?.note || "No data yet";
        return `<td><span class="platform-cell is-empty${needs ? " is-nofit" : ""}" data-tip="${esc(`${names().model(model)} on ${macName(mac)}\n${why}`)}">${needs ? "Doesn't fit" : "–"}</span></td>`;
      }).join("")}</tr>`).join("");

      const ahead = cells.filter((g) => g >= 0).length;
      const sorted = [...cells].sort((a, b) => a - b);
      const median = sorted.length ? sorted[sorted.length >> 1] : null;
      const head = `<tr><th class="platform-corner" scope="col">Mac</th>${models.map((model) => {
        const m = Pie.store.index.models[model] || {};
        const sub = [m.family, m.params_b ? `${m.params_b}B` : ""].filter(Boolean).join(" · ");
        return `<th scope="col"><span class="platform-model">${esc(names().model(model))}</span><span class="platform-sub">${esc(sub)}</span></th>`;
      }).join("")}</tr>`;

      element.innerHTML = `
        <div class="platform-bar">
          <div class="view-toggle" role="group" aria-label="Metric">
            ${METRICS.map((m) => `<button type="button" class="${m === metric ? "is-active" : ""}" data-metric="${m.id}" aria-pressed="${m === metric}">${m.label}</button>`).join("")}
          </div>
          <span class="platform-key is-ahead"><i></i>${esc(names().engine(base))} ahead</span>
          <span class="platform-key is-behind"><i></i>${esc(names().engine(base))} behind</span>
          <span class="platform-key"><i class="is-dash">–</i>No data</span>
          <span class="platform-summary">${cells.length ? `${esc(names().engine(base))} ahead in <b>${ahead}</b> of ${cells.length} · median <b>${signed(median)}</b>` : ""}</span>
        </div>
        <div class="platform-scroll">
          <table class="platform-table"><thead>${head}</thead><tbody>${body}</tbody></table>
        </div>`;
      return { macs: macs.length, models: models.length, metric };
    },

    bind(state) {
      element.addEventListener("click", (event) => {
        const button = event.target.closest("[data-metric]");
        if (!button) return;
        state.platform.metric = button.dataset.metric;
        onChange();
      });
      element.addEventListener("pointermove", (event) => {
        const mark = event.target.closest("[data-tip]");
        if (!mark) {
          tooltip.hidden = true;
          return;
        }
        tooltip.textContent = mark.dataset.tip;
        tooltip.hidden = false;
        const x = Math.min(event.clientX + 14, window.innerWidth - tooltip.offsetWidth - 8);
        const y = Math.min(event.clientY + 14, window.innerHeight - tooltip.offsetHeight - 8);
        tooltip.style.left = `${Math.max(8, x)}px`;
        tooltip.style.top = `${Math.max(8, y)}px`;
      });
      element.addEventListener("pointerleave", () => (tooltip.hidden = true));
      element.addEventListener("scroll", () => (tooltip.hidden = true), true);
    },
  };
})();
