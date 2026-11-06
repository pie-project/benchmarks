window.Pie = window.Pie || {};

// Reports: measurements flagged as wrong from the Performance and Quality tables, kept in Supabase
// (supabase/measurement_reports.sql) and listed here as a table; a maintainer attaches the pull request that fixes one.
(() => {
  const element = document.getElementById("reports");
  const esc = (text) => Pie.format.escape(String(text ?? ""));
  const TABLE = "measurement_reports";
  // a report is Open or Closed; "fixed" is what the table stores for Closed. The rest are older states, read but not offered
  const STATUS = { open: "Open", fixed: "Closed", not_a_bug: "Closed", verified: "Closed", rejected: "Closed" };
  const CHOICES = { open: "Open", fixed: "Closed" };

  let reports = null;  // null until read; a string when the table cannot be read
  let maintainer = false;

  // how many reports are open, for the sidebar's count: one small request straight to the table's REST endpoint, so
  // a visit that never opens Reports does not load Supabase's library; the full read keeps it current after
  let open = null;  // the filed reports still open, from the table
  // the Outliers card's red dots, reported on their own: worked out from the live data each time, so they always match
  // the card and leave once a number comes back inside its band (Pie.board.outliers)
  const outliers = () => {
    try { return Pie.board?.outliers?.() || []; } catch { return []; }
  };
  // an outlier closed by a maintainer: kept in outlier_status by its machine, model and setup (the outliers themselves are
  // worked out, not stored), so it reads Closed and leaves the counts until the data moves it again
  let closedOutliers = new Set();
  const keyOf = (o) => `${o.engine}|${o.hardware}|${o.model}|${o.setup}`;
  const isClosed = (o) => closedOutliers.has(keyOf(o));
  // a maintainer's status: the cell reads as every other status (its square and word), a pop-up under it, its arrows only
  // on hover, as a Mac list lets a cell be edited in place
  const statusPick = (o) => `<button type="button" class="reports-status-pick" data-reports-pick="status:${esc(keyOf(o))}" aria-haspopup="menu" aria-label="Status">${statusTag(isClosed(o) ? "fixed" : "open")}<svg class="popup-chevron" viewBox="0 0 10 14" aria-hidden="true"><path d="M2 5l3-3 3 3M2 9l3 3 3-3"/></svg></button>`;
  // closing or reopening an outlier, picked in the site's own menu
  const setStatus = async (key, closed) => {
    const client = await Pie.account.client();
    const { error } = await client.from("outlier_status").upsert({ key, status: closed ? "closed" : "open", updated_at: new Date().toISOString() });
    if (error) return;
    closed ? closedOutliers.add(key) : closedOutliers.delete(key);
    draw();
    showCount();
  };
  const openCount = () => (open === null && !outliers().length ? null : (open || 0) + outliers().filter((o) => !isClosed(o)).length);
  const showCount = () => {
    const slot = document.querySelector('.sidebar-item[data-table="reports"] .sidebar-count');
    const all = openCount();
    if (slot) slot.textContent = all ?? "";
    // and the Outliers card's Reports button, drawn before the count came
    for (const button of document.querySelectorAll("[data-board-reports]")) {
      let count = button.querySelector(".board-pick-count");
      if (!count && all) { count = document.createElement("span"); count.className = "board-pick-count"; button.append(count); }
      if (count) count.textContent = all || "";
    }
  };
  (async () => {
    const { url, anonKey } = Pie.authConfig || {};
    if (!url || !anonKey) return;
    try {
      const response = await fetch(`${url}/rest/v1/${TABLE}?select=id&status=eq.open`, { method: "HEAD", headers: { apikey: anonKey, Prefer: "count=exact" } });
      const total = response.ok && Number(response.headers.get("content-range")?.split("/")[1]);
      if (Number.isFinite(total)) { open = total; showCount(); }
    } catch { /* the count stays blank */ }
  })();

  const nameOf = (table, id) => {
    const row = (Pie.store.rows(table) || []).find((r) => r.id === id);
    return row?.name || row?.label || id;
  };
  const tag = Pie.format;
  const day = (t) => new Date(t).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
  // a status as the site's tables draw one: a small square before its name
  const STATUS_TAG = { open: "noisy", fixed: "pass", not_a_bug: "not_run", verified: "pass", rejected: "fail" };
  const statusTag = (s) => `<span class="status-tag is-${STATUS_TAG[s] || "not_run"}">${esc(STATUS[s] || s)}</span>`;

  // one row a report, in the Performance table's own style; a maintainer's row closes it in place
  // a red dot of the Outliers card as a report row: Pie on its machine, model and setup, why it stands out
  const OUTLIER_WORKLOAD = { decode: "decode", prefill: "prefill", batching: "batching", pbatch: "pbatch" };
  // a row's type, as the site's tables mark a category: a small coloured square before its name
  const TYPES = {
    limit: { label: "Exceeds Theoretical Limit", color: "#FF9500", title: "Pie measures above the hardware's theoretical maximum: the run or the limit's inputs are off" },
    report: { label: "Report", color: "#8E8E93", title: "Filed by a visitor" },
  };
  const typeTag = (t) => `<span class="cell-dot" style="--dot: ${TYPES[t].color}" title="${esc(TYPES[t].title)}">${esc(TYPES[t].label)}</span>`;
  // the Type filter in the bar: every type, or one, kept per browser
  let typeFilter = (() => { try { const v = localStorage.getItem("pieReportsType"); return TYPES[v] ? v : ""; } catch { return ""; } })();
  const keeps = (t) => !typeFilter || t === typeFilter;
  // one cell, opened from a link (#reports/<machine>/<model>/<setup>): only its rows, until its chip in the bar is cleared
  let focused = null;
  const inFocus = (r) => !focused || (r.hardware === focused.hardware && r.model === focused.model && (!focused.setup || !r.setup || r.setup === focused.setup));
  const outlierRow = (o, i) => `
    <tr class="is-outlier-row${isClosed(o) ? " is-closed" : ""}" data-pick>
      <td class="row-number">${i + 1}</td>
      <td>${typeTag("limit")}</td>
      <td>${statusTag(isClosed(o) ? "fixed" : "open")}</td>
      <td>${tag.engineTag(o.engine, nameOf("engines", o.engine))}</td>
      <td>${esc(nameOf("models", o.model))}${o.miniature ? ` <span class="reports-none">(slice)</span>` : ""}</td>
      <td>${tag.hardwareTag(o.hardware)}</td>
      <td><span class="workload-tag">${Pie.platform.degree(OUTLIER_WORKLOAD[o.setup])}${esc(o.label)}</span></td>
      <td class="is-numeric">${esc(`${Math.round(o.pie).toLocaleString("en-US")} ${o.unit}`)}</td>
      <td class="is-wide reports-auto">${o.above ? "Above theoretical limit" : `Slower than strongest competitor (${esc(nameOf("engines", o.best))} ${Math.round(o.bestValue).toLocaleString("en-US")} ${esc(o.unit)})`}</td>
      <td class="reports-auto">Auto</td>
      <td>${esc(o.measured ? day(String(o.measured).replace(" ", "T")) : dataDay())}</td>
      <td class="reports-fix-cell">${issueLinks(o)}</td>
    </tr>`;
  // an outlier's issue on pie: one stays open per platform ("[NVIDIA] Benchmarks", labelled benchmarks), its description the platform's current
  // list (tools/outlier_issues.py rewrites it as the data changes), so every row links to its platform's issue
  const ISSUES = "https://github.com/pie-project/pie/issues";
  const PLATFORM_NAME = { mac: "Apple", nvidia: "NVIDIA", amd: "AMD", tpu: "TPU", android: "Mobile", web: "WebGPU", cerebras: "Cerebras" };
  // each platform's issue number, written beside the data by tools/outlier_issues.py; until it is there the link says GitHub
  let trackers = {};
  fetch("data/trackers.json").then((r) => (r.ok ? r.json() : {})).then((t) => { trackers = t || {}; if (!element.hidden) draw(); }).catch(() => {});
  const issueLinks = (o) => {
    const code = Pie.platformOf(Pie.store.index.hardware[o.hardware] || {});
    const platform = PLATFORM_NAME[code] || "";
    const number = trackers[code];
    const link = number ? `${ISSUES}/${number}` : `${ISSUES}?q=${encodeURIComponent(`is:issue is:open label:benchmarks in:title "[${platform}] Benchmarks"`)}`;
    // plain text as a Mac list sets it, the site's outward arrow after it, as See Runs reads: a link only under the pointer
    return `<a class="reports-issue" href="${esc(link)}" target="_blank" rel="noopener" title="Open [${esc(platform)}] Benchmarks on GitHub">${esc(platform)} Reports<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M5 11 11 5M6 5h5v5"/></svg></a>`;
  };
  const dataDay = () => { const at = Pie.store.tables.updated_at; return at ? day(at) : ""; };
  const row = (r, i) => `
    <tr data-id="${r.id}" data-pick>
      <td class="row-number">${i + 1}</td>
      <td>${typeTag("report")}</td>
      <td>${statusTag(r.status)}</td>
      <td>${tag.engineTag(r.engine, nameOf("engines", r.engine))}</td>
      <td>${esc(nameOf("models", r.model))}</td>
      <td>${r.source === "quality" ? esc(r.hardware === "unknown" ? "" : nameOf("hardware", r.hardware)) : tag.hardwareTag(r.hardware)}</td>
      <td>${r.source === "quality" ? esc(r.workload) : tag.workloadTag(r.workload)}</td>
      <td class="is-numeric${r.value ? "" : " is-empty"}">${r.value ? esc(r.value) : "—"}</td>
      <td class="is-wide" data-note="${esc([r.note, r.version && `Version: ${r.version}`, r.config && `Setup: ${r.config}`, r.link].filter(Boolean).join("\n"))}">${esc(r.note)}${r.link ? ` · <a href="${esc(r.link)}" target="_blank" rel="noopener">Logs</a>` : ""}</td>
      <td>${esc(r.reporter || "—")}</td>
      <td>${day(r.created_at)}</td>
      <td class="reports-fix-cell">${maintainer ? `
        <form class="reports-fix">
          <input name="fix_url" type="url" pattern="https://github\\.com/.+" placeholder="Pull request link" value="${esc(r.fix_url || "")}">
          <select name="status">${Object.entries(CHOICES).map(([k, v]) => `<option value="${k}"${k === (r.status === "open" ? "open" : "fixed") ? " selected" : ""}>${v}</option>`).join("")}</select>
          <button type="submit">Save</button>
        </form>` : r.fix_url ? `<a href="${esc(r.fix_url)}" target="_blank" rel="noopener">${esc(r.fix_url.replace(/^https:\/\/github\.com\//, ""))}</a>` : `<span class="reports-none">—</span>`}</td>
    </tr>`;

  // the table is always drawn, its header at once, as the site's other tables are: while the reports load the body
  // stays empty, and no reports, or none readable, is the one quiet row the other tables show when nothing matches
  const COLUMNS = 12;
  const list = () => {
    const note = (text) => `<tr><td class="table-empty" colspan="${COLUMNS}">${esc(text)}</td></tr>`;
    // the filed reports first, newest first, then the outliers the data shows now
    const filed = (Array.isArray(reports) ? reports : []).filter((r) => keeps("report") && inFocus(r));
    const found = outliers().filter((o) => keeps("limit") && inFocus(o));
    shown = reports === null && !found.length ? "" : `${(filed.length + found.length).toLocaleString("en-US")} ${filed.length + found.length === 1 ? "row" : "rows"}`;
    const body = reports === null && !found.length ? ""
      : filed.length || found.length ? filed.map(row).join("") + found.map((o, i) => outlierRow(o, filed.length + i)).join("")
      : typeof reports === "string" ? note(reports) : note("No reports yet");
    return `
      <div class="reports-table-wrap">
        <table class="data-table reports-table">
          <thead><tr><th class="row-number" aria-label="Row"></th><th>Type</th><th>Status</th><th>Engine</th><th>Model</th><th>Hardware</th><th>Workload</th><th class="is-numeric">Value</th><th>Details</th><th>Reported by</th><th>Date</th><th>Issue</th></tr></thead>
          <tbody>${body}</tbody>
        </table>
      </div>`;
  };

  // rows selected as the Performance table's are, in the accent: a click selects one alone (again clears it), ⌘-click
  // adds or drops one, ⇧-click the run from the last one clicked; Engine Gaps selects its rows the same way
  Pie.pickRows = (root) => {
    let anchor = null;
    root.addEventListener("mousedown", (event) => { if (event.shiftKey && event.target.closest("tr[data-pick]")) event.preventDefault(); });
    root.addEventListener("click", (event) => {
      const tr = event.target.closest("tr[data-pick]");
      if (!tr || event.target.closest("a, button, input, select")) return;
      const rows = [...root.querySelectorAll("tr[data-pick]")], at = rows.indexOf(tr);
      const set = (row, on) => { row.classList.toggle("is-picked", on); row.setAttribute("aria-selected", on); };
      if (event.shiftKey && anchor !== null) {
        if (!event.metaKey && !event.ctrlKey) rows.forEach((row) => set(row, false));
        rows.slice(Math.min(anchor, at), Math.max(anchor, at) + 1).forEach((row) => set(row, true));
        return;
      }
      if (event.metaKey || event.ctrlKey) set(tr, !tr.classList.contains("is-picked"));
      else {
        const only = tr.classList.contains("is-picked") && rows.filter((row) => row.classList.contains("is-picked")).length === 1;
        rows.forEach((row) => set(row, false));
        if (!only) set(tr, true);
      }
      anchor = at;
    });
  };
  Pie.pickRows(element);

  let shown = "";  // how many rows the table holds, said under the window's title
  const draw = () => {
    if (element.hidden) return;
    // no title: the table fills the page as Performance's does, the toolbar naming the page
    element.innerHTML = list();
    if (Pie.toolbar?.elements?.subtitle) Pie.toolbar.elements.subtitle.textContent = shown;
  };

  const load = async () => {
    try {
      const client = await Pie.account.client();
      const { data, error } = await client.from(TABLE).select("*").order("created_at", { ascending: false }).limit(500);
      if (error) throw error;
      reports = data;
      // the outliers maintainers closed; a table not set up yet leaves every outlier open
      const { data: states } = await client.from("outlier_status").select("key,status");
      closedOutliers = new Set((states || []).filter((x) => x.status === "closed").map((x) => x.key));
      open = data.filter((r) => r.status === "open").length;
      showCount();
      const user = Pie.account.user();
      maintainer = false;
      if (user) {
        const { data: me } = await client.from("maintainers").select("user_id").eq("user_id", user.id).maybeSingle();
        maintainer = Boolean(me);
      }
    } catch {
      reports = "Reports could not be loaded";
    }
    draw();
  };

  // a maintainer's save: a pull request attached closes the report as fixed
  element.addEventListener("submit", async (event) => {
    event.preventDefault();
    const target = event.target;
    if (!target.classList.contains("reports-fix")) return;
    const data = Object.fromEntries(new FormData(target));
    const client = await Pie.account.client();
    const id = Number(target.closest("[data-id]").dataset.id);
    const status = data.fix_url && data.status === "open" ? "fixed" : data.status;
    const { error } = await client.from(TABLE).update({ fix_url: data.fix_url || null, status }).eq("id", id);
    if (!error) await load();
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

  // a better result, sent by an engine's team: what it is, the number, and how to reproduce it; it is kept as a
  // submission and published only once rerun on the project's own machines
  const pickerOf = (name, table, label, chosen) => `<select name="${name}" aria-label="${label}" required><option value="">${label}</option>${(Pie.store.rows(table) || [])
    .map((r) => `<option value="${esc(r.id)}"${r.id === chosen ? " selected" : ""}>${esc(r.name || r.label || r.id)}</option>`).join("")}</select>`;
  const submitSheet = document.createElement("dialog");
  submitSheet.className = "reports-sheet";
  document.body.append(submitSheet);
  let submitSource = "results", submitDone = null;
  submitSheet.addEventListener("click", (event) => {
    if (event.target.closest("[data-sheet-cancel]") || event.target === submitSheet) submitSheet.close();
  });
  submitSheet.addEventListener("submit", async (event) => {
    event.preventDefault();
    const data = Object.fromEntries(new FormData(event.target));
    const status = submitSheet.querySelector(".reports-status");
    const send = submitSheet.querySelector(".reports-send");
    send.disabled = true;
    const user = Pie.account.user();
    try {
      const client = await Pie.account.client();
      const { error } = await client.from(TABLE).insert({
        kind: "result", source: submitSource,
        hardware: data.hardware, engine: data.engine, model: data.model, workload: data.workload,
        value: data.value.trim(), version: data.version.trim(), config: data.config.trim(), link: data.link.trim() || null,
        note: `Submitted result: ${data.value.trim()}${data.version.trim() ? ` on ${data.version.trim()}` : ""}`,
        reporter: user?.user_metadata?.full_name || user?.email?.split("@")[0] || data.reporter?.trim() || null,
      });
      if (error) throw error;
      submitSheet.close();
      submitDone?.();
      reports = null;
    } catch {
      status.textContent = "Couldn’t submit the result. Please try again.";
      status.hidden = false;
      send.disabled = false;
    }
  });

  document.addEventListener("click", (event) => {
    const clear = event.target.closest("[data-reports-unfocus]");
    if (clear) { focused = null; clear.closest(".filter")?.remove(); draw(); return; }
    const button = event.target.closest("[data-reports-pick]");
    if (!button) return;
    event.stopPropagation();
    Pie.popover.open(button, `reports:${button.dataset.reportsPick}`, null);
  }, true);

  // signing in or out redraws the form and the maintainer's fields
  document.addEventListener("pie:account", () => { if (!element.hidden) load(); });

  Pie.reports = {
    element,
    // the bar's Type filter, as the tables' filters read: its name, or the type picked, in the accent
    focus(hardware, model, setup) { focused = { hardware, model, setup: setup || null }; if (!element.hidden) draw(); },
    bar() {
      const chip = focused ? `<span class="filter is-set"><button class="filter-button" type="button" data-reports-unfocus title="Show every report">${esc([nameOf("hardware", focused.hardware), nameOf("models", focused.model), focused.setup && { decode: "Single Decode", prefill: "Single Prefill", batching: "Batched Decode", pbatch: "Batched Prefill" }[focused.setup]].filter(Boolean).join(" · "))}<svg class="popup-chevron" viewBox="0 0 10 10" aria-hidden="true"><path d="M2.5 2.5l5 5M7.5 2.5l-5 5"/></svg></button></span>` : "";
      const chevron = '<svg class="popup-chevron" viewBox="0 0 10 14" aria-hidden="true"><path d="M2 5l3-3 3 3M2 9l3 3 3-3"/></svg>';
      return chip + `<span class="filter${typeFilter ? " is-set" : ""}"><button class="filter-button" type="button" data-reports-pick="type" aria-haspopup="menu">${typeFilter ? esc(TYPES[typeFilter].label) : "Type"}${chevron}</button></span>`;
    },
    menu(k) {
      if (k.startsWith("status:")) {
        const closed = closedOutliers.has(k.slice(7));
        return [{ value: "open", label: "Open", selected: !closed, icon: statusTag("open").replace(/>[^<]*</, "><") },
          { value: "closed", label: "Closed", selected: closed, icon: statusTag("fixed").replace(/>[^<]*</, "><") }];
      }
      if (k !== "type") return [];
      return [{ value: "", label: "All Types", selected: !typeFilter },
        ...Object.entries(TYPES).map(([id, t]) => ({ value: id, label: t.label, selected: id === typeFilter, icon: `<span class="cell-dot" style="--dot: ${t.color}"></span>` }))];
    },
    pick(k, value) {
      if (k.startsWith("status:")) { setStatus(k.slice(7), value === "closed"); return; }
      if (k !== "type") return;
      typeFilter = TYPES[value] ? value : "";
      try { localStorage.setItem("pieReportsType", typeFilter); } catch { /* private windows can refuse storage */ }
      draw();
    },
    // the sheet for a submitted result, filled from one selected row of the Performance or Quality table if given
    submit(row, source, done) {
      if (!Pie.account?.configured) return;  // for now open to anyone, signed in or not (supabase/measurement_reports.sql)
      submitSource = source || "results";
      submitDone = done;
      const quality = submitSource === "quality";
      submitSheet.innerHTML = `
        <form method="dialog" class="account-sheet reports-sheet-form">
          <h2 class="account-title">Submit a result</h2>
          <p class="account-sub">We rerun it on our machines before it appears on the site.</p>
          <div class="account-email">
            ${pickerOf("engine", "engines", "Engine", row?.engine)}
            ${pickerOf("model", "models", "Model", row?.model)}
            ${pickerOf("hardware", "hardware", "Machine", row?.hardware)}
            ${quality ? `<input name="workload" aria-label="Task" required maxlength="60" placeholder="Task (for example gsm8k)" value="${esc(row?.task || "")}">` : pickerOf("workload", "workloads", "Workload", row?.workload)}
            <input name="value" aria-label="Your result" required maxlength="60" placeholder="${quality ? "Your score (for example 81.2)" : "Your result (for example 512 tok/s)"}">
            <input name="version" aria-label="Engine version" required maxlength="200" placeholder="Engine version or commit">
            <textarea name="config" aria-label="How to reproduce it" required minlength="10" maxlength="8000" rows="3" placeholder="The exact command and settings"></textarea>
            <input name="link" type="url" aria-label="Logs" maxlength="500" pattern="https://.+" placeholder="Logs or reproduction link (optional)">
            ${Pie.signedIn() ? "" : `<input name="reporter" aria-label="Contact" maxlength="120" autocomplete="email" placeholder="Name or email (optional)">`}
          </div>
          <p class="account-note is-error reports-status" role="status" hidden></p>
          <button type="submit" class="account-primary reports-send">Submit</button>
          <button type="button" class="account-cancel" data-sheet-cancel>Cancel</button>
        </form>`;
      submitSheet.showModal();
      submitSheet.querySelector(row ? "[name=value]" : "select")?.focus();
    },
    open: () => openCount(),
    shown: () => shown,  // the open reports, filed and found, for the sidebar
    // open the sheet for the selected rows of the Performance (results) or Quality table, once signed in;
    // `sent` runs once the reports are filed (the table clears its selection); `numbers` are the rows' numbers in the table
    flag(rows, source, sent, numbers) {
      if (!rows.length) return;
      // a report is a GitHub issue on the open benchmarks repo, written out from the picked measurements: no account here
      const name = (t, id) => nameOf(t, id);
      const lines = rows.map((row) => `| ${name("engines", row.engine)} | ${name("models", row.model)} | ${name("hardware", row.hardware || row.platform)} | ${source === "quality" ? row.task : name("workloads", row.workload)} | ${valueOf(row, source) || "—"} |`);
      const body = `<!-- What looks off in these measurements? -->\n\n\n| Engine | Model | Machine | ${source === "quality" ? "Task" : "Workload"} | Value |\n|---|---|---|---|---|\n${lines.join("\n")}\n`;
      window.open(`https://github.com/pie-project/benchmarks/issues/new?body=${encodeURIComponent(body)}&labels=report`, "_blank", "noopener");
      sent?.();
      return;
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
