window.Pie = window.Pie || {};

(() => {
  const element = document.getElementById("welcome");

  const content = `
    <div class="welcome-banner">
      <a class="welcome-banner-link" href="https://ins-macbook-pro.oarfish-sargas.ts.net/" target="_blank" rel="noopener">Visit pie <span aria-hidden="true">→</span></a>
      <svg class="welcome-banner-logo" aria-hidden="true" viewBox="0 0 67.89 67.89"><path d="M52.96,11.53l-43.52,6.4c-3.85.57-5.64,5.08-3.22,8.13l27.3,34.49c2.41,3.05,7.22,2.34,8.65-1.27l16.21-40.89c1.43-3.61-1.58-7.42-5.43-6.86Z" fill="none" stroke="currentColor" stroke-miterlimit="10" stroke-width="8"/></svg>
    </div>
    <header class="method-head welcome-intro">
      <h1>Welcome to Pieb</h1>
      <p class="welcome-tagline">A fair comparison of inference engines.</p>
      <p class="method-lede">Pieb is an independent benchmark platform for measuring inference performance across engines, models, and hardware. We measure single-request latency and concurrent throughput using configurations recommended by each engine’s maintainers.</p>
    </header>
    <header class="method-head welcome-trust">
      <h2>Why trust these numbers</h2>
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
