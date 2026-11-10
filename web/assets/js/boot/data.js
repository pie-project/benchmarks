window.Pie = window.Pie || {};

// Where the benchmark data lives: db.js (loaded here, before the app's scripts), tags/<tag>.json and trackers.json,
// published by pie-project/benchmarks' CI (tools/webdb.py, pages.yml). A page served from localhost reads a data/
// folder beside it instead, so a preview, or CI's outlier check, shows the data it was given.
(() => {
  const DATA = "data/";  // benchmarks.pie-project.org serves the data beside the app (pages.yml)
  const local = ["localhost", "127.0.0.1", "[::1]"].includes(location.hostname);
  Pie.dataBase = local ? "data/" : DATA;
  document.write(`<script src="${Pie.dataBase}db.js"><\/script>`);
})();
