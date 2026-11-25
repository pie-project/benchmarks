window.Pie = window.Pie || {};

(() => {
  const element = document.getElementById("welcome");

  const STACK = { mac: "Metal", windows: "CUDA", nvidia: "CUDA", tpu: "XLA", amd: "ROCm", cerebras: "CSL", android: "Vulkan", web: "WebGPU" };
  const platforms = () => Object.entries(Pie.schema).filter(([, s]) => s.view === "platform" && s.platform).sort(([, a], [, b]) => Pie.byPlatformOrder(a, b));

  let sortKey = null;
  let sortDir = 1;
  const table = () => {
    const list = platforms().map(([id, s]) => ({ id, s, name: s.short, stack: STACK[id] || "", machines: Pie.platform?.machines ? Pie.platform.machines(s.platform) : 0 }));
    if (sortKey) list.sort((a, b) => sortDir * (typeof a[sortKey] === "number" ? a[sortKey] - b[sortKey] : String(a[sortKey]).localeCompare(String(b[sortKey]))));
    const arrow = (key) => (sortKey === key ? `<span class="column-sort">${sortDir > 0 ? "↑" : "↓"}</span>` : "");
    const rows = list.map(({ id, s, machines: n }, i) => `<tr class="is-link" data-go="${id}">
        <td class="row-number">${i + 1}</td>
        <td><span class="welcome-cell" title="${s.label}"><span class="sidebar-glyph" style="--tint: ${s.tint}">${Pie.icon(id)}</span>${s.short}</span></td>
        <td class="welcome-stack">${STACK[id] || ""}</td>
        <td class="welcome-fill"></td>
        <td class="welcome-count is-numeric">${n}</td>
      </tr>`).join("");
    return `<table class="data-table welcome-table">
      <thead><tr><th class="row-number" aria-label="Row"></th><th data-sort="name">Platform${arrow("name")}</th><th data-sort="stack">Stack${arrow("stack")}</th><th class="welcome-fill"></th><th class="is-numeric" data-sort="machines">Machines${arrow("machines")}</th></tr></thead>
      <tbody>${rows}</tbody>
    </table>`;
  };

  let open = null;
  Pie.welcome = {
    element,
    onOpen(handler) {
      open = handler;
    },
    render(state) {
      element.hidden = state.table !== "welcome";
      if (!element.hidden && element.dataset.ready !== "1") {
        element.innerHTML = `<div class="filter-bar" aria-hidden="true"></div>${table()}`;
        element.addEventListener("click", (event) => {
          const head = event.target.closest("th[data-sort]");
          if (head) {
            const key = head.dataset.sort;
            if (sortKey !== key) { sortKey = key; sortDir = 1; }
            else if (sortDir > 0) sortDir = -1;
            else sortKey = null;
            element.querySelector(".welcome-table").outerHTML = table();
            return;
          }
          const row = event.target.closest("[data-go]");
          if (row) open?.(Pie.schema[row.dataset.go].short);
        });
        element.dataset.ready = "1";
      }
    },
  };
})();
