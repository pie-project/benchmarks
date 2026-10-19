window.Pie = window.Pie || {};

// Services: what Liszt AI offers around pie.
(() => {
  const element = document.getElementById("services");

  const content = `
    <header class="inf-hero">
      <h1 class="inf-title">Services</h1>
      <p class="inf-text">Liszt AI helps teams run pie on their own hardware.</p>
    </header>`;

  Pie.services = {
    element,
    render(state) {
      element.hidden = state.table !== "services";
      if (element.hidden || element.dataset.ready === "1") return;
      element.innerHTML = `<div class="method-inner">${content}</div>`;
      element.dataset.ready = "1";
    },
  };
})();
