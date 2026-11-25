window.Pie = window.Pie || {};

(() => {
  const KEY = "pieResultDates";
  const MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
  const SHORT = new Intl.DateTimeFormat("en-US", { month: "short", day: "numeric" });
  const chevron = '<svg class="popup-chevron" viewBox="0 0 10 14" aria-hidden="true"><path d="M2 5l3-3 3 3M2 9l3 3 3-3"/></svg>';
  const element = document.createElement("div");
  element.className = "date-popover";
  element.hidden = true;
  document.body.appendChild(element);

  let range = (() => { try { return JSON.parse(localStorage.getItem(KEY)) || null; } catch { return null; } })();
  let picking = null;
  let month = null;
  let anchor = null;

  const save = () => { try { range ? localStorage.setItem(KEY, JSON.stringify(range)) : localStorage.removeItem(KEY); } catch { } };
  const dayOf = (row) => String(row?.measured || row?.date || "").slice(0, 10);
  const counts = (state) => {
    const out = {};
    for (const row of state.table === "quality" ? Pie.store.qualitySnapshot(state.release) : Pie.store.snapshot(state.release)) { const d = dayOf(row); if (d) out[d] = (out[d] || 0) + 1; }
    return out;
  };
  const label = (iso) => SHORT.format(new Date(`${iso}T12:00`));
  const span = (r) => (r.to === r.from ? label(r.from)
    : SHORT.formatRange(new Date(`${r.from}T12:00`), new Date(`${r.to}T12:00`)).replace(/\s*[–—]\s*/, r.from.slice(0, 7) === r.to.slice(0, 7) ? "-" : " - "));
  const pad = (n) => String(n).padStart(2, "0");

  const calendar = (state) => {
    const have = counts(state);
    const days = Object.keys(have).sort();
    if (!days.length) return `<p class="date-empty">No measured results yet</p>`;
    const [first, last] = [days[0].slice(0, 7), days[days.length - 1].slice(0, 7)];
    month = month && month >= first && month <= last ? month : (range?.to || days[days.length - 1]).slice(0, 7);
    const [y, m] = month.split("-").map(Number);
    const lead = (new Date(y, m - 1, 1).getDay() + 6) % 7;
    const total = new Date(y, m, 0).getDate();
    const [from, to] = picking ? [picking, picking] : range ? [range.from, range.to] : [null, null];
    const cells = [...Array(lead)].map(() => `<span></span>`);
    for (let d = 1; d <= total; d++) {
      const iso = `${month}-${pad(d)}`;
      const n = have[iso] || 0;
      const cls = [n ? "has-data" : "", from && iso >= from && iso <= to ? "is-in" : "", iso === from || iso === to ? "is-end" : ""].filter(Boolean).join(" ");
      cells.push(`<button type="button" class="${cls}" data-day="${iso}" title="${n ? `${n} result${n === 1 ? "" : "s"}` : "No results"}">${d}</button>`);
    }
    const shift = (dir) => { const t = new Date(y, m - 1 + dir, 1); return `${t.getFullYear()}-${pad(t.getMonth() + 1)}`; };
    return `<div class="date-head">
        <button type="button" class="date-nav" data-month="${shift(-1)}"${month <= first ? " disabled" : ""} aria-label="Previous month"><svg viewBox="0 0 16 16" aria-hidden="true"><path d="M10 3 5 8l5 5"/></svg></button>
        <b>${MONTHS[m - 1]} ${y}</b>
        <button type="button" class="date-nav" data-month="${shift(1)}"${month >= last ? " disabled" : ""} aria-label="Next month"><svg viewBox="0 0 16 16" aria-hidden="true"><path d="m6 3 5 5-5 5"/></svg></button>
      </div>
      <div class="date-week">${["M", "T", "W", "T", "F", "S", "S"].map((w) => `<span>${w}</span>`).join("")}</div>
      <div class="date-grid">${cells.join("")}</div>
      <div class="date-foot"><span>${picking ? "Pick the last day" : ""}</span>${range || picking ? `<button type="button" class="date-clear" data-clear>Show all</button>` : ""}</div>`;
  };

  const draw = (state) => { element.innerHTML = calendar(state); };
  const place = () => {
    const box = anchor.getBoundingClientRect();
    element.style.left = `${Math.max(8, Math.min(box.left, window.innerWidth - element.offsetWidth - 8))}px`;
    element.style.top = `${box.bottom + 6}px`;
  };
  const close = () => { element.hidden = true; picking = null; anchor = null; };
  const changed = () => { save(); document.dispatchEvent(new CustomEvent("pie:refresh")); };

  let current = null;
  element.addEventListener("click", (event) => {
    event.stopPropagation();
    const nav = event.target.closest("[data-month]");
    if (nav && !nav.disabled) { month = nav.dataset.month; draw(current); return; }
    if (event.target.closest("[data-clear]")) { range = null; picking = null; draw(current); changed(); return; }
    const day = event.target.closest("[data-day]")?.dataset.day;
    if (!day) return;
    if (!picking) { picking = day; draw(current); return; }
    range = day < picking ? { from: day, to: picking } : { from: picking, to: day };
    picking = null;
    changed();
    close();
  });
  document.addEventListener("click", (event) => {
    if (!element.hidden && !element.contains(event.target) && !event.target.closest("[data-dates]")) close();
  });
  document.addEventListener("keydown", (event) => { if (event.key === "Escape" && !element.hidden) close(); });
  window.addEventListener("resize", () => { if (anchor) place(); });

  Pie.dates = {
    button: () => `<span class="filter${range ? " is-set" : ""}"><button class="filter-button" type="button" data-dates aria-haspopup="dialog">${range ? span(range) : "Dates"}${chevron}</button></span>`,
    open(target, state) {
      if (!element.hidden && anchor === target) { close(); return; }
      current = state;
      anchor = target;
      month = null;
      element.hidden = false;
      draw(state);
      place();
    },
    close: () => { if (!element.hidden) close(); },
    active: () => Boolean(range),
    clear: () => { range = null; picking = null; try { localStorage.removeItem(KEY); } catch { } },
    keeps: (row) => !range || (dayOf(row) >= range.from && dayOf(row) <= range.to),
  };
})();
