window.Pie = window.Pie || {};

(() => {
  const PAGES = ["table-container", "overview", "platform", "welcome", "approach", "reports", "methods", "board", "checks"];
  for (const id of PAGES) {
    const page = document.getElementById(id);
    if (page) page.hidden = true;
  }
  document.querySelector(".filter-bar")?.setAttribute("hidden", "");

  let loading = true;
  Pie.loading = {
    done() {
      if (!loading) return false;
      loading = false;
      return true;
    },
  };
})();
