window.Pie = window.Pie || {};

// Services: what Liszt offers around pie.
(() => {
  const element = document.getElementById("services");

  const content = `
    <header class="inf-hero">
      <h1 class="inf-title">Your hardware, at its limit.</h1>
      <p class="inf-label">Agents at the speed of thought.</p>
      <p class="inf-text">Liszt manages both the hardware and the thinking in agentic workloads, on an efficient runtime from a single Mac to a GPU cluster.</p>
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
