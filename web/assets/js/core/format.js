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

  // one formatter a precision, made once: toLocaleString built a new one for every cell
  numberFormats: {},
  number(value, decimals = 0) {
    const f = (this.numberFormats[decimals] ||= new Intl.NumberFormat(undefined, { minimumFractionDigits: decimals, maximumFractionDigits: decimals }));
    return f.format(Number(value));
  },

  date(isoDate) {
    if (!isoDate) return "";
    const [year, month, day] = isoDate.slice(0, 10).split("-").map(Number);
    this.dateFormat ||= new Intl.DateTimeFormat(undefined, { month: "short", day: "numeric", year: "numeric" });
    return this.dateFormat.format(new Date(year, month - 1, day));
  },

  count(shown, total) {
    const noun = total === 1 ? "row" : "rows";
    return shown === total ? `${total} ${noun}` : `${shown} of ${total} rows`;
  },

  engineTag(id, label) {
    return `<span class="engine-tag" style="--engine-color: ${Pie.engines.colorOf(id)}">${this.escape(label)}</span>`;
  },

  // a workload's name after the setup marks the platform pages give it; Raw and Speculative as a run carry both phases
  workloadMarks: { raw: ["decode", "prefill"], spec: ["spec", "prefill"], raw_decode: ["decode"], raw_prefill: ["prefill"], spec_decode: ["spec"], spec_prefill: ["prefill"], throughput: ["batching"], prefill_batch: ["pbatch"] },

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
    if (column.swept && String(value).includes("–")) {
      return this.sweptTag(value);
    }
    return this.escape(value);
  },

  // a value each machine picks, as macOS marks an adjustable setting: the sliders symbol alone, the range on hover
  sweptTag(range) {
    return `<span class="swept-tag" title="${this.escape(`Picked per machine, ${range}`)}" aria-label="${this.escape(`Picked per machine, ${range}`)}"><svg viewBox="0 0 16 16" aria-hidden="true"><path d="M2 4h12M2 8h12M2 12h12"/><circle cx="10" cy="4" r="1.6"/><circle cx="5" cy="8" r="1.6"/><circle cx="11" cy="12" r="1.6"/></svg></span>`;
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
