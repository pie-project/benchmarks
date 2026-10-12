window.Pie = window.Pie || {};

(() => {
  const element = document.getElementById("welcome");

  const content = `
    <img class="welcome-banner" src="assets/img/welcome-banner.jpg" alt="Pieb: Programmable Inference Engine Benchmark. Comprehensive benchmark for inference engines." width="2000" height="766">
    <header class="method-head">
      <h1>Why trust these numbers</h1>
      <p class="method-lede">Measuring inference engines accurately is difficult, and a comparison is only as credible as its fairness. Fairness toward every engine measured here is therefore our first obligation to the reader.</p>
      <p class="method-lede">Each engine is evaluated under the configuration its own maintainers recommend for the model and the kind of generation in question, so that its results reflect what its users would reasonably expect of it. pie runs on every platform in this study, which allows each model to be compared on each machine without omission.</p>
      <p class="method-lede">This site is a continuous record. Each pie release is measured against the most recent release of every other engine available at that time, so each release records the state of the field on the date it was measured.</p>
      <p class="method-lede">Every engine is measured under two conditions: a single request at a time, as a single agent or thread would issue them, and many concurrent requests, enough to saturate the bandwidth of the hardware. Together they show how well each engine manages memory and compute for each model, on each machine.</p>
    </header>`;

  Pie.welcome = {
    element,
    render(state) {
      element.hidden = state.table !== "welcome";
      if (!element.hidden && element.dataset.ready !== "1") {
        element.innerHTML = `<div class="method-inner">${content}</div>`;
        element.dataset.ready = "1";
      }
    },
  };
})();
