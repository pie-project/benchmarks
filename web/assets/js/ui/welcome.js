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
    <header class="method-head welcome-trust">
      <h2>Message to a Reader</h2>
      <p class="method-lede">Every question you ask a cloud model leaves your hands. It travels to a data center you will never see, runs on hardware you do not control, and is kept under terms you did not write. Your drafts, your code, your health questions, your half-formed ideas, the most personal things you think, quietly become someone else’s data.</p>
      <p class="method-lede">It does not have to be this way. The computer on your desk is already powerful enough to run the models that matter, and your words never need to leave it. What has been missing is not the hardware but the software: an engine that makes local AI as fast and as effortless as the cloud, so that choosing privacy never means choosing less.</p>
      <p class="method-lede">That is why we built Pie, and why we measure it in the open against every engine we can. Intelligence should run where you live, answer only to you, and belong to everyone. This is our step toward that future.</p>
      <p class="welcome-sign">With love, the Pie team!</p>
    </header>
    <header class="method-head welcome-trust welcome-pie">
      <h2>Pie: Programmable Inference Engine</h2>
      <p class="method-lede">Most inference engines today grew one model and one feature at a time, and many have become hard to extend and harder to maintain. We built Pie to give the open-source community a cleaner foundation.</p>
      <p class="method-lede">Pie borrows its design from operating systems. It manages the hardware as precisely as a kernel manages memory and compute, and runs your programs on top of it as lightweight processes called inferlets. The result is an engine that is simple to build on, and fast and fluid for everyone who uses it.</p>
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
