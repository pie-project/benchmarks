window.Pie = window.Pie || {};

Pie.icons = {
  profiler: '<path d="M3 12h4l2.5-6 5 12 2.5-6h4"/>',
  inferlets: '<path d="M12 3 4 7.5v9L12 21l8-4.5v-9L12 3z"/><path d="m4 7.5 8 4.5 8-4.5M12 12v9"/>',
  services: '<rect x="3" y="7" width="18" height="13" rx="2.5"/><path d="M9 7V5.5A1.5 1.5 0 0 1 10.5 4h3A1.5 1.5 0 0 1 15 5.5V7M3 12.5h18M10.5 12.5v1.5h3v-1.5"/>',  // a briefcase: work done for a company
  welcome: '<rect x="4" y="4" width="6.5" height="6.5" rx="1.5"/><rect x="13.5" y="4" width="6.5" height="6.5" rx="1.5"/><rect x="4" y="13.5" width="6.5" height="6.5" rx="1.5"/><rect x="13.5" y="13.5" width="6.5" height="6.5" rx="1.5"/>',  // square.grid.2x2: every platform at once
  board: '<path d="M4 10.5 12 4l8 6.5V19a1 1 0 0 1-1 1h-4.5v-5.5h-5V20H5a1 1 0 0 1-1-1z"/>',  // house: the Overview, the site's home
  bars: '<path d="M6 20v-9M12 20V4.5M18 20v-6"/>',  // chart.bar: a measured release, in the changelog
  speedups: '<path d="M9.93,5.31L10.17,2.98L13.83,2.98L14.07,5.31L15.27,5.81L17.08,4.33L19.67,6.92L18.19,8.73L18.69,9.93L21.02,10.17L21.02,13.83L18.69,14.07L18.19,15.27L19.67,17.08L17.08,19.67L15.27,18.19L14.07,18.69L13.83,21.02L10.17,21.02L9.93,18.69L8.73,18.19L6.92,19.67L4.33,17.08L5.81,15.27L5.31,14.07L2.98,13.83L2.98,10.17L5.31,9.93L5.81,8.73L4.33,6.92L6.92,4.33L8.73,5.81Z" stroke-linejoin="round"/><circle cx="12" cy="12" r="3"/>',  // gearshape, as SF Symbols draws it: an engine against the others
  tps: '<rect x="3.5" y="3.5" width="17" height="6.5" rx="2"/><rect x="3.5" y="14" width="17" height="6.5" rx="2"/><path d="M7 6.75h.01M7 17.25h.01M11 6.75h5.5M11 17.25h5.5"/>',  // server.rack: the hardware a model runs fastest on
  all_hardware: '<path d="M16.5 4.2c-2.4-.7-4.1.2-4.6 2.7L9.6 17.6c-.5 2.5-2.2 3.4-4.6 2.7M8 10h8"/>',  // function, as SF Symbols draws it: the kernel each forward pass runs, against the hardware's limit
  tpu: '<path class="is-filled" transform="translate(2 2) scale(.833)" d="M12.48 10.92v3.28h7.84c-.24 1.84-.853 3.187-1.787 4.133-1.147 1.147-2.933 2.4-6.053 2.4-4.827 0-8.6-3.893-8.6-8.72s3.773-8.72 8.6-8.72c2.6 0 4.507 1.027 5.907 2.347l2.307-2.307C18.747 1.44 16.133 0 12.48 0 5.867 0 .307 5.387.307 12s5.56 12 12.173 12c3.573 0 6.267-1.173 8.373-3.36 2.16-2.16 2.84-5.213 2.84-7.667 0-.76-.053-1.467-.173-2.053H12.48z"/>',  // the maker's own mark (simple-icons, CC0), white on its tile
  nvidia: '<path class="is-filled" d="M8.948 8.798v-1.43a6.7 6.7 0 0 1 .424-.018c3.922-.124 6.493 3.374 6.493 3.374s-2.774 3.851-5.75 3.851c-.398 0-.787-.062-1.158-.185v-4.346c1.528.185 1.837.857 2.747 2.385l2.04-1.714s-1.492-1.952-4-1.952a6.016 6.016 0 0 0-.796.035m0-4.735v2.138l.424-.027c5.45-.185 9.01 4.47 9.01 4.47s-4.08 4.964-8.33 4.964c-.37 0-.733-.035-1.095-.097v1.325c.3.035.61.062.91.062 3.957 0 6.82-2.023 9.593-4.408.459.371 2.34 1.263 2.73 1.652-2.633 2.208-8.772 3.984-12.253 3.984-.335 0-.653-.018-.971-.053v1.864H24V4.063zm0 10.326v1.131c-3.657-.654-4.673-4.46-4.673-4.46s1.758-1.944 4.673-2.262v1.237H8.94c-1.528-.186-2.73 1.245-2.73 1.245s.68 2.412 2.739 3.11M2.456 10.9s2.164-3.197 6.5-3.533V6.201C4.153 6.59 0 10.653 0 10.653s2.35 6.802 8.948 7.42v-1.237c-4.84-.6-6.492-5.936-6.492-5.936z"/>',  // the maker's own mark (simple-icons, CC0), white on its tile
  amd: '<path class="is-filled" transform="scale(3.6) translate(-17.9 -8.8)" d="M18.324 9.137l1.559 1.56h2.556v2.557L24 14.814V9.137zM19.881 11.01l-1.604 1.603v2.25h2.246l1.604-1.607h-2.246z"/>',  // the maker's own mark (simple-icons, CC0), white on its tile
  cerebras: '<rect x="4" y="4" width="16" height="16" rx="2.5"/><path d="M8 8h8v8H8z"/><path d="M12 4v4M12 16v4M4 12h4M16 12h4"/>',
  android: '<rect x="7" y="3" width="10" height="18" rx="2.4"/><path d="M11 18h2"/>',
  web: '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c2.5 2.6 3.8 5.6 3.8 9s-1.3 6.4-3.8 9c-2.5-2.6-3.8-5.6-3.8-9s1.3-6.4 3.8-9z"/>',
  mac: '<path class="is-filled" d="M12.152 6.896c-.948 0-2.415-1.078-3.96-1.04-2.04.027-3.91 1.183-4.961 3.014-2.117 3.675-.546 9.103 1.519 12.09 1.013 1.454 2.208 3.09 3.792 3.039 1.52-.065 2.09-.987 3.935-.987 1.831 0 2.35.987 3.96.948 1.637-.026 2.676-1.48 3.676-2.948 1.156-1.688 1.636-3.325 1.662-3.415-.039-.013-3.182-1.221-3.22-4.857-.026-3.04 2.48-4.494 2.597-4.559-1.429-2.09-3.623-2.324-4.39-2.376-2-.156-3.675 1.09-4.61 1.09zM15.53 3.83c.843-1.012 1.4-2.427 1.245-3.83-1.207.052-2.662.805-3.532 1.818-.78.896-1.454 2.338-1.273 3.714 1.338.104 2.715-.688 3.559-1.701"/>',
  overview: '<path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/>',
  results: '<path d="M4 5h16M4 12h16M4 19h16"/>',
  quality: '<path d="m5 12 4 4 10-10"/>',
  accuracy: '<circle cx="12" cy="12" r="8.5"/><circle cx="12" cy="12" r="4.5"/><circle class="is-filled" cx="12" cy="12" r="1.5"/>',  // a target: how close the engines land to one another
  scores: '<path class="is-filled" transform="translate(3 3) scale(1.125)" d="M13.982 16h1.996v-3.997h-3.992V16zM7.984 0 3.992 3.997H0v3.998h5.988L9.98 3.997h2.006V0zM7.984 7.995l-3.992 4.008H0V16h5.988l3.992-3.997h2.006V7.995zM15.978 7.995V3.997h-3.992v3.998h3.992"/>',  // Artificial Analysis's mark, white on a tile in their purple: Quality opens their site
  methodology: '<path d="M3.5 17a8.5 8.5 0 1 1 17 0"/><path d="m12 17 4.2-5.2"/><path d="M6.5 13.2l1.2.7M12 8.5v1.4M17.5 13.2l-1.2.7"/>',  // a gauge: the hardware limit
  methods: '<path d="M4 4v16h16"/><path d="M7 16l5-7h8"/>',  // a roofline: the bandwidth slope meeting the flat compute roof
  fit: '<rect x="3.5" y="5" width="17" height="14" rx="2.5"/><rect x="7.5" y="9" width="9" height="6" rx="1"/>',  // rectangle.inset: a model inside the machine's memory
  hardware: '<rect x="5" y="5" width="14" height="14" rx="2"/><path d="M9 2v3M15 2v3M9 19v3M15 19v3M2 9h3M2 15h3M19 9h3M19 15h3"/>',
  engines: '<circle cx="12" cy="12" r="3"/><path d="M12 2v4M12 18v4M2 12h4M18 12h4M5 5l3 3M16 16l3 3M5 19l3-3M16 8l3-3"/>',
  models: '<path d="M12 3 3 8l9 5 9-5-9-5z"/><path d="m3 16 9 5 9-5"/>',
  workloads: '<path d="M3 12h4l3-8 4 16 3-8h4"/>',
  unsupported: '<circle cx="12" cy="12" r="8.5"/><path d="m6 18 12-12"/>',  // circle.slash: the reference engine cannot run this model
  checks: '<path d="M4 9.5c2.7-2 5.3-2 8 0s5.3 2 8 0M4 15.5c2.7-2 5.3-2 8 0s5.3 2 8 0"/>',  // almost equal: pie against its reference
  quality_tasks: '<path d="M9 4h6l1 3H8l1-3z"/><rect x="5" y="7" width="14" height="14" rx="2"/><path d="m9 14 2 2 4-4"/>',
};

Pie.icon = (name) => `<svg viewBox="0 0 24 24" aria-hidden="true">${Pie.icons[name] || ""}</svg>`;
