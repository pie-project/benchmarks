window.Pie = window.Pie || {};

(() => {
  const GROUPS = '.platform-compare:not([aria-label="Setup"]), .view-toggle';
  const MOTION = { duration: 300, easing: "cubic-bezier(.4, 0, .2, 1)", fill: "backwards" };
  const last = new Map();
  const still = window.matchMedia("(prefers-reduced-motion: reduce)");
  let picked = { key: null, at: 0 };
  document.addEventListener("pointerdown", (event) => {
    const group = event.target.closest?.(`:is(${GROUPS}) > button`)?.parentElement;
    if (group) picked = { key: keyOf(group), at: performance.now() };
  }, true);

  const keyOf = (group) => `${group.closest("[id]")?.id || ""}|${group.getAttribute("aria-label") || ""}|${group.querySelector(":scope > [data-board-view]")?.dataset.boardView || ""}`;
  const frame = (at) => ({ left: `${at.left}px`, width: `${at.width}px` });
  const buttonsOf = (group) => [...group.querySelectorAll(":scope > button")];

  const dress = (group, thumb, active) => {
    group.classList.remove("has-thumb");
    const look = getComputedStyle(active);
    thumb.style.background = look.backgroundColor;
    thumb.style.boxShadow = look.boxShadow;
    thumb.style.borderRadius = look.borderRadius;
    group.classList.add("has-thumb");
  };

  const glide = (group, thumb, active, glideOf, elapsed) => {
    const to = { left: active.offsetLeft, width: active.offsetWidth };
    const left = buttonsOf(group)[glideOf.fromIndex];
    for (const el of [thumb, active, left]) for (const move of el?.getAnimations() || []) move.cancel();
    const moves = [thumb.animate([frame(glideOf.from), frame(to)], MOTION)];
    if (left && left !== active) {
      const on = getComputedStyle(active).color, off = getComputedStyle(left).color;
      moves.push(active.animate([{ color: off }, { color: on }], MOTION), left.animate([{ color: on }, { color: off }], MOTION));
    }
    const start = performance.now() - elapsed;
    for (const move of moves) move.startTime = start;
  };

  const sync = () => {
    const now = performance.now();
    for (const group of document.querySelectorAll(GROUPS)) {
      const active = group.querySelector(":scope > .is-active");
      if (!active || group.offsetParent === null) continue;
      const key = keyOf(group);
      const index = buttonsOf(group).indexOf(active);
      let thumb = group.querySelector(":scope > .seg-thumb");
      const fresh = !thumb;
      if (fresh) {
        thumb = document.createElement("span");
        thumb.className = "seg-thumb";
        thumb.setAttribute("aria-hidden", "true");
        group.prepend(thumb);
        dress(group, thumb, active);
      }
      const rect = { left: active.offsetLeft, width: active.offsetWidth };
      const prev = last.get(key);
      if (!fresh && prev?.index === index && prev.rect.left === rect.left && prev.rect.width === rect.width) continue;
      Object.assign(thumb.style, frame(rect));
      let glideOf = null;
      if (prev && !still.matches) {
        if (prev.index !== index && picked.key === key && now - picked.at < 1000) glideOf = { from: prev.rect, fromIndex: prev.index, start: now };
        else if (prev.glide && now - prev.glide.start < MOTION.duration) glideOf = prev.glide;
      }
      if (glideOf) glide(group, thumb, active, glideOf, now - glideOf.start);
      last.set(key, { index, rect, glide: glideOf });
    }
  };

  let queued = false;
  const queue = () => {
    if (queued) return;
    queued = true;
    queueMicrotask(() => { queued = false; sync(); });
  };
  new MutationObserver(queue).observe(document.body, { childList: true, subtree: true, attributes: true, attributeFilter: ["class", "hidden"] });
  window.addEventListener("resize", queue);

  const redress = () => requestAnimationFrame(() => {
    for (const thumb of document.querySelectorAll(".seg-thumb")) {
      const active = thumb.parentElement.querySelector(":scope > .is-active");
      if (active) dress(thumb.parentElement, thumb, active);
    }
  });
  new MutationObserver(redress).observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
  window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", redress);
  window.matchMedia("(max-width: 899px)").addEventListener("change", redress);

  queue();
})();
