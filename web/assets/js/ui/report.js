window.Pie = window.Pie || {};

(() => {
  const button = document.getElementById("report-button");
  if (!button) return;  // the toolbar's report button is hidden for now
  const dialog = document.getElementById("report-dialog");
  const form = dialog.querySelector("form");
  const text = document.getElementById("report-text");
  const status = document.getElementById("report-status");
  const send = document.getElementById("report-send");
  // the report service files the issue; without it, a pre-filled issue opens instead
  const ENDPOINT = "";
  const ISSUES = "https://github.com/pie-project/pie/issues/new";
  const TITLE = "Benchmarks: Issue report";  // one fixed title, so every report from the site reads and sorts alike

  const reset = () => {
    text.value = "";
    status.textContent = "";
    send.disabled = false;
    send.textContent = "Send";
  };

  button.addEventListener("click", () => {
    reset();
    dialog.showModal();
    text.focus();
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
      const url = `${ISSUES}?title=${encodeURIComponent(TITLE)}&body=${encodeURIComponent(note)}`;
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
        body: JSON.stringify({ title: TITLE, text: note }),
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
