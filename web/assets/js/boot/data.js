window.Pie = window.Pie || {};

(() => {
  const API = "https://bench-api.pie-project.org/v1/";
  const local = ["localhost", "127.0.0.1", "[::1]"].includes(location.hostname);
  Pie.dataBase = new URLSearchParams(location.search).get("api") || (local ? "http://localhost:8790/v1/" : API);
  Pie.getJson = (path) => fetch(Pie.dataBase + path).then((r) => (r.ok ? r.json() : Promise.reject(new Error(`${path}: ${r.status}`))));

  const APP = [
    "config/icons", "config/engines", "config/schema", "config/architectures",
    "core/state", "core/format", "core/store", "core/query",
    "ui/preferences", "ui/sidebar", "ui/toolbar", "ui/palette", "ui/report", "ui/popover", "ui/tap-card", "ui/segmented",
    "ui/filters", "ui/dates", "ui/table", "ui/overview", "ui/platform", "ui/welcome", "ui/inferlets", "ui/services",
    "ui/approach", "ui/reports", "config/gapnotes", "config/profiles", "ui/gaps", "ui/reasons", "ui/profiler", "ui/fairness", "ui/methodology",
    "ui/methods", "ui/board", "ui/tour", "ui/checks", "app",
  ];

  const read = async () => {
    for (let tries = 0; ; tries++) {
      try {
        return await Promise.all([Pie.getJson("catalog"), Pie.getJson("results")]);
      } catch (error) {
        if (tries >= 20) throw error;
        await new Promise((done) => setTimeout(done, 3000));
      }
    }
  };

  read().then(([catalog, latest]) => {
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
