window.Pie = window.Pie || {};

(() => {
  const text = (key, label, group, options = {}) => ({ key, label, group, type: "text", ...options });
  const number = (key, label, group, unit = "", decimals = 1, options = {}) => ({ key, label, group, type: "number", unit, decimals, ...options });
  const reference = (key, label, group, table, options = {}) => ({ key, label, group, type: "reference", table, ...options });

  Pie.sections = [
    { id: "home", label: "General" },
    { id: "platforms", label: "Platforms" },
    { id: "measurements", label: "Measurements" },
    { id: "catalog", label: "Catalog" },
  ];

  Pie.schema = {
    welcome: {
      label: "Welcome",
      section: "home",
      view: "welcome",  // not a table: why the numbers can be trusted
      filters: [],
      columns: [],
    },
    inferlets: {
      label: "Inferlets",
      section: "home",
      view: "inferlets",  // not a table yet: the page is under development
      filters: [],
      columns: [],
    },
    all_hardware: {
      label: "All hardware",
      section: "platforms",
      view: "platform",
      tint: "#0a84ff",  // every platform's machines, grouped by platform
      filters: [],
      columns: [],
    },
    mac: {
      label: "Apple Silicon",
      section: "platforms",
      view: "platform",
      platform: "mac",
      tint: "#636366",
      filters: [],
      columns: [],
    },
    tpu: {
      label: "Google TPU",
      section: "platforms",
      view: "platform",
      platform: "tpu",
      tint: "#4285f4",
      filters: [],
      columns: [],
    },
    nvidia: {
      label: "NVIDIA GPU",
      section: "platforms",
      view: "platform",
      platform: "nvidia",
      tint: "#76b900",
      filters: [],
      columns: [],
    },
    amd: {
      label: "AMD GPU",
      section: "platforms",
      view: "platform",
      platform: "amd",
      tint: "#ed1c24",
      filters: [],
      columns: [],
    },
    cerebras: {
      label: "Cerebras",
      section: "platforms",
      view: "platform",
      platform: "cerebras",
      tint: "#f05a28",
      filters: [],
      columns: [],
    },
    android: {
      label: "Android",
      section: "platforms",
      view: "platform",
      platform: "android",
      tint: "#3ddc84",
      filters: [],
      columns: [],
    },
    web: {
      label: "WebGPU",
      section: "platforms",
      view: "platform",
      platform: "web",
      tint: "#5b8def",
      filters: [],
      columns: [],
    },
    results: {
      label: "Results",
      section: "measurements",
      filters: ["hardware", "engine", "model", "workload", "status"],
      numbered: true,
      columns: [
        reference("engine", "Engine", "Setup", "engines"),
        reference("model", "Model", "Setup", "models"),
        reference("hardware", "Hardware", "Setup", "hardware"),
        reference("workload", "Workload", "Setup", "workloads"),
        text("status", "Status", "Setup", { status: true }),
        text("release", "Release", "Setup", { code: true }),
        text("scheme", "Quantization", "Setup", { code: true }),
        number("decode_tok_s", "Decode", "Speed", "tok/s", 1),
        number("prefill_tok_s", "Prefill", "Speed", "tok/s", 0, {
          // under load the first token waits behind other requests, so no fair prefill rate exists
          na: (row) => row.workload === "throughput",
          naHint: "Not measured under load: with 32 requests at once, time to first token is mostly queueing, not prefill",
        }),
        number("output_tok_s", "Output", "Speed", "tok/s", 1),
        number("ttft_ms_p50", "TTFT p50", "Latency", "ms", 0),
        number("ttft_ms_p99", "TTFT p99", "Latency", "ms", 0),
        number("itl_ms_p50", "ITL p50", "Latency", "ms", 2),
        number("itl_ms_p99", "ITL p99", "Latency", "ms", 2),
        number("latency_ms_p50", "E2E p50", "Latency", "ms", 0),
        number("latency_ms_p99", "E2E p99", "Latency", "ms", 0),
        number("resident_gib", "Memory", "Resources", "GiB", 1),
        number("load_s", "Load time", "Resources", "s", 1),
        text("commit", "pie commit", "Run", { code: true }),
        text("measured", "Measured", "Run", { code: true }),
        text("note", "Note", "Run", { wide: true }),
      ],
    },

    quality: {
      label: "Quality",
      section: "measurements",
      filters: ["model", "engine", "task", "status"],
      numbered: true,
      columns: [
        reference("engine", "Engine", "Setup", "engines"),
        text("status", "Status", "Setup", { status: true }),
        reference("model", "Model", "Setup", "models"),
        text("task", "Task", "Setup"),
        text("release", "Release", "Setup", { code: true }),
        text("version", "Version", "Setup", { code: true }),
        text("artifact", "Weights", "Setup", { code: true }),
        number("score", "Score", "Result", "", 3),
        number("ci_low", "95% low", "Result", "", 3),
        number("ci_high", "95% high", "Result", "", 3),
        number("n", "Questions", "Result", "", 0),
        number("minutes", "Minutes", "Run", "", 1),
        text("date", "Date", "Run", { code: true }),
        text("note", "Note", "Run", { wide: true }),
      ],
    },


    hardware: {
      label: "Hardware",
      section: "catalog",
      filters: ["location", "class", "backend"],
      columns: [
        text("name", "Name", "Identity"),
        text("resource", "Resource", "Identity"),
        text("id", "ID", "Identity", { code: true }),
        text("class", "Class", "Identity"),
        text("location", "Location", "Identity"),
        text("vendor", "Vendor", "Identity"),
        text("backend", "Backend", "Identity"),
        text("arch", "Arch", "Specs", { code: true }),
        number("count", "Devices", "Specs", "", 0),
        number("memory_gib", "Memory", "Specs", "GiB", 0),
        number("bandwidth_gbs", "Bandwidth", "Specs", "GB/s", 0),
        number("gpu_cores", "GPU cores", "Specs", "", 0),
        text("interconnect", "Interconnect", "Specs"),
        number("_results", "Results", "Coverage", "", 0),
      ],
    },

    engines: {
      label: "Engines",
      section: "catalog",
      filters: [],
      columns: [
        reference("id", "Engine", "Identity", "engines"),
        text("version", "Version", "Identity", { code: true }),
        text("license", "License", "Identity"),
        text("repo", "Repo", "Identity", { code: true }),
        text("os", "OS", "Support"),
        text("formats", "Formats", "Support"),
        text("speculative", "Speculative", "Features", { wide: true }),
        number("_results", "Results", "Coverage", "", 0),
      ],
    },

    models: {
      label: "Models",
      section: "catalog",
      filters: ["suite", "family", "architecture"],
      columns: [
        text("name", "Name", "Identity"),
        text("suite", "CI suite", "Identity", { hint: "Targeted models run in every release; Full adds the rest" }),
        text("family", "Family", "Identity", { code: true }),
        text("architecture", "Architecture", "Shape"),
        text("ssd_streaming", "SSD streaming", "Shape"),
        text("draft", "Draft", "Shape", { hint: "pie decodes single-stream rows with a drafter (speculative decoding)" }),
        number("params_b", "Params", "Shape", "B", 1),
        number("active_b", "Active", "Shape", "B", 1),
        number("size_gib", "4-bit size", "Shape", "GiB", 1),
        number("needs_gib", "Needs", "Shape", "GiB", 1),
        text("schemes", "Quantizations", "Weights", { code: true }),
        number("artifacts", "Weight files", "Weights", "", 0),
        text("base_model", "Source", "Identity", { code: true }),
        number("_results", "Results", "Coverage", "", 0),
      ],
    },

    workloads: {
      label: "Workloads",
      section: "catalog",
      filters: [],
      columns: [
        text("label", "Workload", "Identity"),
        number("concurrency", "Parallel requests", "Shape", "", 0),
        number("prompt_tokens", "Prompt", "Shape", "tok", 0),
        number("output_tokens", "Output", "Shape", "tok", 0),
        text("benchmark", "Benchmark", "Identity", { code: true }),
        number("_results", "Results", "Coverage", "", 0),
      ],
    },

    quality_tasks: {
      label: "Benchmarks",
      section: "catalog",
      filters: [],
      columns: [
        text("task", "Task", "Identity", { code: true }),
        text("description", "What it tests", "Identity", { wide: true }),
        text("source", "Questions from", "Identity", { code: true }),
        text("scoring", "Scored by", "Method"),
        number("max_tokens", "Answer budget", "Method", "tok", 0),
      ],
    },
  };
})();
