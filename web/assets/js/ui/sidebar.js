window.Pie = window.Pie || {};

(() => {
  const nav = document.getElementById("sidebar-nav");
  const logo = document.querySelector(".sidebar-logo");
  const aside = document.getElementById("sidebar");
  const backdrop = document.getElementById("sidebar-backdrop");

  // results count the selected release's enumerated setups, measured or not
  const count = (id, state) => (id === "results" ? Pie.store.count(state.release).rows : (Pie.store.rows(id) || []).length);
  // a platform counts its machines; an empty one shows none
  const machines = (schema) => (Pie.platform?.machines ? Pie.platform.machines(schema.platform) : 0);

  const item = (id, schema, selected, state) => schema.href ? `
    <a class="sidebar-item is-link" href="${schema.href}" target="_blank" rel="noopener">
      <span class="sidebar-glyph"${schema.tint ? ` style="--tint: ${schema.tint}"` : ""}>${Pie.icon(id)}</span>
      <span>${schema.label}</span>
      <svg class="sidebar-out" viewBox="0 0 16 16" aria-hidden="true"><path d="M5 11 11 5M6 5h5v5"/></svg>
    </a>` : `
    <button class="sidebar-item${selected ? " is-selected" : ""}${schema.platform ? " is-platform" : ""}" type="button" data-table="${id}" aria-current="${selected}">
      <span class="sidebar-glyph"${schema.tint ? ` style="--tint: ${schema.tint}"` : ""}>${Pie.icon(id)}</span>
      <span>${schema.label}</span>
      ${schema.tag ? `<span class="sidebar-tag" title="Under development">${schema.tag}</span>` : ""}
      ${schema.view === "platform" && !schema.platform ? ""  // Speedup and Efficiency: views, not lists, so no count
        : schema.view === "platform"
        // a platform counts the machines measured on it; none yet reads 0
        ? `<span class="sidebar-count"${machines(schema) ? "" : ' title="No measurements yet"'}>${machines(schema)}</span>`
        // the Platforms list counts its rows, one a platform
        : schema.view === "welcome" ? `<span class="sidebar-count">${Object.values(Pie.schema).filter((s) => s.view === "platform" && s.platform).length}</span>`
        // Methodology counts its chapters
        : schema.view === "approach" ? `<span class="sidebar-count">${Pie.approach?.chapters ?? ""}</span>`
        : schema.view ? "" : `<span class="sidebar-count">${count(id, state)}</span>`}
    </button>`;

  const section = (section, state) => {
    const current = state.table;
    const items = Object.entries(Pie.schema)
      .filter(([, schema]) => schema.section === section.id)
      .map(([id, schema]) => item(id, schema, id === current, state))
      .join("");
    return `${section.label ? `<div class="sidebar-heading">${section.label}</div>` : ""}${items}`;
  };

  Pie.sidebar = {
    render(state) {
      nav.innerHTML = Pie.sections.filter((entry) => !entry.login || Pie.signedIn()).map((entry) => section(entry, state)).join("");
    },

    spinLogo() {
      logo.classList.remove("is-spinning");
      void logo.getBoundingClientRect();
      logo.classList.add("is-spinning");
    },

    bindLogo() {
      logo.addEventListener("animationend", () => logo.classList.remove("is-spinning"));
      // the whole brand row spins it: the logo, the name and the (i) beside them
      logo.closest(".sidebar-brand").addEventListener("mouseenter", () => {
        if (!logo.classList.contains("is-spinning")) logo.classList.add("is-spinning");
      });
      this.spinLogo();
    },

    // the slide-over closes on its backdrop, and follows a finger swiping it back to the left
    bindDrawer(close) {
      backdrop.addEventListener("click", close);
      let start = null;
      let shift = 0;
      aside.addEventListener("touchstart", (event) => {
        start = event.touches.length === 1 ? { x: event.touches[0].clientX, y: event.touches[0].clientY, sideways: null } : null;
        shift = 0;
      }, { passive: true });
      aside.addEventListener("touchmove", (event) => {
        if (!start) return;
        const dx = event.touches[0].clientX - start.x;
        const dy = event.touches[0].clientY - start.y;
        if (start.sideways === null && Math.abs(dx) + Math.abs(dy) > 8) start.sideways = Math.abs(dx) > Math.abs(dy);
        if (!start.sideways) return;
        shift = Math.min(0, dx);
        aside.style.transition = "none";
        aside.style.transform = `translateX(${shift}px)`;
      }, { passive: true });
      const settle = () => {
        if (!start) return;
        aside.style.transition = "";
        aside.style.transform = "";
        if (start.sideways && shift < -Math.min(80, aside.offsetWidth / 3)) close();
        start = null;
      };
      aside.addEventListener("touchend", settle);
      aside.addEventListener("touchcancel", settle);
    },

    onSelect(handler) {
      nav.addEventListener("click", (event) => {
        const target = event.target.closest("[data-table]");
        if (target) handler(target.dataset.table);
      });
    },
  };
})();
