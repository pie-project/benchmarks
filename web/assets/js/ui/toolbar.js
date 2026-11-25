window.Pie = window.Pie || {};

(() => {
  const elements = {
    title: document.getElementById("toolbar-title"),
    subtitle: document.getElementById("toolbar-subtitle"),
    search: document.getElementById("search"),
    searchCancel: document.getElementById("search-cancel"),
    themeToggle: document.getElementById("theme-toggle"),
    sidebarToggle: document.getElementById("sidebar-toggle"),
  };

  const root = document.documentElement;

  Pie.toolbar = {
    elements,

    render(state, shown, total) {
      elements.title.textContent = Pie.schema[state.table].label;
      elements.subtitle.textContent = Pie.format.count(shown, total);
    },

    clearSearch() {
      elements.search.value = "";
      this.showSearch(false);
    },

    showSearch(open) {
      if (open) {
        root.dataset.search = "open";
      } else {
        delete root.dataset.search;
      }
    },

    focusSearch() {
      elements.search.focus();
    },
  };
})();
