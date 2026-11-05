window.Pie = window.Pie || {};

// The page's outline while its data loads, as a Mac app shows a redacted view: grey rounded bars where the words and
// numbers go, laid out as the page about to open lays them out. Drawn before data/db.js is read, for the page a
// reload or a link opens; app.js shows it again while a tag's own file loads (core/store.js), then fades the page in.
(() => {
  const element = document.getElementById("skeleton");
  const GRIDS = ["speedups", "tps", "all_hardware", "mac", "nvidia", "amd", "tpu", "cerebras", "android", "web", "checks"];
  const TEXTS = ["methods", "fit", "methodology", "inferlets", "services", "profiler", "accuracy"];
  // the page a reload opens, read as app.js reads it: the address first, then the view kept in the browser
  const opening = () => {
    const [view] = decodeURIComponent(location.hash.slice(1)).split("/");
    if (view === "board") return "board";
    if (view === "quality") return "checks";
    if (view === "overview" || view === "mac") return "mac";
    try { return JSON.parse(localStorage.getItem("pieView") || "null")?.table || "board"; } catch { return "board"; }
  };
  // widths that vary from bar to bar, the same on every draw, so the outline does not flicker as it is drawn again
  const width = (i, lo, hi) => lo + ((i * 37) % 11) / 10 * (hi - lo);
  const bar = (w, cls = "") => `<span class="skeleton-bar${cls ? ` ${cls}` : ""}" style="width: ${typeof w === "number" ? `${Math.round(w)}px` : w}"></span>`;
  const range = (n) => [...Array(n).keys()];

  // the four platforms the page lists (Apple Silicon, NVIDIA, AMD, TPU), each with about its own number of machines
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

  // the sidebar's rows and the toolbar's title, until app.js names them
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
    // the outline of a page, in place of the page; the pages and their bars stay hidden under it
    show(page) {
      if (!element) return;
      // no outline is drawn: the page stays empty until its data arrives
      shown = page;
      for (const id of ["table-container", "overview", "platform", "welcome", "inferlets", "services", "profiler", "methodology", "methods", "board", "checks"]) {
        const other = document.getElementById(id);
        if (other) other.hidden = true;
      }
      document.querySelector(".filter-bar")?.setAttribute("hidden", "");
    },
    // the page drawn in its place fades in (a platform's numbers roll in instead, platform.js)
    hide() {
      if (!element || shown === null) return false;
      shown = null;
      return true;
    },
  };

  Pie.skeleton.show(opening());
})();
