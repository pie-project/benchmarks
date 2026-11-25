window.Pie = window.Pie || {};

(() => {
  const GROUPS = [
    ["Workload", [
      { tint: "#30d158", icon: "M4 6h16M4 12h16M4 18h10", big: "512", unit: "tokens", label: "Prompt", line: "Same seeded text everywhere." },
      { tint: "#30d158", icon: "M5 5h14v10H9l-4 4zM8 9h8M8 12h5", big: "Random words", label: "Prompt text", line: "Common English words in a seeded random order, not a real question, after the system message “You are a helpful benchmarking assistant.” Speed of raw decode does not depend on it; speculation's acceptance does, so Spec numbers sit below what real chat or code reach." },
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
    ["Shortcuts", [
      { big: "1 2 3 4", label: "Setup", line: "Latency Decode, Prefill; Throughput Decode, Prefill, on a grid page." },
      { big: "V", label: "Switch view", line: "Relative Speed and Kernel Efficiency, on a platform's page." },
      { big: "Hold R", label: "Peek at the other view", line: "Shows the other view until the key is let go." },
      { big: "Hold U", label: "Show unavailable", line: "Shows the empty rows and columns until the key is let go." },
      { big: "[  ]", label: "Previous, next page", line: "Steps through the grid pages in the sidebar's order." },
      { big: "⌘S", label: "Sidebar", line: "Show or hide the sidebar." },
    ]],

  ];
  const QUALITY = [
    ["Full model", [
      { big: "MATH-500", label: "Benchmark", line: "Pie and one other engine, the same weights on the same machine." },
      { big: "Within noise", label: "Pass", line: "Pie's score stays inside the run's own noise of the other engine's; 5 points where a run has no noise figure." },
    ]],
    ["Model slice", [
      { big: "First token", label: "Check", line: "The same prompts on both engines, each forced to give exactly one token." },
      { big: "KL < 0.15", label: "Pass", line: "KL divergence between the two engines' first-token distributions." },
    ]],
    ["Inference", [
      { big: "Greedy", label: "Decoding", line: "Temperature 0, top-p 1." },
      { big: "Off", label: "Thinking", line: "No reasoning tokens." },
    ]],
  ];
  const esc = (text) => Pie.format.escape(text);

  const listOf = (groups) => groups.map(([title, items]) => `
    <div class="popover-heading">${esc(title)}</div>${items.map((t) => `
    <div class="rules-row" title="${esc(t.line)}">
      <span class="popover-label">${esc(t.label)}</span>
      <span class="popover-detail">${esc(t.big)}${t.unit ? ` ${esc(t.unit)}` : ""}</span>
    </div>`).join("")}`).join(`<div class="popover-separator"></div>`);
  const content = listOf(GROUPS), quality = listOf(QUALITY);

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
    panel.innerHTML = button.dataset.rules === "quality" ? quality : content;
    panel.hidden = false;
    panel.scrollTop = 0;
    const r = button.getBoundingClientRect();
    const width = document.documentElement.clientWidth;
    const left = r.left + r.width / 2 > width / 2 ? r.right - panel.offsetWidth : r.left;
    panel.style.left = `${Math.max(8, Math.min(left, width - panel.offsetWidth - 8))}px`;
    panel.style.top = `${r.bottom + 6}px`;
    panel.style.maxHeight = `${window.innerHeight - r.bottom - 16}px`;
  };
  document.addEventListener("click", (event) => {
    const button = event.target.closest("[data-rules]");
    if (button) {
      if (owner === button) close();
      else {
        Pie.popover?.close();
        open(button);
      }
      return;
    }
    if (!panel.hidden && !panel.contains(event.target)) close();
  }, true);
  document.addEventListener("scroll", (event) => {
    if (!panel.hidden && !panel.contains(event.target)) close();
  }, true);
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && !panel.hidden) close();
  });
  window.addEventListener("resize", close);
})();
