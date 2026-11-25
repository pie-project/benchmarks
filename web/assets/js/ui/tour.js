window.Pie = window.Pie || {};

(() => {
  const KEY = "pieTourSeen";
  const seen = () => { try { return localStorage.getItem(KEY) === "1"; } catch { return true; } };
  const remember = () => { try { localStorage.setItem(KEY, "1"); } catch { } };
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  const nav = (id) => document.querySelector(`.sidebar-item[data-table="${id}"]`);
  const go = async (id) => { if (Pie.state?.table !== id) { nav(id)?.click(); await sleep(400); } };
  const find = async (selector) => {
    for (let i = 0; i < 40; i++) { const el = [...document.querySelectorAll(selector)].find((e) => e.offsetParent); if (el) return el; await sleep(150); }
    return null;
  };

  const MARK = `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2.75 21 5.25V7.75L12 10.25 3 7.75V5.25Z"/>
    <path d="M3 10.75 12 13.25 21 10.75V13.25L12 15.75 3 13.25Z"/><path d="M3 16.25 12 18.75 21 16.25V18.75L12 21.25 3 18.75Z"/></svg>`;

  const STEPS = [
    { target: () => find('.sidebar-item[data-table="speedups"]'), title: "Performance",
      text: "Pie vs. the fastest other engine on identical hardware, model and workload." },
    { target: () => find('.sidebar-item[data-table="checks"]'), title: "Quality",
      text: "KL divergence and task scores verified against a reference engine." },
    { target: async () => {
        await go("speedups");
        if (Pie.platform?.setCompare) { Pie.platform.setCompare("engines"); document.dispatchEvent(new CustomEvent("pie:refresh")); }
        for (let i = 0; i < 40; i++) {
          const cell = [...document.querySelectorAll(".platform-table td.is-gap, .platform-table td.is-explained")]
            .find((td) => { const r = td.getBoundingClientRect(); return td.offsetParent && r.left > 0 && r.right <= innerWidth - 16; });
          if (cell) return cell;
          await sleep(150);
        }
        return null;
      }, title: "Highlighted Gaps",
      text: "Yellow: the two fastest engines are 25% or more apart, so the cell needs review. Green: a profile of both engines confirms the gap." },
    { target: async () => { await go("reasons"); return find("#reasons .reasons-item, #reasons .reasons-empty"); }, title: "Profiling",
      text: "Every gap under the slower engine, with a profile of both engines showing where its time goes." },
    { target: async () => { await go("board"); return find(".board-welcome-primary"); }, title: "pie-bench",
      text: "Every number is reproducible. Run pip install pie-bench on your own hardware and share your results." },
    { target: async () => { await go("board"); return find('.board-welcome-secondary[data-board-go-page="approach"]'); }, title: "Bench Book",
      text: "The measurement methodology, and how every engine gets a fair setup." },
  ];

  const sheet = () => `
    <div class="tour-backdrop" data-tour>
      <section class="tour-sheet" role="dialog" aria-modal="true" aria-labelledby="tour-title">
        <div class="tour-body">
          <span class="tour-mark">${MARK}</span>
          <h2 class="tour-title" id="tour-title">Welcome!</h2>
          <p class="tour-lead">Pie Benchmarks is open, reproducible benchmarking of LLM inference engines on every major platform.</p>
        </div>
        <div class="tour-actions">
          <a class="tour-button" href="https://github.com/pie-project/benchmarks" target="_blank" rel="noopener"><svg class="tour-button-icon is-filled" viewBox="0 0 16 16" aria-hidden="true"><path d="M8 .2a8 8 0 0 0-2.5 15.6c.4 0 .5-.2.5-.4v-1.5c-2.2.5-2.7-1-2.7-1-.4-.9-.9-1.2-.9-1.2-.7-.5.1-.5.1-.5.8.1 1.2.8 1.2.8.7 1.3 1.9.9 2.4.7.1-.5.3-.9.5-1.1-1.8-.2-3.6-.9-3.6-4 0-.9.3-1.6.8-2.1-.1-.2-.4-1 .1-2.1 0 0 .7-.2 2.2.8a7.6 7.6 0 0 1 4 0c1.5-1 2.2-.8 2.2-.8.4 1.1.2 1.9.1 2.1.5.6.8 1.3.8 2.1 0 3.1-1.9 3.8-3.6 4 .3.3.6.8.6 1.5v2.2c0 .2.1.5.6.4A8 8 0 0 0 8 .2z"/></svg>Open Source</a>
          <a class="tour-button" href="https://pypi.org/project/pie-bench/" target="_blank" rel="noopener" title="pip install pie-bench"><svg class="tour-button-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3 4 7.5v9L12 21l8-4.5v-9L12 3z"/><path d="m4 7.5 8 4.5 8-4.5M12 12v9"/></svg>pie-bench</a>
          <span class="tour-spacer"></span>
          <button type="button" class="tour-button is-default" data-tour-next>Take the Tour</button>
        </div>
      </section>
    </div>`;

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
  const close = () => {
    const walked = !!layer();
    document.querySelector("[data-tour]")?.remove(); layer()?.remove(); lit = null; step = -1; token++; remember();
    if (walked) go("board");
  };
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
    if (!target) return show(i + 1);
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
