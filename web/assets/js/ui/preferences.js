window.Pie = window.Pie || {};

(() => {
  const root = document.documentElement;
  // below the desktop width the sidebar is a slide-over above the page, as on iPhone and iPad in portrait
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

  // the slide-over's Dark Mode switch reads as on in the dark theme
  const syncSwitch = () => document.getElementById("sidebar-theme")?.setAttribute("aria-checked", String(root.dataset.theme === "dark"));
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

    // the slide-over is not a preference: it opens for one pick and closes again
    showDrawer(open) {
      if (open) {
        root.dataset.drawer = "open";
        // the logo spins as the slide-over comes in, as it does when the sidebar shows on a wider screen
        Pie.sidebar.spinLogo();
      } else {
        delete root.dataset.drawer;
      }
    },
  };
})();
