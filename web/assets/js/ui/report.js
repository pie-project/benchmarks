window.Pie = window.Pie || {};

(() => {
  const button = document.getElementById("report-button");
  const dialog = document.getElementById("report-dialog");
  const text = document.getElementById("report-text");
  const ISSUES = "https://github.com/pie-project/pie/issues/new";

  // what the reader was looking at, so the report can be traced to the numbers
  const context = () => {
    const state = Pie.state || {};
    const lines = [`Page: ${Pie.schema?.[state.table]?.label || state.table || ""}`, `Release: ${state.release || ""}`];
    if (state.table === "overview" && state.overview) {
      const o = state.overview;
      lines.push(`Mac: ${o.hardware || ""}`, `Workload: ${o.workload || ""}`, `Engine: ${o.engine || ""}`);
    }
    lines.push(`Link: ${location.href}`);
    return lines.join("\n");
  };

  button.addEventListener("click", () => {
    text.value = "";
    dialog.showModal();
    text.focus();
  });

  dialog.addEventListener("close", () => {
    if (dialog.returnValue !== "send") return;
    const kind = dialog.querySelector('input[name="report-kind"]:checked')?.value || "Report";
    const body = `${text.value.trim()}\n\n---\n${context()}`;
    const url = `${ISSUES}?title=${encodeURIComponent(`[Benchmarks] ${kind}`)}&body=${encodeURIComponent(body)}`;
    window.open(url, "_blank", "noopener");
  });
})();
