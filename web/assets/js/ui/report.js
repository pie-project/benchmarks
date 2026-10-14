window.Pie = window.Pie || {};

(() => {
  const button = document.getElementById("report-button");
  const dialog = document.getElementById("report-dialog");
  const form = dialog.querySelector("form");
  const text = document.getElementById("report-text");
  const shot = document.getElementById("report-shot");
  const include = document.getElementById("report-include");
  // the thumbnail opens the screenshot full size in a new tab
  document.getElementById("report-thumb").addEventListener("click", () => {
    if (!image) return;
    const view = window.open();
    if (view) view.document.write(`<title>Screenshot</title><img src="${image}" style="max-width:100%">`);
  });
  const status = document.getElementById("report-status");
  const send = document.getElementById("report-send");
  // the report service files the issue with the screenshot attached; without it, a pre-filled issue opens instead
  const ENDPOINT = "";
  const ISSUES = "https://github.com/pie-project/pie/issues/new";
  const CAPTURE = "https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js";
  let image = "";

  const context = () => {
    const state = Pie.state || {};
    const lines = [`Page: ${Pie.schema?.[state.table]?.label || state.table || ""}`, `Release: ${state.release || ""}`];
    if (state.table === "overview" && state.overview) {
      const o = state.overview;
      lines.push(`Workload: ${o.workload || ""}`, `Engine: ${o.engine || ""}`);
    }
    lines.push(`Link: ${location.href}`, `Window: ${window.innerWidth}x${window.innerHeight}`);
    return lines.join("\n");
  };

  const loadCapture = () => window.html2canvas ? Promise.resolve() : new Promise((resolve, reject) => {
    const script = document.createElement("script");
    script.src = CAPTURE;
    script.onload = resolve;
    script.onerror = reject;
    document.head.append(script);
  });

  // what the reader sees right now, at screen size
  const capture = async () => {
    try {
      await loadCapture();
      const canvas = await window.html2canvas(document.body, {
        x: window.scrollX, y: window.scrollY, width: window.innerWidth, height: window.innerHeight,
        // the sheet opens at once and is left out of the picture; a phone captures at 1x, which is plenty for a report
        backgroundColor: getComputedStyle(document.body).backgroundColor, logging: false,
        scale: window.matchMedia("(max-width: 899px)").matches ? 1 : Math.min(window.devicePixelRatio || 1, 2),
        ignoreElements: (node) => node === dialog,
      });
      return canvas.toDataURL("image/png");
    } catch {
      return "";
    }
  };

  const reset = () => {
    text.value = "";
    status.textContent = "";
    send.disabled = false;
    send.textContent = "Send";
  };

  // the library loads once the page is idle, so a tap on the flag never waits for the network
  const idle = window.requestIdleCallback || ((fn) => setTimeout(fn, 2000));
  idle(() => loadCapture().catch(() => {}));

  button.addEventListener("click", () => {
    reset();
    image = "";
    shot.hidden = true;
    include.checked = true;
    dialog.showModal();
    text.focus();
    // the screenshot is taken behind the open sheet and shown when it is ready
    capture().then((taken) => {
      if (!dialog.open) return;
      image = taken;
      shot.hidden = !image;
      if (image) shot.querySelector("img").src = image;
    });
  });

  document.getElementById("report-cancel").addEventListener("click", () => dialog.close());

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const note = text.value.trim();
    if (!note) {
      text.focus();
      return;
    }
    if (!ENDPOINT) {
      const url = `${ISSUES}?title=${encodeURIComponent(`[Benchmarks] ${note.split("\n")[0].slice(0, 70)}`)}&body=${encodeURIComponent(`${note}\n\n---\n${context()}`)}`;
      window.open(url, "_blank", "noopener");
      dialog.close();
      return;
    }
    send.disabled = true;
    send.textContent = "Sending…";
    try {
      const response = await fetch(ENDPOINT, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: note, context: context(), image: include.checked ? image : "" }),
      });
      const result = await response.json();
      if (!response.ok || !result.url) throw new Error(result.error || response.status);
      status.innerHTML = `Thanks. <a href="${Pie.format.escape(result.url)}" target="_blank" rel="noopener">View the issue</a>`;
      send.textContent = "Sent";
    } catch {
      status.textContent = "Couldn’t send the report. Please try again.";
      send.disabled = false;
      send.textContent = "Send";
    }
  });
})();
