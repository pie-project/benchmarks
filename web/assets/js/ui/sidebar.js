window.Pie = window.Pie || {};

(() => {
  const nav = document.getElementById("sidebar-nav");
  const logo = document.querySelector(".sidebar-logo");

  // results count the selected release's enumerated setups, measured or not
  const count = (id, state) => (id === "results" ? Pie.store.snapshot(state.release).length : (Pie.store.rows(id) || []).length);
  // a platform counts its machines; an empty one shows none
  const machines = (schema) => (Pie.platform?.machines ? Pie.platform.machines(schema.platform) : 0);

  const item = (id, schema, selected, state) => `
    <button class="sidebar-item${selected ? " is-selected" : ""}" type="button" data-table="${id}" aria-current="${selected}">
      <span class="sidebar-glyph"${schema.tint ? ` style="--tint: ${schema.tint}"` : ""}>${Pie.icon(id)}</span>
      <span>${schema.label}</span>
      ${schema.view === "platform" ? (machines(schema) ? `<span class="sidebar-count">${machines(schema)}</span>` : "") : schema.view ? "" : `<span class="sidebar-count">${count(id, state)}</span>`}
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
      nav.innerHTML = Pie.sections.map((entry) => section(entry, state)).join("");
    },

    spinLogo() {
      logo.classList.remove("is-spinning");
      void logo.getBoundingClientRect();
      logo.classList.add("is-spinning");
    },

    bindLogo() {
      logo.addEventListener("animationend", () => logo.classList.remove("is-spinning"));
      logo.addEventListener("mouseenter", () => {
        if (!logo.classList.contains("is-spinning")) logo.classList.add("is-spinning");
      });
      this.spinLogo();
    },

    onSelect(handler) {
      nav.addEventListener("click", (event) => {
        const target = event.target.closest("[data-table]");
        if (target) handler(target.dataset.table);
      });
    },
  };
})();
