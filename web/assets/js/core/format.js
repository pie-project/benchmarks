window.Pie = window.Pie || {};

Pie.format = {
  isEmpty(value) {
    return value === null || value === undefined || value === "";
  },

  escape(value) {
    return String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;");
  },

  number(value, decimals = 0) {
    return Number(value).toLocaleString(undefined, {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    });
  },

  date(isoDate) {
    if (!isoDate) return "";
    const [year, month, day] = isoDate.slice(0, 10).split("-").map(Number);
    return new Date(year, month - 1, day).toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" });
  },

  count(shown, total) {
    const noun = total === 1 ? "row" : "rows";
    return shown === total ? `${total} ${noun}` : `${shown} of ${total} rows`;
  },

  engineTag(id, label) {
    return `<span class="engine-tag" style="--engine-color: ${Pie.engines.colorOf(id)}">${this.escape(label)}</span>`;
  },

  // a workload's name after the setup marks the platform pages give it: Raw and Speculative both their Decode and their Prefill
  workloadMarks: { raw: ["decode", "prefill"], spec: ["spec", "prefill"], throughput: ["batching"], prefill_batch: ["pbatch"] },

  workloadTag(id) {
    const marks = (this.workloadMarks[id] || []).map((mode) => Pie.platform?.degree?.(mode) || "").join("");
    return `<span class="workload-tag">${marks}${this.escape(Pie.store.names.workload(id))}</span>`;
  },

  hardwareTag(id) {
    return `<span class="hardware-tag">${this.escape(id)}</span>`;
  },

  statusLabels: { pass: "Measured", noisy: "Noisy", fail: "Failed", not_run: "Not run", unsupported: "Unsupported", no_fit: "Doesn't fit", no_data: "No data" },

  statusTag(status) {
    return `<span class="status-tag is-${this.escape(status)}">${this.escape(this.statusLabels[status] || status)}</span>`;
  },

  value(column, value) {
    if (this.isEmpty(value)) {
      return "—";
    }
    if (column.type === "number") {
      return this.number(value, column.decimals);
    }
    if (column.status) {
      return this.statusTag(value);
    }
    if (column.type === "reference") {
      return this.reference(column, value);
    }
    return this.escape(value);
  },

  reference(column, id) {
    if (column.table === "engines") {
      return this.engineTag(id, Pie.store.names.engine(id));
    }
    if (column.table === "hardware") {
      return this.hardwareTag(id);
    }
    if (column.table === "workloads") {
      return this.workloadTag(id);
    }
    return this.escape(Pie.store.names.of(column.table, id));
  },

  option(column, value) {
    if (column.status) {
      return this.statusTag(value);
    }
    if (column.type === "reference") {
      return this.reference(column, value);
    }
    return this.escape(value);
  },
};
