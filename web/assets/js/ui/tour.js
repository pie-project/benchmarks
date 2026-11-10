window.Pie = window.Pie || {};

// A first visit's tour: a welcome sheet, then a walk through the site that dims the page and lights one thing at a
// time, opening the pages it talks about. Shown once per browser; ?tour=1 shows it again.
(() => {
  const KEY = "pieTourSeen";
  const seen = () => { try { return localStorage.getItem(KEY) === "1"; } catch { return true; } };
  const remember = () => { try { localStorage.setItem(KEY, "1"); } catch { /* private windows can refuse storage */ } };
  const esc = (text) => String(text).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  const nav = (id) => document.querySelector(`.sidebar-item[data-table="${id}"]`);
  const go = async (id) => { if (Pie.state?.table !== id) { nav(id)?.click(); await sleep(400); } };
  // the first element a selector finds once the page has drawn it, or nothing after a few seconds
  const find = async (selector) => {
    for (let i = 0; i < 40; i++) { const el = [...document.querySelectorAll(selector)].find((e) => e.offsetParent); if (el) return el; await sleep(150); }
    return null;
  };

  // the sidebar's mark: a model's weights on top, the hardware below, the engine between
  const MARK = `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2.75 21 5.25V7.75L12 10.25 3 7.75V5.25Z"/>
    <path d="M3 10.75 12 13.25 21 10.75V13.25L12 15.75 3 13.25Z"/><path d="M3 16.25 12 18.75 21 16.25V18.75L12 21.25 3 18.75Z"/></svg>`;

  const STEPS = [
    { target: () => find('.sidebar-item[data-table="speedups"]'), title: "Performance",
      text: "Relative Speed: pie against the fastest other engine on the same hardware, model and workload." },
    { target: () => find('.sidebar-item[data-table="checks"]'), title: "Quality",
      text: "pie's outputs checked against a reference engine, so speed never costs accuracy." },
    { target: async () => {
        await go("speedups");
        if (Pie.platform?.setCompare) { Pie.platform.setCompare("engines"); document.dispatchEvent(new CustomEvent("pie:refresh")); }
        return find(".platform-table td.is-gap");
      }, title: "Large gaps are yellow",
      text: "Engines 25% or more apart are marked yellow. Every one is reviewed, and a click opens its note." },
    { target: async () => { await go("gaps"); return (await find('#gaps .gaps-note[data-tip-kind="explained"]')) || find("#gaps .gaps-note[data-tip]"); }, title: "Every gap has a note",
      text: (note) => `Each gap gets its measured cause and a conclusion. Hover a row for the full note.${note.textContent.trim()
        ? ` <span class="tour-quote"><b>${esc(note.dataset.tipVs || "Note")} ${esc(note.dataset.tipGap || "")}</b><br>${esc(note.dataset.tip || note.textContent.trim())}</span>` : ""}` },
    { target: () => find('.sidebar-item[data-table="reports"]'), title: "CI Errors",
      text: "Every number is checked against the hardware's theoretical limit. One above it turns red and is listed here." },
    { target: async () => { await go("board"); return find(".board-welcome-primary"); }, title: "Open Source",
      text: "The benchmark CI is open, so every number can be reproduced. pie-bench, for runs on your own machine, is coming soon." },
  ];

  const sheet = () => `
    <div class="tour-backdrop" data-tour>
      <section class="tour-sheet" role="dialog" aria-modal="true" aria-labelledby="tour-title">
        <div class="tour-body">
          <span class="tour-mark">${MARK}</span>
          <h2 class="tour-title" id="tour-title">Welcome to Pie Benchmarks</h2>
          <p class="tour-lead">A quick look at how to read these numbers.</p>
        </div>
        <div class="tour-actions">
          <a class="tour-button" href="https://github.com/pie-project/benchmarks" target="_blank" rel="noopener">View CI on GitHub</a>
          <!-- the pip package for self-hosted runs that add data; it links to PyPI once it ships -->
          <button type="button" class="tour-button" disabled title="pip install pie-bench: run the benchmarks on your own machine and add the data. Coming soon"><svg class="tour-button-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3 4 7.5v9L12 21l8-4.5v-9L12 3z"/><path d="m4 7.5 8 4.5 8-4.5M12 12v9"/></svg>pie-bench <span class="tour-soon">Soon</span></button>
          <span class="tour-spacer"></span>
          <button type="button" class="tour-button is-default" data-tour-next>Take the Tour</button>
        </div>
      </section>
    </div>`;

  // the walk: a blocker over the page, a lit hole around the target, and a callout beside it
  let step = -1, lit = null, token = 0;
  const layer = () => document.querySelector("[data-tour-walk]");
  const place = () => {
    const walk = layer(); if (!walk || !lit) return;
    const r = lit.getBoundingClientRect(), pad = 6;
    Object.assign(walk.querySelector(".tour-spot").style, { left: `${r.left - pad}px`, top: `${r.top - pad}px`, width: `${r.width + pad * 2}px`, height: `${r.height + pad * 2}px` });
    const tip = walk.querySelector(".tour-tip"), w = tip.offsetWidth, h = tip.offsetHeight, gap = 14;
    let left = r.right + pad + gap, top = r.top + r.height / 2 - h / 2;
    if (left + w > innerWidth - 12) {
      left = Math.min(Math.max(12, r.left + r.width / 2 - w / 2), innerWidth - w - 12);
      top = r.bottom + pad + gap + h < innerHeight ? r.bottom + pad + gap : r.top - pad - gap - h;
    }
    Object.assign(tip.style, { left: `${left}px`, top: `${Math.min(Math.max(12, top), innerHeight - h - 12)}px` });
  };
  const close = () => { document.querySelector("[data-tour]")?.remove(); layer()?.remove(); lit = null; step = -1; token++; remember(); };
  const show = async (i) => {
    const mine = ++token;
    document.querySelector("[data-tour]")?.remove();
    if (i >= STEPS.length) return close();
    step = i;
    if (!layer()) document.body.insertAdjacentHTML("beforeend", `<div class="tour-walk" data-tour-walk><div class="tour-spot"></div>
      <div class="tour-tip" role="dialog" aria-live="polite"></div></div>`);
    const walk = layer();
    walk.classList.add("is-moving");
    const target = await STEPS[i].target();
    if (mine !== token) return;
    if (!target) return show(i + 1);  // nothing to show on this page today: the next step
    target.scrollIntoView({ block: "center", inline: "nearest" });
    await sleep(60);
    lit = target;
    const { title, text } = STEPS[i];
    walk.querySelector(".tour-tip").innerHTML = `
      <div class="tour-tip-count">${i + 1} of ${STEPS.length}</div>
      <h3>${title}</h3><p>${typeof text === "function" ? text(target) : text}</p>
      <div class="tour-tip-actions"><button type="button" class="tour-tip-skip" data-tour-close>Skip</button>
        ${i ? `<button type="button" class="tour-button" data-tour-back>Back</button>` : ""}
        <button type="button" class="tour-button is-default" data-tour-next>${i === STEPS.length - 1 ? "Done" : "Next"}</button></div>`;
    place();
    walk.classList.remove("is-moving");
    walk.querySelector("[data-tour-next]")?.focus();
  };
  const open = () => {
    if (document.querySelector("[data-tour]") || layer()) return;
    document.body.insertAdjacentHTML("beforeend", sheet());
    document.querySelector("[data-tour-next]")?.focus();
  };
  document.addEventListener("click", (event) => {
    if (event.target.closest("[data-tour-next]")) show(step + 1);
    else if (event.target.closest("[data-tour-back]")) show(Math.max(0, step - 1));
    else if (event.target.closest("[data-tour-close]") || event.target.matches("[data-tour]")) close();
  });
  document.addEventListener("keydown", (event) => {
    if (!document.querySelector("[data-tour]") && !layer()) return;
    if (event.key === "Escape") close();
    else if (layer() && (event.key === "ArrowRight" || event.key === "Enter")) { event.preventDefault(); show(step + 1); }
    else if (layer() && event.key === "ArrowLeft" && step > 0) show(step - 1);
  });
  addEventListener("resize", place);
  addEventListener("scroll", place, true);
  const again = new URLSearchParams(location.search).get("tour") === "1";
  const start = () => { if (again || !seen()) open(); };
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", start); else start();
  Pie.tour = { open };
})();
