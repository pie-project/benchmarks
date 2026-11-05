window.Pie = window.Pie || {};

(() => {
  const text = (key, label, group, options = {}) => ({ key, label, group, type: "text", ...options });
  const number = (key, label, group, unit = "", decimals = 1, options = {}) => ({ key, label, group, type: "number", unit, decimals, ...options });
  const reference = (key, label, group, table, options = {}) => ({ key, label, group, type: "reference", table, ...options });

  Pie.sections = [
    { id: "start", label: "" },  // the home page on its own at the top, under no heading, as a Mac app sets its first page
    { id: "home", label: "Compare" },
    { id: "platforms", label: "Platforms" },
    { id: "measurements", label: "Measurements" },  // open to everyone for now (login: true closes it again)
    { id: "catalog", label: "Catalog" },  // open to everyone for now (login: true closes it again)
    { id: "resources", label: "Resources", login: true },  // how the numbers are worked out, after the data itself
  ];
  // the sections an account opens: hidden, and their pages closed, until the viewer logs in (ui/account.js)
  Pie.signedIn = () => Boolean(Pie.account?.user());
  Pie.isOpen = (table) => Pie.signedIn() || !Pie.sections.find((s) => s.id === Pie.schema[table]?.section)?.login;

  Pie.schema = {
    welcome: {
      label: "Platforms",
      section: "catalog",
      view: "welcome",  // not a table: why the numbers can be trusted
      filters: [],
      columns: [],
    },
    // Inferlets and Services, hidden for now
    // inferlets: {
    //   label: "Inferlets",
    //   tag: "Alpha",  // not yet beta
    //   section: "home",
    //   view: "inferlets",  // not a table yet: the page is under development
    //   filters: [],
    //   columns: [],
    // },
    // services: { label: "Services", tag: "Alpha", section: "home", view: "services", filters: [], columns: [] },
    // the Profiler, hidden for now
    // profiler: {
    //   label: "Profiler",
    //   tag: "Alpha",
    //   section: "home",
    //   view: "profiler",  // not a table: uploaded traces of long workloads, empty until uploads open
    //   filters: [],
    //   columns: [],
    // },
    // every platform's machines in one grid, a header row per platform, every model a column
    // every engine side by side on one model, as Artificial Analysis ranks models
    board: {
      label: "Overview",
      section: "start",
      tint: "#0A84FF",  // a tile in System Settings' blue, as the platforms below wear theirs
      view: "board",
      filters: [],
      columns: [],
    },
    // every machine in one table: pie against the other engines
    // Relative Speed, Tokens per Second and Kernel Efficiency as one page, switched in its bar
    speedups: {
      label: "Performance",
      section: "home",
      tint: "#FF2D55",  // pink
      view: "platform",
      filters: [],
      columns: [],
    },
    // how close the engines come to one another's answers, across every measurement: off for now, Quality Checks shows it
    accuracy: {
      label: "Accuracy",
      section: null,
      view: "accuracy",
      filters: [],
      columns: [],
    },
    // every machine in one table: the engine's own tokens per second
    tps: {
      label: "Tokens per Second",
      section: null,  // a view of Speed now; the page stays for links
      tint: "#FF9F0A",  // orange
      view: "platform",
      compare: "tps",
      filters: [],
      columns: [],
    },
    // every machine in one table: each engine against the hardware's theoretical limit
    all_hardware: {
      label: "Kernel Efficiency",
      section: null,  // a view of Speed now; the page stays for links
      tint: "#30B0C7",  // teal
      view: "platform",
      compare: "ceiling",
      filters: [],
      columns: [],
    },
    // pie against a reference engine: token distributions, kernel tests and benchmark scores side by side
    checks: {
      label: "Quality",
      title: "Quality",
      section: "home",  // in Compare, where Accuracy was
      tint: "#7a4cf5",  // Intelligence's purple
      view: "checks",
      filters: [],
      columns: [],
    },
    // how well models answer: Artificial Analysis measures it, so the sidebar links there rather than to a page of ours
    scores: {
      label: "Intelligence",  // the model's own smarts (Artificial Analysis's Intelligence Index), not an engine's
      section: null,  // off the sidebar
      href: "https://artificialanalysis.ai/",
      tint: "#7a4cf5",  // Artificial Analysis's purple, as the platforms' tiles wear theirs
      filters: [],
      columns: [],
    },
    mac: {
      label: "Apple Silicon",
      short: "Mac",  // as the tables name it
      section: "platforms",
      view: "platform",
      platform: "mac",
      tint: "#636366",
      filters: [],
      columns: [],
    },
    nvidia: {
      label: "NVIDIA GPU",
      short: "NVIDIA",  // as the tables name it
      section: "platforms",
      view: "platform",
      platform: "nvidia",
      tint: "#76b900",
      filters: [],
      columns: [],
    },
    amd: {
      label: "AMD GPU",
      short: "AMD",  // as the tables name it
      section: "platforms",
      view: "platform",
      platform: "amd",
      tint: "#ed1c24",
      filters: [],
      columns: [],
    },
    tpu: {
      label: "Google TPU",
      short: "TPU",  // as the tables name it
      section: "platforms",
      view: "platform",
      platform: "tpu",
      tint: "#4285f4",
      filters: [],
      columns: [],
    },
    cerebras: {
      label: "Cerebras",
      short: "Cerebras",  // as the tables name it
      section: null,  // no page for now; still a row in the Platforms list ("platforms" to bring it back)
      view: "platform",
      platform: "cerebras",
      tint: "#f05a28",
      filters: [],
      columns: [],
    },
    android: {
      label: "Mobile",
      short: "Mobile",  // as the tables name it
      section: null,  // no page until a machine is measured; still a row in the Platforms list
      view: "platform",
      platform: "android",
      tint: "#1C1C1E",  // black: no other platform wears it
      filters: [],
      columns: [],
    },
    web: {
      label: "Browser",
      short: "Browser",  // as the tables name it
      section: null,  // no page until a machine is measured; still a row in the Platforms list
      view: "platform",
      platform: "web",
      tint: "#AEAEB2",  // light gray
      filters: [],
      columns: [],
    },
    results: {
      label: "Performance",
      section: "measurements",
      filters: ["engine", "model", "platform", "hardware", "workload", "status"],  // in the order of the columns they filter
      numbered: true,
      columns: [
        reference("engine", "Engine", "Setup", "engines"),
        reference("model", "Model", "Setup", "models"),
        text("platform", "Platform", "Setup"),
        reference("hardware", "Hardware", "Setup", "hardware"),
        reference("workload", "Workload", "Setup", "workloads"),
        text("status", "Status", "Setup", { status: true }),
        text("release", "Release", "Setup", { code: true }),
        text("scheme", "Quantization", "Setup", { code: true }),
        // a datacenter model cut to fit one device: how much of it ran ("8 of 93 layers"), and its own size
        text("miniature", "Model slice", "Setup", { hint: "Layers kept when a model too big for the device ran as a slice; for engine-to-engine comparison only" }),
        number("mini_params_b", "Mini size", "Setup", "B", 1, { hint: "The cut-down model's parameters (an estimate from the full model's)" }),
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
        text("commit", "Pie commit", "Run", { code: true }),
        text("measured", "Measured", "Run", { code: true }),
        text("note", "Note", "Run", { wide: true }),
      ],
    },

    quality: {
      label: "Quality",
      section: "measurements",
      filters: ["engine", "status", "model", "task"],  // in the order of the columns they filter
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

    // a measurement that looks wrong, reported by a visitor and closed by a maintainer with its fix
    reports: {
      label: "Pie Reports",
      section: "measurements",
      view: "reports",
      filters: [],
      columns: [],
    },
    // how the benchmark is run, as prose: the model slices behind the datacenter rows
    approach: {
      label: "Methodology",
      section: "measurements",
      view: "approach",
      filters: [],
      columns: [],
    },
    methods: {
      label: "Roofline",
      section: null,  // now a Methodology chapter (approach.js); the page stays for old links
      view: "methods",  // how each theoretical limit is worked out, a table of formulas per workload
      filters: [],
      columns: [],
    },
    // how a model is judged to fit a machine, the same table as Roofline
    fit: {
      label: "Memory",
      section: null,  // now a Methodology chapter (approach.js); the page stays for old links
      view: "methods",
      filters: [],
      columns: [],
    },

    // the Limit calculator, hidden for now; its code stays (methodology.js), and Pie.ceiling there still feeds the grid
    // methodology: {
    //   label: "Limit",
    //   title: "Theoretical Limit",  // the page title in the top bar; the sidebar keeps the short label
    //   tag: "Beta",  // still under development
    //   section: "measurements",
    //   view: "methodology",  // not a table: a calculator of the theoretical maximum
    //   filters: [],
    //   columns: [],
    // },

    hardware: {
      label: "Hardware",
      section: "catalog",
      numbered: true,
      filters: [],
      columns: [
        text("name", "Name", "Identity"),
        text("platform", "Platform", "Identity"),
        text("resource", "Resource", "Identity"),
        text("full_name", "Full name", "Identity"),
        text("id", "ID", "Identity", { code: true }),
        text("location", "Location", "Identity"),
        text("runs", "CI runs", "Identity", { tags: true }),
        text("vendor", "Vendor", "Identity"),
        text("backend", "Backend", "Identity"),
        text("arch", "Arch", "Specs", { code: true }),
        number("count", "Devices", "Specs", "", 0),
        number("memory_gib", "Memory", "Specs", "GiB", 0),
        text("memory_type", "Memory type", "Specs"),
        number("bandwidth_gbs", "Bandwidth", "Specs", "GB/s", 0),
        number("cpu_cores", "CPU cores", "Specs", "", 0),
        number("gpu_cores", "GPU cores", "Specs", "", 0),
        number("tflops_fp16", "Compute", "Specs", "TFLOPS", 1, {
          info: "Peak fp16 matrix math, GPU only. An estimate, not exact: other units, such as the neural accelerators or the Neural Engine, can add more.",
        }),
        number("power_w", "Power", "Specs", "W", 0),
        text("interconnect", "Interconnect", "Specs"),
        text("year", "Year", "Specs"),
        number("_results", "Results", "Coverage", "", 0),
      ],
    },

    engines: {
      label: "Engines",
      section: "catalog",
      numbered: true,
      filters: [],
      columns: [
        reference("id", "Engine", "Identity", "engines"),
        text("version", "Version", "Identity", { code: true }),
        text("license", "License", "Identity"),
        text("repo", "Repo", "Identity", { code: true }),
        text("os", "OS", "Support"),
        text("formats", "Formats", "Support"),
        text("raw", "Single", "Decoding", { info: "Decodes with speculation off: the Single rows." }),
        text("speculation", "Speculation", "Decoding", { info: "Drafts and verifies tokens: the Speculative rows." }),
        number("_results", "Results", "Coverage", "", 0),
      ],
    },

    models: {
      label: "Models",
      section: "catalog",
      numbered: true,
      filters: [],
      columns: [
        text("name", "Name", "Identity"),
        text("platforms", "Platforms", "Identity", { hint: "The platforms this model is measured on" }),
        text("family", "Family", "Identity", { code: true }),
        text("architecture", "Architecture", "Shape"),
        text("ssd_streaming", "SSD streaming", "Shape"),
        text("speculation", "Speculation", "Shape", { hint: "Whether the model has a drafter, so it runs with speculative decoding" }),
        number("params_b", "Params", "Shape", "B", 1),
        number("active_b", "Active", "Shape", "B", 1),
        number("layers", "Layers", "Shape", "", 0, { hint: "Transformer layers, from the model's config.json" }),
        number("hidden_size", "Hidden", "Shape", "", 0, { hint: "Hidden size, from the model's config.json" }),
        number("experts", "Experts", "Shape", "", 0, { hint: "Routed experts a MoE layer holds" }),
        number("top_k", "Top-k", "Shape", "", 0, { hint: "Routed experts each token runs through" }),
        number("context", "Context", "Shape", "tok", 0, { hint: "Longest context the model's config.json allows" }),
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
      numbered: true,
      filters: [],
      columns: [
        reference("id", "Workload", "Identity", "workloads"),
        text("goal", "Goal", "Identity"),
        text("parallel", "Parallel requests", "Shape", { numeric: true, swept: true, info: "A batched workload sweeps its requests: each machine runs the count at which the fastest engine stops gaining more than 5%, the same count for every engine." }),
        number("prompt_tokens", "Prompt", "Shape", "tok", 0),
        number("output_tokens", "Output", "Shape", "tok", 0),
        text("benchmark", "Benchmark", "Identity", { code: true }),
        number("_results", "Results", "Coverage", "", 0),
      ],
    },

    quality_tasks: {
      label: "Benchmarks",
      section: "catalog",
      numbered: true,
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
