window.Pie = window.Pie || {};

Pie.icons = {
  profiler: '<path d="M3 12h4l2.5-6 5 12 2.5-6h4"/>',
  inferlets: '<path d="M12 3 4 7.5v9L12 21l8-4.5v-9L12 3z"/><path d="m4 7.5 8 4.5 8-4.5M12 12v9"/>',
  services: '<rect x="3" y="7" width="18" height="13" rx="2.5"/><path d="M9 7V5.5A1.5 1.5 0 0 1 10.5 4h3A1.5 1.5 0 0 1 15 5.5V7M3 12.5h18M10.5 12.5v1.5h3v-1.5"/>',  // a briefcase: work done for a company
  welcome: '<rect x="4" y="4" width="6.5" height="6.5" rx="1.5"/><rect x="13.5" y="4" width="6.5" height="6.5" rx="1.5"/><rect x="4" y="13.5" width="6.5" height="6.5" rx="1.5"/><rect x="13.5" y="13.5" width="6.5" height="6.5" rx="1.5"/>',  // square.grid.2x2: every platform at once
  board: '<rect class="is-filled" x="3" y="11.5" width="5.6" height="9.5" rx="1.2"/><rect class="is-filled" x="9.2" y="3" width="5.6" height="18" rx="1.2"/><rect class="is-filled" x="15.4" y="7.5" width="5.6" height="13.5" rx="1.2"/>',  // three solid bars, as Artificial Analysis draws its mark in blocks
  speedups: '<path class="is-filled" d="M2.59 4.68Q2 4 2.90 4.00L7.10 4.00Q8 4 8.59 4.68L14.41 11.32Q15 12 14.41 12.68L8.59 19.32Q8 20 7.10 20.00L2.90 20.00Q2 20 2.59 19.32L8.41 12.68Q9 12 8.41 11.32ZM10.09 4.68Q9.5 4 10.40 4.00L14.60 4.00Q15.5 4 16.09 4.68L21.91 11.32Q22.5 12 21.91 12.68L16.09 19.32Q15.5 20 14.60 20.00L10.40 20.00Q9.5 20 10.09 19.32L15.91 12.68Q16.5 12 15.91 11.32Z"/>',  // two solid chevrons, their corners softened a little: faster than the other engine
  tps: '<path class="is-filled" fill-rule="evenodd" d="M4.5 2.5h15A2 2 0 0 1 21.5 4.5v5a2 2 0 0 1-2 2h-15a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2zm2 3v2.75H10V5.5zM4.5 12.5h15a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-15a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2zm2 3v2.75H10V15.5z"/>',  // two solid server units, a light cut out of each
  all_hardware: '<path d="M17 3.8c-2.6-.8-4.5.2-5 2.9L9.6 17.4c-.6 2.7-2.4 3.6-5 2.9M7.5 10h9" stroke-width="4.2" stroke-linecap="square"/>',  // a bold function sign: the kernel each forward pass runs, against the hardware's limit
  tpu: '<path class="is-filled" d="M6.8 19.5h10.7a4.6 4.6 0 0 0 .8-9.15 6.2 6.2 0 0 0-11.9-1.2A5.2 5.2 0 0 0 6.8 19.5z"/>',  // a solid cloud: Google's TPUs, rented in its cloud
  nvidia: '<path class="is-filled" fill-rule="evenodd" d="M7 5h10a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2zM9.75 9.75v4.5h4.5v-4.5z"/><path class="is-filled" d="M8.25 1.5h2.25v3h-2.25zM13.5 1.5h2.25v3H13.5zM8.25 19.5h2.25v3h-2.25zM13.5 19.5h2.25v3H13.5zM1.5 8.25h3v2.25h-3zM1.5 13.5h3v2.25h-3zM19.5 8.25h3v2.25h-3zM19.5 13.5h3v2.25h-3z"/>',  // a solid chip, its die cut out, in the bold blocks of the page icons
  amd: '<path class="is-filled" fill-rule="evenodd" d="M7 5h10a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2zM8.5 8.5v7h7v-7zM10.5 10.5h3v3h-3z"/><path class="is-filled" d="M8.25 1.5h2.25v3h-2.25zM13.5 1.5h2.25v3H13.5zM8.25 19.5h2.25v3h-2.25zM13.5 19.5h2.25v3H13.5zM1.5 8.25h3v2.25h-3zM1.5 13.5h3v2.25h-3zM19.5 8.25h3v2.25h-3zM19.5 13.5h3v2.25h-3z"/>',  // a solid chip with a ring cut round its core: told apart from NVIDIA's
  cerebras: '<path class="is-filled" fill-rule="evenodd" d="M5.5 2.5h13a3 3 0 0 1 3 3v13a3 3 0 0 1-3 3h-13a3 3 0 0 1-3-3v-13a3 3 0 0 1 3-3zM6.25 6.25v4.75H11V6.25zm6.75 0v4.75h4.75V6.25zM6.25 13v4.75H11V13zm6.75 0v4.75h4.75V13z"/>',  // a solid wafer, its four dies cut out
  android: '<rect x="7" y="3" width="10" height="18" rx="2.4"/><path d="M11 18h2"/>',
  web: '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c2.5 2.6 3.8 5.6 3.8 9s-1.3 6.4-3.8 9c-2.5-2.6-3.8-5.6-3.8-9s1.3-6.4 3.8-9z"/>',
  mac: '<path class="is-filled" d="M12.152 6.896c-.948 0-2.415-1.078-3.96-1.04-2.04.027-3.91 1.183-4.961 3.014-2.117 3.675-.546 9.103 1.519 12.09 1.013 1.454 2.208 3.09 3.792 3.039 1.52-.065 2.09-.987 3.935-.987 1.831 0 2.35.987 3.96.948 1.637-.026 2.676-1.48 3.676-2.948 1.156-1.688 1.636-3.325 1.662-3.415-.039-.013-3.182-1.221-3.22-4.857-.026-3.04 2.48-4.494 2.597-4.559-1.429-2.09-3.623-2.324-4.39-2.376-2-.156-3.675 1.09-4.61 1.09zM15.53 3.83c.843-1.012 1.4-2.427 1.245-3.83-1.207.052-2.662.805-3.532 1.818-.78.896-1.454 2.338-1.273 3.714 1.338.104 2.715-.688 3.559-1.701"/>',
  overview: '<path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/>',
  results: '<path d="M4 5h16M4 12h16M4 19h16"/>',
  quality: '<path d="m5 12 4 4 10-10"/>',
  scores: '<path style="fill: #fff; stroke: none" transform="translate(3 3) scale(1.125)" d="M13.982 16h1.996v-3.997h-3.992V16zM7.984 0 3.992 3.997H0v3.998h5.988L9.98 3.997h2.006V0zM7.984 7.995l-3.992 4.008H0V16h5.988l3.992-3.997h2.006V7.995zM15.978 7.995V3.997h-3.992v3.998h3.992"/>',  // Artificial Analysis's mark, white on a tile in their purple: Quality opens their site
  methodology: '<path d="M3.5 17a8.5 8.5 0 1 1 17 0"/><path d="m12 17 4.2-5.2"/><path d="M6.5 13.2l1.2.7M12 8.5v1.4M17.5 13.2l-1.2.7"/>',  // a gauge: the hardware limit
  methods: '<path d="M4 4v16h16"/><path d="M7 16l5-7h8"/>',  // a roofline: the bandwidth slope meeting the flat compute roof
  fit: '<rect x="3.5" y="5" width="17" height="14" rx="2.5"/><rect x="7.5" y="9" width="9" height="6" rx="1"/>',  // rectangle.inset: a model inside the machine's memory
  hardware: '<rect x="5" y="5" width="14" height="14" rx="2"/><path d="M9 2v3M15 2v3M9 19v3M15 19v3M2 9h3M2 15h3M19 9h3M19 15h3"/>',
  engines: '<circle cx="12" cy="12" r="3"/><path d="M12 2v4M12 18v4M2 12h4M18 12h4M5 5l3 3M16 16l3 3M5 19l3-3M16 8l3-3"/>',
  models: '<path d="M12 3 3 8l9 5 9-5-9-5z"/><path d="m3 16 9 5 9-5"/>',
  workloads: '<path d="M3 12h4l3-8 4 16 3-8h4"/>',
  quality_tasks: '<path d="M9 4h6l1 3H8l1-3z"/><rect x="5" y="7" width="14" height="14" rx="2"/><path d="m9 14 2 2 4-4"/>',
};

Pie.icon = (name) => `<svg viewBox="0 0 24 24" aria-hidden="true">${Pie.icons[name] || ""}</svg>`;
