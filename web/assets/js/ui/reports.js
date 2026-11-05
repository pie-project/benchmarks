window.Pie = window.Pie || {};

// Reports: a measurement that looks wrong, filed by anyone signed in and kept in Supabase (supabase/measurement_reports.sql);
// a maintainer attaches the pull request that fixes it, which marks it fixed.
(() => {
  const element = document.getElementById("reports");
  const esc = (text) => Pie.format.escape(String(text ?? ""));
  const TABLE = "measurement_reports";
  const STATUS = { open: "Open", fixed: "Fixed", not_a_bug: "Not a bug" };

  let reports = null;  // null until read; a string when the table cannot be read
  let maintainer = false;
  let sending = false;

  const nameOf = (table, id) => {
    const row = (Pie.store.rows(table) || []).find((r) => r.id === id);
    return row?.name || row?.label || id;
  };
  // a picker per part of the measurement, its options the catalog's
  const select = (table, label) => `
    <label class="reports-field"><span>${label}</span>
      <select name="${table}" required><option value="">Choose…</option>${(Pie.store.rows(table) || [])
        .map((r) => `<option value="${esc(r.id)}">${esc(r.name || r.label || r.id)}</option>`).join("")}</select></label>`;

  const form = () => {
    if (!Pie.account?.configured) return "";
    if (!Pie.signedIn()) return `
      <div class="method-pane reports-form">
        <h2>Report a measurement</h2>
        <p class="method-summary">Seen a number that looks wrong? Log in to tell us which one and why.</p>
        <button type="button" class="reports-send" data-reports-login>Log In to Report</button>
      </div>`;
    return `
      <form class="method-pane reports-form">
        <h2>Report a measurement</h2>
        <p class="method-summary">Tell us which number looks wrong and why. We review every report.</p>
        <div class="reports-grid">
          ${select("hardware", "Machine")}${select("engines", "Engine")}${select("models", "Model")}${select("workloads", "Workload")}
          <label class="reports-field"><span>Value shown</span><input name="value" maxlength="60" placeholder="e.g. 42.1 tok/s"></label>
        </div>
        <label class="reports-field is-wide"><span>What is off</span><textarea name="note" required minlength="10" maxlength="4000" rows="4" placeholder="What you expected, what you saw, and anything that would help us reproduce it."></textarea></label>
        <div class="reports-actions"><span class="reports-status" role="status"></span><button type="submit" class="reports-send"${sending ? " disabled" : ""}>Send report</button></div>
      </form>`;
  };

  const card = (r) => `
    <article class="method-pane reports-card" data-id="${r.id}">
      <div class="reports-card-head">
        <h3>${esc(nameOf("engines", r.engine))} · ${esc(nameOf("models", r.model))}</h3>
        <span class="reports-badge is-${esc(r.status)}">${STATUS[r.status] || esc(r.status)}</span>
      </div>
      <p class="reports-where">${esc(nameOf("hardware", r.hardware))} · ${esc(nameOf("workloads", r.workload))}${r.value ? ` · <b>${esc(r.value)}</b>` : ""}</p>
      <p class="reports-note">${esc(r.note)}</p>
      <p class="reports-meta">${esc(r.reporter || "A visitor")} · ${new Date(r.created_at).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })}${r.fix_url ? ` · <a href="${esc(r.fix_url)}" target="_blank" rel="noopener">The fix</a>` : ""}</p>
      ${maintainer ? `
      <form class="reports-fix">
        <input name="fix_url" type="url" pattern="https://github\\.com/.+" placeholder="https://github.com/pie-project/pie/pull/…" value="${esc(r.fix_url || "")}">
        <select name="status">${Object.entries(STATUS).map(([k, v]) => `<option value="${k}"${k === r.status ? " selected" : ""}>${v}</option>`).join("")}</select>
        <button type="submit">Save</button>
      </form>` : ""}
    </article>`;

  const list = () => {
    if (reports === null) return `<p class="reports-empty">Loading reports…</p>`;
    if (typeof reports === "string") return `<p class="reports-empty">${esc(reports)}</p>`;
    if (!reports.length) return `<p class="reports-empty">No reports yet.</p>`;
    return reports.map(card).join("");
  };

  const draw = () => {
    if (element.hidden) return;
    element.innerHTML = `
      <div class="method-inner reports-inner">
        ${form()}
        <div class="board-section-head"><div class="board-section-text"><h1 class="board-title">Reports</h1></div></div>
        <div class="reports-list">${list()}</div>
      </div>`;
  };

  const load = async () => {
    try {
      const client = await Pie.account.client();
      const { data, error } = await client.from(TABLE).select("*").order("created_at", { ascending: false }).limit(200);
      if (error) throw error;
      reports = data;
      const user = Pie.account.user();
      maintainer = false;
      if (user) {
        const { data: row } = await client.from("maintainers").select("user_id").eq("user_id", user.id).maybeSingle();
        maintainer = Boolean(row);
      }
    } catch {
      reports = "Reports are not set up yet.";
    }
    draw();
  };

  element.addEventListener("click", (event) => {
    if (event.target.closest("[data-reports-login]")) Pie.account.open();
  });

  element.addEventListener("submit", async (event) => {
    event.preventDefault();
    const target = event.target;
    const data = Object.fromEntries(new FormData(target));
    const client = await Pie.account.client();
    if (target.classList.contains("reports-fix")) {
      const id = Number(target.closest("[data-id]").dataset.id);
      const status = data.fix_url && data.status === "open" ? "fixed" : data.status;  // a fix attached closes it
      const { error } = await client.from(TABLE).update({ fix_url: data.fix_url || null, status }).eq("id", id);
      if (!error) await load();
      return;
    }
    const user = Pie.account.user();
    sending = true;
    target.querySelector(".reports-send").disabled = true;
    const { error } = await client.from(TABLE).insert({
      reporter: user?.user_metadata?.full_name || user?.email?.split("@")[0] || null,
      hardware: data.hardware, engine: data.engines, model: data.models, workload: data.workloads,
      value: data.value || null, note: data.note.trim(),
    });
    sending = false;
    if (error) {
      target.querySelector(".reports-send").disabled = false;
      target.querySelector(".reports-status").textContent = "Couldn’t send the report. Please try again.";
      return;
    }
    await load();
    element.querySelector(".reports-status")?.replaceChildren("Thanks. Your report is below.");
  });

  // measurements picked on the Performance or Quality table: a sheet that names them and asks what is off
  const sheet = document.createElement("dialog");
  sheet.className = "reports-sheet";
  document.body.append(sheet);
  let flagged = [];   // one report row per picked measurement, sharing the note
  let onSent = null;
  const fmt = (n) => (typeof n === "number" ? n.toLocaleString("en-US", { maximumFractionDigits: n < 10 ? 2 : 0 }) : n);
  const valueOf = (row, source) => source === "quality"
    ? (row.score != null ? `Score ${fmt(row.score)}` : "")
    : [["decode_tok_s", "decode"], ["prefill_tok_s", "prefill"], ["output_tok_s", "output"]]
      .filter(([k]) => row[k] != null).map(([k, label]) => `${fmt(row[k])} tok/s ${label}`).join(", ");
  sheet.addEventListener("submit", async (event) => {
    event.preventDefault();
    const note = sheet.querySelector("textarea").value.trim();
    const status = sheet.querySelector(".reports-status");
    if (note.length < 10) { status.textContent = "Tell us a little more: at least a sentence."; status.hidden = false; return; }
    const send = sheet.querySelector(".reports-send");
    send.disabled = true;
    const user = Pie.account.user();
    try {
      const client = await Pie.account.client();
      const reporter = user?.user_metadata?.full_name || user?.email?.split("@")[0] || null;
      const { error } = await client.from(TABLE).insert(flagged.map((f) => ({ ...f, note, reporter })));
      if (error) throw error;
      sheet.close();
      onSent?.();
      reports = null;  // read again on the next visit to Reports
    } catch {
      status.textContent = "Couldn’t send the report. Please try again.";
      status.hidden = false;
      send.disabled = false;
    }
  });
  sheet.addEventListener("click", (event) => {
    if (event.target.closest("[data-sheet-cancel]") || event.target === sheet) sheet.close();
  });

  // signing in or out redraws the form and the maintainer's fields
  document.addEventListener("pie:account", () => { if (!element.hidden) load(); });

  Pie.reports = {
    element,
    // open the sheet for the selected rows of the Performance (results) or Quality table, once signed in;
    // `sent` runs once the reports are filed (the table clears its selection); `numbers` are the rows' numbers in the table
    flag(rows, source, sent, numbers) {
      if (!Pie.account?.configured || !rows.length) return;
      if (!Pie.signedIn()) { Pie.account.open(); return; }  // a report is filed under an account: log in first
      onSent = sent;
      flagged = rows.map((row) => ({
        source, row_id: Pie.table.keyOf(row),
        hardware: row.hardware || row.platform || "unknown", engine: row.engine, model: row.model,
        workload: (source === "quality" ? row.task : row.workload) || "unknown", value: valueOf(row, source) || null,
      }));
      // what each one is, in words, for its pill's hover
      const describe = (f) => [nameOf("engines", f.engine), nameOf("models", f.model), nameOf("hardware", f.hardware),
        source === "quality" ? f.workload : nameOf("workloads", f.workload), f.value].filter((x) => x && x !== "unknown").join(" · ");
      const n = flagged.length;
      const what = n === 1 ? describe(flagged[0]) : `${n} measurements selected`;
      // drawn with the login sheet's own parts (account.css), so the two read as one
      sheet.innerHTML = `
        <form method="dialog" class="account-sheet reports-sheet-form">
          <h2 class="account-title">Report measurements</h2>
          <p class="account-sub" title="${esc(flagged.map(describe).join("\n"))}">${esc(what)}</p>
          <div class="account-email">
            <textarea aria-label="What looks wrong" required minlength="10" maxlength="4000" rows="3" placeholder="What looks wrong?"></textarea>
          </div>
          <p class="account-note is-error reports-status" role="status" hidden></p>
          <button type="submit" class="account-primary reports-send">Report</button>
          <button type="button" class="account-cancel" data-sheet-cancel>Cancel</button>
        </form>`;
      sheet.showModal();
      sheet.querySelector("textarea").focus();
    },
    render(state) {
      const was = element.hidden;
      element.hidden = state.table !== "reports";
      if (element.hidden) return;
      if (was || reports === null) { draw(); load(); }
    },
  };
})();
