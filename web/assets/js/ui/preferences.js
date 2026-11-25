window.Pie = window.Pie || {};

(() => {
  const root = document.documentElement;
  const compact = window.matchMedia("(max-width: 899px)");

  const save = (key, value) => {
    try {
      localStorage.setItem(key, value);
    } catch {
      return;
    }
  };

  const toggle = (attribute, storageKey, on, off) => {
    const next = root.dataset[attribute] === on ? off : on;
    root.dataset[attribute] = next;
    save(storageKey, next);
  };

  const MOON = '<path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/>';
  const SUN = '<circle cx="12" cy="12" r="4.2"/><path d="M12 1.75v3M12 19.25v3M1.75 12h3M19.25 12h3M4.75 4.75l2.1 2.1M17.15 17.15l2.1 2.1M4.75 19.25l2.1-2.1M17.15 6.85l2.1-2.1"/>';
  const syncSwitch = () => {
    const row = document.getElementById("sidebar-theme");
    if (!row) return;
    const dark = root.dataset.theme === "dark";
    row.innerHTML = `<svg viewBox="0 0 24 24" aria-hidden="true">${dark ? SUN : MOON}</svg><span>${dark ? "Light Mode" : "Dark Mode"}</span>`;
  };
  syncSwitch();

  Pie.preferences = {
    toggleTheme() {
      toggle("theme", "theme", "dark", "light");
      syncSwitch();
    },

    compact,

    toggleSidebar() {
      if (compact.matches) {
        this.showDrawer(root.dataset.drawer !== "open");
        return;
      }
      toggle("sidebar", "sidebar", "hidden", "shown");
      if (root.dataset.sidebar === "shown") Pie.sidebar.spinLogo();
    },

    showDrawer(open) {
      if (open) {
        root.dataset.drawer = "open";
        Pie.sidebar.spinLogo();
      } else {
        delete root.dataset.drawer;
      }
    },
  };
})();
