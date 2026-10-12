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
        <a class="welcome-banner-link is-primary" href="https://liszt.ai/etude" target="_blank" rel="noopener"><svg class="is-stroke" viewBox="0 0 16 16" aria-hidden="true"><path d="M8 2.5v8M4.5 7 8 10.5 11.5 7M3 13.5h10"/></svg>Étude<span class="welcome-version">0.1.24</span></a>
        <a class="welcome-banner-link" href="https://github.com/pie-project/pie" target="_blank" rel="noopener"><svg viewBox="0 0 16 16" aria-hidden="true"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0 0 16 8c0-4.42-3.58-8-8-8z"/></svg>GitHub</a>
      </div>
    </div>
    <header class="method-head welcome-intro">
      <h1>LLM Inference Engine Benchmarks</h1>
      <p class="welcome-tagline">Performance without compromise.</p>
      <p class="method-lede">An independent benchmark platform for measuring inference performance across engines, models, and hardware.</p>
    </header>
    <div class="welcome-body">
    <div class="welcome-art" aria-hidden="true">
      <div class="stack-layer is-weights" title="Model weights"><svg viewBox="0 0 24 24"><path d="M12 3 3 8l9 5 9-5-9-5z"/><path d="m3 12 9 5 9-5"/><path d="m3 16 9 5 9-5"/></svg></div>
      <div class="stack-layer is-engine" title="Inference engine"><svg class="is-pie" viewBox="0 0 67.89 67.89"><path d="M52.96,11.53l-43.52,6.4c-3.85.57-5.64,5.08-3.22,8.13l27.3,34.49c2.41,3.05,7.22,2.34,8.65-1.27l16.21-40.89c1.43-3.61-1.58-7.42-5.43-6.86Z"/></svg></div>
      <div class="stack-layer is-silicon" title="GPU silicon"><svg viewBox="0 0 24 24"><rect x="6" y="6" width="12" height="12" rx="2"/><rect x="9.5" y="9.5" width="5" height="5" rx="1"/><path d="M9 2.5v3M15 2.5v3M9 18.5v3M15 18.5v3M2.5 9h3M2.5 15h3M18.5 9h3M18.5 15h3"/></svg></div>
    </div>
    <header class="method-head welcome-trust">
      <h2>Message to a Reader</h2>
      <p class="method-lede">Every question you ask a cloud model leaves your hands. It travels to a data center you will never see, runs on hardware you do not control, and is kept under terms you did not write. Your drafts, your code, your health questions, your half-formed ideas, the most personal things you think, quietly become someone else’s data.</p>
      <p class="method-lede">It does not have to be this way. The computer on your desk is already powerful enough to run the models that matter, and your words never need to leave it. What has been missing is not the hardware but the software: an engine that makes local AI as fast and as effortless as the cloud, so that choosing privacy never means choosing less.</p>
      <p class="method-lede">That is why we built Pie, and why we measure it in the open against every engine we can. Intelligence should run where you live, answer only to you, and belong to everyone. This is our step toward that future.</p>
      <p class="welcome-sign">With love, the Pie team!</p>
    </header>
    </div>`;

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
