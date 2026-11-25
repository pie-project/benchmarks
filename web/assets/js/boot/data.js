window.Pie = window.Pie || {};

(() => {
  const API = "https://bench-api.pie-project.org/v1/";
  const local = ["localhost", "127.0.0.1", "[::1]"].includes(location.hostname);
  Pie.dataBase = new URLSearchParams(location.search).get("api") || (local ? `${location.origin}/v1/` : API);
  Pie.getJson = (path) => fetch(Pie.dataBase + path).then((r) => (r.ok ? r.json() : Promise.reject(new Error(`${path}: ${r.status}`))));

  const APP = [
    "config/icons", "config/engines", "config/schema", "config/architectures",
    "core/state", "core/format", "core/store", "core/query",
    "ui/preferences", "ui/sidebar", "ui/toolbar", "ui/palette", "ui/report", "ui/popover", "ui/tap-card", "ui/segmented",
    "ui/filters", "ui/dates", "ui/table", "ui/overview", "ui/platform", "ui/welcome", "ui/inferlets", "ui/services",
    "ui/approach", "ui/reports", "config/gapnotes", "ui/gaps", "ui/reasons", "ui/profiler", "ui/fairness", "ui/methodology",
    "ui/methods", "ui/board", "ui/tour", "ui/checks", "app",
  ];

  const CATALOG = {
    machines: "hardware", models: "models", engines: "engines", workloads: "workloads", releases: "releases",
    suites: "suites", install: "install", totals: "totals", miniatures: "miniatures", parity: "parity",
    "no-fit": "no_fit", "speed-gaps": "speed_gaps", quality: "quality", "quality-tasks": "quality_tasks",
    "quality-parity": "quality_parity", "quality-kernels": "quality_kernels", "quality-gaps": "quality_gaps",
  };

  const readCatalog = async () => {
    const names = Object.keys(CATALOG);
    const parts = await Promise.all(names.map((name) => Pie.getJson(name)));
    if (new Set(parts.map((part) => part.updated_at)).size > 1) throw new Error("catalog parts from different builds");
    const catalog = { updated_at: parts[0].updated_at };
    names.forEach((name, i) => { catalog[CATALOG[name]] = parts[i][name]; });
    return catalog;
  };

  const read = async () => {
    for (let tries = 0; ; tries++) {
      try {
        return await Promise.all([readCatalog(), Pie.getJson("results"), Pie.getJson("profiles").catch(() => ({}))]);
      } catch (error) {
        if (tries >= 20) throw error;
        await new Promise((done) => setTimeout(done, 3000));
      }
    }
  };

  read().then(([catalog, latest, profiles]) => {
    Pie.profiles = profiles;
    // verified: a profile of both engines agrees with the benchmark, by the API's own checks
    Pie.verifiedProfile = (key) => profiles[key]?.verdict === "confirmed";
    window.DB = {
      ...catalog,
      tags: catalog.releases,
      snapshots: { [latest.id]: latest.results },
      quality_snapshots: { [latest.id]: latest.quality },
    };
    for (const name of APP) {
      const script = document.createElement("script");
      script.src = `assets/js/${name}.js`;
      script.async = false;
      document.body.append(script);
    }
  });
})();
