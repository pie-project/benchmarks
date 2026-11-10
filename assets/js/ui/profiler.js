window.Pie = window.Pie || {};

// Profiler: where a long agentic workload spends the hardware's time. A visitor opens a trace of their own run (.pie)
// with Open Trace… or by dropping it anywhere on the page, as a Mac app opens a document. Viewing it is not built
// yet, so a picked trace only names itself; any other file is refused before it is read.
(() => {
  const element = document.getElementById("profiler");
  const EXT = ".pie";

  const content = `
    <section class="prof-drop">
      <svg class="prof-drop-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8l-5-5v4a1 1 0 0 0 1 1h4"/><path d="M7.5 14h2.25l1.5-3.5 2 7 1.5-3.5h1.75"/></svg>
      <p class="prof-drop-title">No Traces</p>
      <p class="prof-drop-text">Record a trace with Pie, then open it here.</p>
      <button class="prof-choose" type="button">Open Trace…</button>
      <input class="prof-input" type="file" accept="${EXT}" hidden>
    </section>`;

  const esc = (value) => Pie.format.escape(value);

  const open = (file) => {
    const title = element.querySelector(".prof-drop-title");
    const text = element.querySelector(".prof-drop-text");
    if (!file.name.toLowerCase().endsWith(EXT)) {
      title.textContent = "Not a Pie Trace";
      text.innerHTML = `“${esc(file.name)}” can’t be opened. Choose a file that ends in ${EXT}.`;
      return;
    }
    title.textContent = file.name;
    text.textContent = "Viewing traces is coming soon.";
  };

  const wire = () => {
    const input = element.querySelector(".prof-input");
    element.querySelector(".prof-choose").addEventListener("click", () => input.click());
    input.addEventListener("change", () => {
      if (input.files[0]) open(input.files[0]);
      input.value = "";
    });
    // the whole page is the drop target: it takes the accent ring while a file is held over it
    let depth = 0;
    const hasFile = (event) => [...(event.dataTransfer?.types || [])].includes("Files");
    element.addEventListener("dragenter", (event) => {
      if (!hasFile(event)) return;
      depth += 1;
      element.classList.add("is-dropping");
    });
    element.addEventListener("dragleave", () => {
      depth = Math.max(0, depth - 1);
      if (!depth) element.classList.remove("is-dropping");
    });
    element.addEventListener("dragover", (event) => {
      if (hasFile(event)) event.preventDefault();
    });
    element.addEventListener("drop", (event) => {
      event.preventDefault();
      depth = 0;
      element.classList.remove("is-dropping");
      const file = event.dataTransfer.files[0];
      if (file) open(file);
    });
  };

  Pie.profiler = {
    element,
    render(state) {
      element.hidden = state.table !== "profiler";
      if (element.hidden || element.dataset.ready === "1") return;
      element.innerHTML = `<div class="method-inner prof-inner">${content}</div>`;
      element.dataset.ready = "1";
      wire();
    },
  };
})();
