window.Pie = window.Pie || {};

(() => {
  const element = document.getElementById("welcome");

  const content = `
    <div class="welcome-banner">
      <div class="welcome-banner-copy">
        <h2 class="welcome-banner-title">Run AI on your Mac!</h2>
        <p class="welcome-banner-sub">Free and private, for the whole world.</p>
      </div>
      <div class="welcome-banner-actions">
        <a class="welcome-banner-link is-primary" href="https://liszt.ai/etude" target="_blank" rel="noopener"><svg class="is-stroke" viewBox="0 0 16 16" aria-hidden="true"><path d="M8 2.5v8M4.5 7 8 10.5 11.5 7M3 13.5h10"/></svg>Download</a>
        <a class="welcome-banner-link" href="https://github.com/pie-project/pie" target="_blank" rel="noopener"><svg viewBox="0 0 16 16" aria-hidden="true"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0 0 16 8c0-4.42-3.58-8-8-8z"/></svg>GitHub</a>
      </div>
      <svg class="welcome-banner-logo" aria-hidden="true" viewBox="0 0 67.89 67.89"><path d="M52.96,11.53l-43.52,6.4c-3.85.57-5.64,5.08-3.22,8.13l27.3,34.49c2.41,3.05,7.22,2.34,8.65-1.27l16.21-40.89c1.43-3.61-1.58-7.42-5.43-6.86Z" fill="none" stroke="currentColor" stroke-miterlimit="10" stroke-width="8"/></svg>
    </div>
    <header class="method-head welcome-intro">
      <h1>LLM Inference Engine Benchmarks</h1>
      <p class="welcome-tagline">Performance without compromise.</p>
      <p class="method-lede">An independent benchmark platform for measuring inference performance across engines, models, and hardware.</p>
    </header>
    <header class="method-head welcome-trust">
      <h2>A note to the reader</h2>
      <p class="method-lede">Measuring inference engines accurately is difficult, and a comparison is only as credible as its fairness. Fairness toward every engine measured here is therefore our first obligation to the reader.</p>
      <p class="method-lede">Each engine is evaluated under the configuration its own maintainers recommend for the model and the kind of generation in question, so that its results reflect what its users would reasonably expect of it. Pie runs on every platform in this study, which allows each model to be compared on each machine without omission.</p>
      <p class="method-lede">This site is a continuous record. Each Pie release is measured against the most recent release of every other engine available at that time, so each release records the state of the field on the date it was measured.</p>
      <p class="method-lede">Every engine is measured under two conditions: a single request at a time, as a single agent or thread would issue them, and many concurrent requests, enough to saturate the bandwidth of the hardware. Together they show how well each engine manages memory and compute for each model, on each machine.</p>
      <p class="welcome-sign">With love, the Pie team!</p>
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
