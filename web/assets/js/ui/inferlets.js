window.Pie = window.Pie || {};

(() => {
  const element = document.getElementById("inferlets");

  const content = `
    <header class="method-head">
      <h1>Inferlets</h1>
      <p class="method-lede">This page is under development.</p>
    </header>`;

  Pie.inferlets = {
    element,
    render(state) {
      element.hidden = state.table !== "inferlets";
      if (!element.hidden && element.dataset.ready !== "1") {
        element.innerHTML = `<div class="method-inner">${content}</div>`;
        element.dataset.ready = "1";
      }
    },
  };
})();
