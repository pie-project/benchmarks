window.Pie = window.Pie || {};

// Profiler: where a long agentic workload spends the hardware's time. Visitors will upload a trace of their own
// run and see it as a timeline; until uploads open, the page shows an empty state.
(() => {
  const element = document.getElementById("profiler");

  const content = `
    <section class="prof-drop" aria-disabled="true">
      <svg class="prof-drop-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 15V4M7.5 8.5 12 4l4.5 4.5"/><path d="M4 14v4.5A1.5 1.5 0 0 0 5.5 20h13a1.5 1.5 0 0 0 1.5-1.5V14"/></svg>
      <p class="prof-drop-title">No Traces</p>
      <p class="prof-drop-text">Run your workload on Pie to record a trace.</p>
    </section>`;

  Pie.profiler = {
    element,
    render(state) {
      element.hidden = state.table !== "profiler";
      if (element.hidden || element.dataset.ready === "1") return;
      element.innerHTML = `<div class="method-inner prof-inner">${content}</div>`;
      element.dataset.ready = "1";
    },
  };
})();
