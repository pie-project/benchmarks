window.Pie = window.Pie || {};

(() => {
  const element = document.getElementById("skeleton");
  const GRIDS = ["speedups", "tps", "all_hardware", "mac", "nvidia", "amd", "tpu", "cerebras", "android", "web", "checks"];
  const TEXTS = ["methods", "fit", "methodology", "approach", "reports", "accuracy"];
  const opening = () => {
    let address = "";
    try { address = decodeURIComponent(location.hash.slice(1)); } catch { address = ""; }
    const [view] = address.split("/");
    if (view === "board") return "board";
    if (view === "quality") return "checks";
    if (view === "overview" || view === "mac") return "mac";
    try { return JSON.parse(localStorage.getItem("pieView") || "null")?.table || "board"; } catch { return "board"; }
  };
  const width = (i, lo, hi) => lo + ((i * 37) % 11) / 10 * (hi - lo);
  const bar = (w, cls = "") => `<span class="skeleton-bar${cls ? ` ${cls}` : ""}" style="width: ${typeof w === "number" ? `${Math.round(w)}px` : w}"></span>`;
  const range = (n) => [...Array(n).keys()];

  const ROWS = [5, 10, 2, 3];
  const grid = () => range(4).map((s) => `
    <div class="skeleton-section">
      <div class="skeleton-head"><span class="skeleton-icon"></span>${bar(96)}${bar(110, "is-faint")}</div>
      <div class="skeleton-grid">
        <div class="skeleton-row is-header"><span>${bar(56, "is-faint")}</span>${range(6).map((c) => `<span class="is-center">${bar(width(c + s, 70, 110))}${bar(36, "is-faint")}</span>`).join("")}</div>
        ${range(ROWS[s]).map((r) => `<div class="skeleton-row"><span><span class="skeleton-icon"></span>${bar(width(r, 40, 80))}</span>${range(6).map((c) => `<span class="is-end">${bar(width(r + c, 28, 44))}</span>`).join("")}</div>`).join("")}
      </div>
    </div>`).join("");

  const board = () => `
    <div class="skeleton-board">
      <div class="skeleton-rail">${bar(70, "is-faint")}${range(4).map((i) => bar(width(i, 60, 100))).join("")}${bar(70, "is-faint")}${range(2).map((i) => bar(width(i + 4, 80, 120))).join("")}</div>
      <div class="skeleton-main">
        ${bar(160, "is-title")}${bar(340, "is-faint")}
        <div class="skeleton-cards">${range(4).map((k) => `
          <div class="skeleton-card">${bar(70)}${bar(230, "is-faint")}
            <div class="skeleton-columns">${range(k ? 3 : 4).map((i) => `<span class="skeleton-column" style="height: ${[100, 70, 60, 45][i] - k * 6}%"></span>`).join("")}</div>
          </div>`).join("")}
        </div>
      </div>
    </div>`;

  const table = (rows) => `
    <div class="skeleton-filters">${range(4).map((i) => bar(width(i, 70, 110), "is-chip")).join("")}</div>
    <div class="skeleton-table">
      <div class="skeleton-row is-header">${range(7).map((c) => `<span>${bar(width(c, 40, 80), "is-faint")}</span>`).join("")}</div>
      ${range(rows).map((r) => `<div class="skeleton-row">${range(7).map((c) => `<span${c > 3 ? ` class="is-end"` : ""}>${bar(width(r * 7 + c, c > 3 ? 30 : 50, c > 3 ? 50 : 120))}</span>`).join("")}</div>`).join("")}
    </div>`;

  const text = () => `
    <div class="skeleton-text">${bar(220, "is-title")}${range(3).map((p) => `<p>${range(4).map((l) => bar(l === 3 ? `${width(p + l, 30, 60)}%` : "100%")).join("")}</p>`).join("")}</div>`;

  const draw = (page) => (page === "board" ? board() : GRIDS.includes(page) ? grid() : TEXTS.includes(page) ? text() : table(page === "welcome" ? 7 : 18));

  const chrome = () => {
    const nav = document.getElementById("sidebar-nav");
    if (nav && !nav.children.length) {
      nav.innerHTML = `<div class="skeleton-nav">${[1, 2, 4, 2, 6].map((n, s) => `${s ? bar(width(s, 44, 70), "is-faint is-heading") : ""}${range(n).map((i) => `<div class="skeleton-item"><span class="skeleton-icon"></span>${bar(width(s * 3 + i, 50, 96))}</div>`).join("")}`).join("")}</div>`;
    }
    const title = document.getElementById("toolbar-title");
    if (title && !title.textContent) title.innerHTML = bar(96, "is-title");
  };

  let shown = null;
  Pie.skeleton = {
    show(page) {
      if (!element) return;
      shown = page;
      for (const id of ["table-container", "overview", "platform", "welcome", "approach", "reports", "methodology", "methods", "board", "checks"]) {
        const other = document.getElementById(id);
        if (other) other.hidden = true;
      }
      document.querySelector(".filter-bar")?.setAttribute("hidden", "");
    },
    hide() {
      if (!element || shown === null) return false;
      shown = null;
      return true;
    },
  };

  Pie.skeleton.show(opening());
})();
