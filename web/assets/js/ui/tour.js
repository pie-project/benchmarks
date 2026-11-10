window.Pie = window.Pie || {};

// A first visit's tour: the page's few ideas on one sheet, as a Mac app's "What's New" sheet shows them, once per
// browser. ?tour=1 shows it again.
(() => {
  const KEY = "pieTourSeen";
  const seen = () => { try { return localStorage.getItem(KEY) === "1"; } catch { return true; } };
  const remember = () => { try { localStorage.setItem(KEY, "1"); } catch { /* private windows can refuse storage */ } };
  // the sidebar's own symbols, drawn the same way: Performance's chevrons, the gauge of the hardware limit, Engine Gaps' flag
  const CODE = '<path d="M8.5 7 3.5 12l5 5M15.5 7l5 5-5 5"/>';
  const ROWS = [
    [Pie.icon("speedups"), "Relative Speed", "Pie vs the fastest other engine on the same setup."],
    [Pie.icon("gaps"), "Gaps Reviewed", "Every gap of 25% or more is yellow and has a note."],
    [Pie.icon("methodology"), "CI Errors Watched", "A number above the hardware's limit turns red."],
    [`<svg viewBox="0 0 24 24" aria-hidden="true">${CODE}</svg>`, "Open Source", "Every number can be reproduced from the open CI."],
  ];
  // the sidebar's mark: a model's weights on top, the hardware below, the engine between
  const MARK = `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2.75 21 5.25V7.75L12 10.25 3 7.75V5.25Z"/>
    <path d="M3 10.75 12 13.25 21 10.75V13.25L12 15.75 3 13.25Z"/><path d="M3 16.25 12 18.75 21 16.25V18.75L12 21.25 3 18.75Z"/></svg>`;
  const sheet = () => `
    <div class="tour-backdrop" data-tour>
      <section class="tour-sheet" role="dialog" aria-modal="true" aria-labelledby="tour-title">
        <div class="tour-body">
          <span class="tour-mark">${MARK}</span>
          <h2 class="tour-title" id="tour-title">Welcome to Pie Benchmarks</h2>
                    <ul class="tour-rows">${ROWS.map(([glyph, head, line]) => `
            <li class="tour-row"><span class="tour-icon">${glyph}</span>
              <div><h3>${head}</h3><p>${line}</p></div></li>`).join("")}
          </ul>
        </div>
        <div class="tour-actions">
          <a class="tour-button" href="https://github.com/pie-project/benchmarks" target="_blank" rel="noopener">View CI on GitHub</a>
          <!-- the pip package for self-hosted runs that add data; it links to PyPI once it ships -->
          <button type="button" class="tour-button" disabled title="pip install pie-bench: run the benchmarks on your own machine and add the data. Coming soon">pie-bench <span class="tour-soon">Soon</span></button>
          <span class="tour-spacer"></span>
          <button type="button" class="tour-button is-default" data-tour-close>Continue</button>
        </div>
      </section>
    </div>`;
  const close = () => { document.querySelector("[data-tour]")?.remove(); remember(); };
  const open = () => {
    if (document.querySelector("[data-tour]")) return;
    document.body.insertAdjacentHTML("beforeend", sheet());
    document.querySelector("[data-tour-close]")?.focus();
  };
  document.addEventListener("click", (event) => {
    if (event.target.closest("[data-tour-close]") || event.target.matches("[data-tour]")) close();
  });
  document.addEventListener("keydown", (event) => { if (event.key === "Escape" && document.querySelector("[data-tour]")) close(); });
  const again = new URLSearchParams(location.search).get("tour") === "1";
  const start = () => { if (again || !seen()) open(); };
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", start); else start();
  Pie.tour = { open };
})();
