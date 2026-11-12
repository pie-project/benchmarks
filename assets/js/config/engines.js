window.Pie = window.Pie || {};

Pie.engines = {
  primary: "pie",

  colors: {
    pie: "var(--color-engine-pie)",
    llamacpp: "var(--color-engine-llamacpp)",
    mlxlm: "var(--color-engine-mlxlm)",
    splash: "var(--color-engine-splash)",
    vllm: "var(--color-engine-vllm)",
    "vllm-metal": "var(--color-engine-vllm-metal)",
    sglang: "var(--color-engine-sglang)",
  },

  colorOf(id) {
    // an engine the palette has no token for brings its color in the data (tools/webdb.py ENGINE_COLOR)
    const own = (Pie.store?.tables?.engines || []).find((e) => e.id === id)?.color;
    return this.colors[id] || own || "var(--color-engine-default)";
  },

  isPrimary(id) {
    return id === this.primary;
  },
};
