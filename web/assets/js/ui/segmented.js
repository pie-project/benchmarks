window.Pie = window.Pie || {};

// A segmented control's selection glides to the segment picked, as iOS moves its thumb: one fill that slides and
// resizes on a soft ease while the two labels cross-fade with it, so the words change as the thumb arrives, not
// before. The pages rebuild their bars on every pick, sometimes twice in a row, so each control remembers which
// segment was chosen and any glide under way; a rebuild carries the glide on from where it was rather than starting it
// over, and a rebuild that keeps the same segment chosen never moves the thumb at all.
(() => {
  // the setups (Decode, Prefill, Peak FLOPs) mark their pick by colour alone and switch at once, so they are left out
  const GROUPS = '.platform-compare:not([aria-label="Setup"]), .view-toggle';
  const MOTION = { duration: 300, easing: "cubic-bezier(.4, 0, .2, 1)", fill: "backwards" };  // a soft start and a long settle, as a damped spring reads
  const last = new Map();  // a control's place on the page -> { index, rect, glide: { from, fromIndex, start } }
  const still = window.matchMedia("(prefers-reduced-motion: reduce)");
  // only a segment the viewer just pressed glides; a page switch or a rebuild for any other reason sets the thumb in place
  let picked = { key: null, at: 0 };
  document.addEventListener("pointerdown", (event) => {
    const group = event.target.closest?.(`:is(${GROUPS}) > button`)?.parentElement;
    if (group) picked = { key: keyOf(group), at: performance.now() };
  }, true);

  // two controls under one id with one label (the Overview's view switches, both "View") are told apart by what they switch
  const keyOf = (group) => `${group.closest("[id]")?.id || ""}|${group.getAttribute("aria-label") || ""}|${group.querySelector(":scope > [data-board-view]")?.dataset.boardView || ""}`;
  // the thumb's two edges move as one: its left and its width are laid out on the same frame, where a transform on the
  // compositor and a width on the page could land a frame apart and stretch one side ahead of the other
  const frame = (at) => ({ left: `${at.left}px`, width: `${at.width}px` });
  const buttonsOf = (group) => [...group.querySelectorAll(":scope > button")];

  // the thumb wears the chosen segment's own fill, read while the segment still shows it, so each theme keeps its look
  const dress = (group, thumb, active) => {
    group.classList.remove("has-thumb");
    const look = getComputedStyle(active);
    thumb.style.background = look.backgroundColor;
    thumb.style.boxShadow = look.boxShadow;
    thumb.style.borderRadius = look.borderRadius;
    group.classList.add("has-thumb");
  };

  // the thumb from one place to the next, already `elapsed` milliseconds in; the label it leaves fades to the resting
  // colour as the one it reaches fades up
  const glide = (group, thumb, active, glideOf, elapsed) => {
    const to = { left: active.offsetLeft, width: active.offsetWidth };
    const left = buttonsOf(group)[glideOf.fromIndex];
    for (const el of [thumb, active, left]) for (const move of el?.getAnimations() || []) move.cancel();  // one glide at a time
    const moves = [thumb.animate([frame(glideOf.from), frame(to)], MOTION)];
    if (left && left !== active) {
      const on = getComputedStyle(active).color, off = getComputedStyle(left).color;
      moves.push(active.animate([{ color: off }, { color: on }], MOTION), left.animate([{ color: on }, { color: off }], MOTION));
    }
    // the clock starts when the glide does, not when its frame began: a page that took 100ms to rebuild would otherwise
    // open the glide a third of the way through; until the next frame reaches it the thumb holds its first place
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
      // measured once the control holds its thumb (has-thumb places it), so a segment's left is the control's own
      const rect = { left: active.offsetLeft, width: active.offsetWidth };
      const prev = last.get(key);
      if (!fresh && prev?.index === index && prev.rect.left === rect.left && prev.rect.width === rect.width) continue;
      Object.assign(thumb.style, frame(rect));
      let glideOf = null;
      if (prev && !still.matches) {
        if (prev.index !== index && picked.key === key && now - picked.at < 1000) glideOf = { from: prev.rect, fromIndex: prev.index, start: now };  // a new pick: glide from the old one
        else if (prev.glide && now - prev.glide.start < MOTION.duration) glideOf = prev.glide;  // a rebuild mid-glide: carry on
      }
      if (glideOf) glide(group, thumb, active, glideOf, now - glideOf.start);
      last.set(key, { index, rect, glide: glideOf });
    }
  };

  // set before the page paints: a rebuilt bar is never drawn without its thumb, so nothing blinks
  let queued = false;
  const queue = () => {
    if (queued) return;
    queued = true;
    queueMicrotask(() => { queued = false; sync(); });
  };
  new MutationObserver(queue).observe(document.body, { childList: true, subtree: true, attributes: true, attributeFilter: ["class", "hidden"] });
  window.addEventListener("resize", queue);

  // a theme change repaints the chosen segments, so each thumb takes its fill again
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
