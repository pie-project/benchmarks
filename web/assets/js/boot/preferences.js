(() => {
  const read = (key) => {
    try {
      return localStorage.getItem(key);
    } catch {
      return null;
    }
  };

  const root = document.documentElement;

  root.dataset.theme = read("theme") || "light";
  root.dataset.sidebar = read("sidebar") || "shown";
})();
