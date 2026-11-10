window.Pie = window.Pie || {};

// A first visit's tour: the page's few ideas on one sheet, as a Mac app's "What's New" sheet shows them, once per
// browser. ?tour=1 shows it again.
(() => {
  const KEY = "pieTourSeen";
  const seen = () => { try { return localStorage.getItem(KEY) === "1"; } catch { return true; } };
  const remember = () => { try { localStorage.setItem(KEY, "1"); } catch { /* private windows can refuse storage */ } };
  const icon = (path) => `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="${path}"/></svg>`;
  const ROWS = [
    ["#007AFF", "M4 19V9M10 19V5M16 19v-7M22 19H2", "Relative Speed",
      "Pie vs the fastest other engine on the same setup."],
    ["#FF9500", "M12 3v12M12 19v.5M4 21h16L12 3z", "Gaps Reviewed",
      "Every gap of 25% or more is yellow and has a note."],
    ["#FF3B30", "M12 8v5M12 16v.5M3 12a9 9 0 1 0 18 0a9 9 0 1 0-18 0", "CI Errors Watched",
      "A number above the hardware's limit turns red."],
    ["#34C759", "M9 18l-6-6 6-6M15 6l6 6-6 6", "Open Source",
      "Every number can be reproduced from the open CI."],
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
                    <ul class="tour-rows">${ROWS.map(([tint, path, head, line]) => `
            <li class="tour-row"><span class="tour-icon" style="--tint:${tint}">${icon(path)}</span>
              <div><h3>${head}</h3><p>${line}</p></div></li>`).join("")}
          </ul>
        </div>
        <div class="tour-actions">
          <a class="tour-button" href="https://github.com/pie-project/benchmarks" target="_blank" rel="noopener">View CI on GitHub</a>
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
