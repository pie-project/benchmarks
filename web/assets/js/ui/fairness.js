window.Pie = window.Pie || {};

// The rules every engine is measured under, in a popover that drops down from "Test Conditions" beside the numbers.
(() => {
  // as a macOS Get Info panel: a column per topic, a row per rule, the value on the right and a short note under it
  const GROUPS = [
    ["Workload", [
      { tint: "#30d158", icon: "M4 6h16M4 12h16M4 18h10", big: "512", unit: "tokens", label: "Prompt", line: "Same seeded text everywhere." },
      { tint: "#30d158", icon: "M5 5h14v10H9l-4 4zM8 9h8M8 12h5", big: "Random words", label: "Prompt text", line: "Common English words in a seeded random order, not a real question. Speed of raw decode does not depend on it; speculation's acceptance does, so Spec numbers sit below what real chat or code reach." },
      { tint: "#30d158", icon: "M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8zM4 21a8 8 0 0 1 16 0", big: "Fixed", label: "System prompt", line: "“You are a helpful benchmarking assistant.” on every engine, the words as the user's message." },
      { tint: "#ff9f0a", icon: "M5 12h11M12 7l5 5-5 5M20 5v14", big: "256", unit: "tokens", label: "Answer", line: "Fixed length on every engine." },
      { tint: "#64d2ff", icon: "M12 3v18M5.6 6.6l12.8 10.8M18.4 6.6 5.6 17.4", big: "Cold", label: "Cache", line: "No prefix-cache hits." },
      { tint: "#ff453a", icon: "M12 3c2 3 5 4.5 5 9a5 5 0 0 1-10 0c0-2.5 1.5-3.5 2-5 1 1.5 2 2 3-4z", big: "Warm", label: "Engine", line: "Warmup runs aren't counted." },
    ]],

    ["Statistics", [
      { tint: "#30d158", icon: "M4 6h16M4 12h16M4 18h16", big: "3", label: "Rounds", line: "Middle one kept; up to 5 if they disagree." },
      { tint: "#64d2ff", icon: "M6 4v16M12 4v16M18 4v16", big: "6-8", label: "Requests per round", line: "Their median is the round." },
      { tint: "#ff453a", icon: "M12 4l9 16H3zM12 10v4M12 17v.5", big: "2%", label: "Noise", line: "Wider spread is flagged noisy." },
      { tint: "#0a84ff", icon: "M4 4h6v6H4zM14 4h6v6h-6zM4 14h6v6H4zM14 14h6v6h-6z", big: "Isolated", label: "Features", line: "One feature at a time, compared with Raw." },
      { tint: "#30d158", icon: "M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18zM12 16a4 4 0 1 0 0-8 4 4 0 0 0 0 8zM12 12h.01", big: "Max throughput", label: "Goal", line: "Every engine is set up for its highest tokens per second." },
    ]],
    ["Inference", [
      { tint: "#0a84ff", icon: "M4 12h15M15 8l4 4-4 4", big: "Greedy", label: "Decoding", line: "Temperature 0, top-p 1." },
      { tint: "#0a84ff", icon: "M6 20V5M12 20v-8M18 20v-5", big: "Top-1", label: "Sampling", line: "Only the highest-probability token is taken." },
      { tint: "#0a84ff", icon: "M10 13.5V5a2 2 0 0 1 4 0v8.5a4 4 0 1 1-4 0z", big: "0", label: "Temperature", line: "No randomness in the choice of tokens." },
      { tint: "#bf5af2", icon: "M12 3a6 6 0 0 0-3.5 10.9V17h7v-3.1A6 6 0 0 0 12 3zM9.5 21h5", big: "Off", label: "Thinking", line: "No reasoning tokens." },
      { tint: "#0a84ff", icon: "M3 7l6 5-6 5zM11 7l6 5-6 5zM20 6v12", big: "Lossless", label: "Speculation", line: "Greedy verify. Off in Raw." },
      { tint: "#0a84ff", icon: "M4 12h6M14 12h6M10 7l4 5-4 5", big: "Like for like", label: "Drafters", line: "The same model is compared across engines. Models with a shared architecture, such as linear attention, are compared only with each other." },
      { tint: "#ffd60a", icon: "M5 5h14v14H5zM5 12h14M12 5v14", big: "bf16", label: "KV cache", line: "On every engine." },
      { tint: "#5e5ce6", icon: "M7 11V8a5 5 0 0 1 10 0v3M5 11h14v10H5z", big: "Latest", label: "Releases", line: "Newest at run time, same on every Mac." },
    ]],

  ];
  const esc = (text) => Pie.format.escape(text);

  // the same rows as the site's other menus: a grey heading per topic, one line per rule with its value at the end,
  // a separator between topics; the rule's note shows when the pointer rests on its row
  const content = GROUPS.map(([title, items]) => `
    <div class="popover-heading">${esc(title)}</div>${items.map((t) => `
    <div class="rules-row" title="${esc(t.line)}">
      <svg viewBox="0 0 24 24" aria-hidden="true"><path d="${t.icon}"/></svg>
      <span class="popover-label">${esc(t.label)}</span>
      <span class="popover-detail">${esc(t.big)}${t.unit ? ` ${esc(t.unit)}` : ""}</span>
    </div>`).join("")}`).join(`<div class="popover-separator"></div>`);

  // the rules drop down under their "Test Conditions" button, as a macOS popover: a click outside,
  // Escape or the button again closes it
  const panel = document.getElementById("rules-popover");
  panel.innerHTML = content;
  let owner = null;
  const close = () => {
    panel.hidden = true;
    owner?.setAttribute("aria-expanded", "false");
    owner = null;
  };
  const open = (button) => {
    owner?.setAttribute("aria-expanded", "false");
    owner = button;
    button.setAttribute("aria-expanded", "true");
    panel.hidden = false;
    panel.scrollTop = 0;
    const r = button.getBoundingClientRect();
    // anchored to the button's leading edge, or its trailing edge when it sits on the right, and never closer than 8px
    // to the window's edge (its width without a scrollbar)
    const width = document.documentElement.clientWidth;
    const left = r.left + r.width / 2 > width / 2 ? r.right - panel.offsetWidth : r.left;
    panel.style.left = `${Math.max(8, Math.min(left, width - panel.offsetWidth - 8))}px`;
    panel.style.top = `${r.bottom + 6}px`;
    // the whole list shows; it scrolls only when the window is too short to hold it
    panel.style.maxHeight = `${window.innerHeight - r.bottom - 16}px`;
  };
  // listened in the capture phase: the other pickers stop their clicks from bubbling, and opening one must close this
  document.addEventListener("click", (event) => {
    const button = event.target.closest("[data-rules]");
    if (button) {
      if (owner === button) close();
      else {
        Pie.popover?.close();  // one menu open at a time
        open(button);
      }
      return;
    }
    if (!panel.hidden && !panel.contains(event.target)) close();
  }, true);
  // scrolling the page or a table moves the button away from the menu, so the menu closes, as a macOS menu does
  document.addEventListener("scroll", (event) => {
    if (!panel.hidden && !panel.contains(event.target)) close();
  }, true);
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && !panel.hidden) close();
  });
  window.addEventListener("resize", close);
})();
