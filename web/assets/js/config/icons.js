window.Pie = window.Pie || {};

Pie.icons = {
  profiler: '<path d="M3 12h4l2.5-6 5 12 2.5-6h4"/>',
  inferlets: '<path d="M12 3 4 7.5v9L12 21l8-4.5v-9L12 3z"/><path d="m4 7.5 8 4.5 8-4.5M12 12v9"/>',
  services: '<rect x="3" y="7" width="18" height="13" rx="2.5"/><path d="M9 7V5.5A1.5 1.5 0 0 1 10.5 4h3A1.5 1.5 0 0 1 15 5.5V7M3 12.5h18M10.5 12.5v1.5h3v-1.5"/>',  // a briefcase: work done for a company
  welcome: '<rect x="4" y="4" width="6.5" height="6.5" rx="1.5"/><rect x="13.5" y="4" width="6.5" height="6.5" rx="1.5"/><rect x="4" y="13.5" width="6.5" height="6.5" rx="1.5"/><rect x="13.5" y="13.5" width="6.5" height="6.5" rx="1.5"/>',  // square.grid.2x2: every platform at once
  board: '<path d="M4 20v-6h5v6M9 20V9h6v11M15 20v-8h5v8M3 20h18"/>',  // a podium: the engines ranked
  speedups: '<path d="M3 17l6-6 4 4 8-8"/><path d="M15 7h6v6"/>',  // chart.line.uptrend: faster than the others
  all_hardware: '<path d="M6 19v-5M12 19V9M18 19V5"/>',  // chart.bar: each result against the hardware's limit; plain lines, as the Speedup arrow
  tpu: '<path d="M7 18h10a4 4 0 0 0 .6-7.95A5.5 5.5 0 0 0 7.1 9.1 4.5 4.5 0 0 0 7 18z"/>',
  nvidia: '<rect x="6" y="6" width="12" height="12" rx="2"/><path d="M9 3v3M15 3v3M9 18v3M15 18v3M3 9h3M3 15h3M18 9h3M18 15h3"/>',
  amd: '<rect x="6" y="6" width="12" height="12" rx="2"/><path d="M10 10h4v4h-4zM9 3v3M15 3v3M9 18v3M15 18v3M3 9h3M3 15h3M18 9h3M18 15h3"/>',
  cerebras: '<rect x="4" y="4" width="16" height="16" rx="2.5"/><path d="M8 8h8v8H8z"/><path d="M12 4v4M12 16v4M4 12h4M16 12h4"/>',
  android: '<rect x="7" y="3" width="10" height="18" rx="2.4"/><path d="M11 18h2"/>',
  web: '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c2.5 2.6 3.8 5.6 3.8 9s-1.3 6.4-3.8 9c-2.5-2.6-3.8-5.6-3.8-9s1.3-6.4 3.8-9z"/>',
  mac: '<path class="is-filled" d="M12.152 6.896c-.948 0-2.415-1.078-3.96-1.04-2.04.027-3.91 1.183-4.961 3.014-2.117 3.675-.546 9.103 1.519 12.09 1.013 1.454 2.208 3.09 3.792 3.039 1.52-.065 2.09-.987 3.935-.987 1.831 0 2.35.987 3.96.948 1.637-.026 2.676-1.48 3.676-2.948 1.156-1.688 1.636-3.325 1.662-3.415-.039-.013-3.182-1.221-3.22-4.857-.026-3.04 2.48-4.494 2.597-4.559-1.429-2.09-3.623-2.324-4.39-2.376-2-.156-3.675 1.09-4.61 1.09zM15.53 3.83c.843-1.012 1.4-2.427 1.245-3.83-1.207.052-2.662.805-3.532 1.818-.78.896-1.454 2.338-1.273 3.714 1.338.104 2.715-.688 3.559-1.701"/>',
  overview: '<path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/>',
  results: '<path d="M4 5h16M4 12h16M4 19h16"/>',
  quality: '<path d="m5 12 4 4 10-10"/>',
  methodology: '<path d="M3.5 17a8.5 8.5 0 1 1 17 0"/><path d="m12 17 4.2-5.2"/><path d="M6.5 13.2l1.2.7M12 8.5v1.4M17.5 13.2l-1.2.7"/>',  // a gauge: the hardware limit
  methods: '<path d="M4 4v16h16"/><path d="M7 16l5-7h8"/>',  // a roofline: the bandwidth slope meeting the flat compute roof
  hardware: '<rect x="5" y="5" width="14" height="14" rx="2"/><path d="M9 2v3M15 2v3M9 19v3M15 19v3M2 9h3M2 15h3M19 9h3M19 15h3"/>',
  engines: '<circle cx="12" cy="12" r="3"/><path d="M12 2v4M12 18v4M2 12h4M18 12h4M5 5l3 3M16 16l3 3M5 19l3-3M16 8l3-3"/>',
  models: '<path d="M12 3 3 8l9 5 9-5-9-5z"/><path d="m3 16 9 5 9-5"/>',
  workloads: '<path d="M3 12h4l3-8 4 16 3-8h4"/>',
  quality_tasks: '<path d="M9 4h6l1 3H8l1-3z"/><rect x="5" y="7" width="14" height="14" rx="2"/><path d="m9 14 2 2 4-4"/>',
};

Pie.icon = (name) => `<svg viewBox="0 0 24 24" aria-hidden="true">${Pie.icons[name] || ""}</svg>`;
