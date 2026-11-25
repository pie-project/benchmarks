window.Pie = window.Pie || {};

(() => {
  const tooltip = document.getElementById("chart-tooltip");
  let shownFor = null;
  let lastPointer = "mouse";

  document.addEventListener("pointerdown", (event) => {
    lastPointer = event.pointerType;
  }, true);

  const hide = () => {
    if (!shownFor) return;
    shownFor = null;
    tooltip.hidden = true;
    tooltip.classList.remove("is-card");
  };

  const place = (target) => {
    const box = target.getBoundingClientRect();
    const x = Math.min(box.left + box.width / 2 - tooltip.offsetWidth / 2, window.innerWidth - tooltip.offsetWidth - 12);
    const below = box.bottom + 8;
    const y = below + tooltip.offsetHeight > window.innerHeight - 12 ? box.top - tooltip.offsetHeight - 8 : below;
    tooltip.style.left = `${Math.max(12, x)}px`;
    tooltip.style.top = `${Math.max(12, y)}px`;
  };

  document.addEventListener("click", (event) => {
    if (shownFor && !shownFor.contains(event.target)) hide();
  }, true);
  document.addEventListener("scroll", hide, { capture: true, passive: true });

  Pie.tapCard = {
    isTouch() {
      return lastPointer !== "mouse";
    },

    toggle(target, html, card = false) {
      if (shownFor === target) {
        hide();
        return;
      }
      tooltip.innerHTML = html;
      tooltip.classList.toggle("is-card", card);
      tooltip.hidden = false;
      shownFor = target;
      place(target);
    },

    hide,
  };
})();
