window.Pie = window.Pie || {};

// Inferlets: a headline that says what they are, then the playground that will run them.
(() => {
  const element = document.getElementById("inferlets");

  const content = `
    <header class="inf-hero">
      <h1 class="inf-title">Absolute control over your hardware.</h1>
      <p class="inf-label">The most humane intelligence ever.</p>
      <p class="inf-text">Inferlets are programmable OS processes that manage how a model thinks, as it runs. The most granular control over your tokens in the world.</p>
    </header>
    <section class="store-shelf">
      <div class="term is-placeholder">
        <div class="term-bar"><span class="term-lights" aria-hidden="true"><i></i><i></i><i></i></span></div>
        <div class="term-body"><div class="term-out is-dim">The playground is in development.</div></div>
      </div>
    </section>`;

  Pie.inferlets = {
    element,
    render(state) {
      element.hidden = state.table !== "inferlets";
      if (element.hidden || element.dataset.ready === "1") return;
      element.innerHTML = `<div class="method-inner">${content}</div>`;
      element.dataset.ready = "1";
    },
  };
})();
