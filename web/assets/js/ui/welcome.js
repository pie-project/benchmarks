window.Pie = window.Pie || {};

(() => {
  const element = document.getElementById("welcome");

  // each row's second line says what is measured there: the stack, then how many machines the data holds
  const STACK = { mac: "Metal", windows: "CUDA", nvidia: "CUDA", tpu: "XLA", amd: "ROCm", cerebras: "CSL", android: "Vulkan", web: "WebGPU" };
  const detailOf = (id, platform) => {
    const n = SOON.has(id) || !Pie.platform?.machines ? 0 : Pie.platform.machines(platform);
    return [STACK[id], n ? `${n} ${n === 1 ? "machine" : "machines"}` : ""].filter(Boolean).join(" · ");
  };
  const platforms = () => Object.entries(Pie.schema).filter(([, s]) => s.view === "platform" && s.platform).sort(([, a], [, b]) => Pie.byPlatformOrder(a, b));
  // the platforms not yet running in CI; every other one has numbers, though a local checkout may not hold them
  const SOON = new Set(["android", "web"].filter((id) => !(DB.hardware || []).some((hw) => Pie.platformOf(hw) === id)));
  const CHEVRON = '<svg class="welcome-chevron" viewBox="0 0 16 16" aria-hidden="true"><path d="M6 3.5 10.5 8 6 12.5"/></svg>';
  // a platform as a row of a grouped list, as macOS Settings sets them: its sidebar mark, its name, one line, and where it leads
  const tile = ([id, s]) => {
    const ready = !SOON.has(id);
    return `
      <${ready ? `button type="button" data-go="${id}"` : "div"} class="welcome-tile${ready ? "" : " is-soon"}">
        <span class="sidebar-glyph welcome-tile-icon" style="--tint: ${s.tint}">${Pie.icon(id)}</span>
        <span class="welcome-tile-copy">
          <span class="welcome-tile-name">${s.label}</span>
          <span class="welcome-tile-line">${detailOf(id, s.platform)}</span>
          
        </span>
        ${ready ? `<span class="welcome-tile-status">${CHEVRON}</span>` : '<span class="welcome-tile-status is-soon">Coming Soon</span>'}
      </${ready ? "button" : "div"}>`;
  };
  // one list, the live platforms first; the rest say so at their end, as a Settings row shows its value there
  const list = () => `
    <section class="welcome-group" aria-label="Platforms">
      <div class="welcome-platforms">${[...platforms().filter(([id]) => !SOON.has(id)), ...platforms().filter(([id]) => SOON.has(id))].map(tile).join("")}</div>
    </section>`;

  // every platform as a row of the site's list, in the sidebar's order: its mark and name, and how many machines ran
  // there as "42 items" in grey at the row's far end, as Finder states a folder's contents; a row opens its platform's page, as its sidebar item does
  // a header click sorts by its column and a second click reverses it, as every other table here sorts
  let sortKey = null;
  let sortDir = 1;
  const table = () => {
    const list = platforms().map(([id, s]) => ({ id, s, name: s.short, stack: STACK[id] || "", machines: Pie.platform?.machines ? Pie.platform.machines(s.platform) : 0 }));
    if (sortKey) list.sort((a, b) => sortDir * (typeof a[sortKey] === "number" ? a[sortKey] - b[sortKey] : String(a[sortKey]).localeCompare(String(b[sortKey]))));
    const arrow = (key) => (sortKey === key ? `<span class="column-sort">${sortDir > 0 ? "↑" : "↓"}</span>` : "");
    const rows = list.map(({ id, s, machines: n }, i) => `<tr class="is-link" data-go="${id}">
        <td class="row-number">${i + 1}</td>
        <td><span class="welcome-cell" title="${s.label}"><span class="sidebar-glyph" style="--tint: ${s.tint}">${Pie.icon(id)}</span>${s.short}</span></td>
        <td class="welcome-stack">${STACK[id] || ""}</td>
        <td class="welcome-fill"></td>
        <td class="welcome-count is-numeric">${n}</td>
      </tr>`).join("");
    return `<table class="data-table welcome-table">
      <thead><tr><th class="row-number" aria-label="Row"></th><th data-sort="name">Platform${arrow("name")}</th><th data-sort="stack">Stack${arrow("stack")}</th><th class="welcome-fill"></th><th class="is-numeric" data-sort="machines">Machines${arrow("machines")}</th></tr></thead>
      <tbody>${rows}</tbody>
    </table>`;
  };

  // the welcome before the table: a banner over a grouped list, kept for when the page grows an introduction again
  const content = () => `
    <div class="welcome-banner">
      <div class="welcome-banner-copy">
        <h2 class="welcome-banner-title">AI that runs everywhere.</h2>
        <p class="welcome-banner-sub">The operating system for your silicon.</p>
      </div>
      <!-- the banner's buttons, hidden for now: download and the repository belong on pie-project.org
      <div class="welcome-banner-actions">
        <a class="welcome-banner-link is-primary" href="https://pie-project.org" target="_blank" rel="noopener">Download</a>
        <a class="welcome-banner-link" href="https://github.com/pie-project/pie" target="_blank" rel="noopener">GitHub</a>
      </div>
      -->
    </div>
    ${list()}
    <!-- the benchmarks header, hidden for now: the platform tiles lead to the numbers
    <header class="method-head welcome-intro">
      <div>
        <span class="welcome-icon is-bench" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M5 19V11M10 19V6M15 19v-9M20 19V4"/></svg></span>
        <h1>LLM Inference Engine Benchmarks</h1>
        <p class="welcome-tagline">Performance without compromise.</p>
        <p class="method-lede">An independent benchmark platform for measuring inference performance across engines, models, and hardware.</p>
      </div>
      <button class="welcome-cta" type="button" data-go="mac">Compare Engines<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M6 3.5 10.5 8 6 12.5"/></svg></button>
    </header>
    -->
    <!-- hidden for now
    <header class="method-head welcome-trust">
      <h2>Message to a Reader</h2>
      <p class="method-lede">Every question you ask a cloud model leaves your hands. It travels to a data center you will never see, runs on hardware you do not control, and is kept under terms you did not write. Your drafts, your code, your health questions, your half-formed ideas, the most personal things you think, quietly become someone else’s data.</p>
      <p class="method-lede">It does not have to be this way. The computer on your desk is already powerful enough to run the models that matter, and your words never need to leave it. What has been missing is not the hardware but the software: an engine that makes local AI as fast and as effortless as the cloud, so that choosing privacy never means choosing less.</p>
      <p class="method-lede">That is why we built Pie, and why we measure it in the open against every engine we can. Intelligence should run where you live, answer only to you, and belong to everyone. This is our step toward that future.</p>
      <p class="welcome-sign">With love, the Pie team!</p>
    </header>
    <header class="method-head welcome-trust welcome-pie">
      <h2>Pie: Programmable Inference Engine</h2>
      <p class="method-lede">Most inference engines today grew one model and one feature at a time, and many have become hard to extend and harder to maintain. We built Pie to give the open-source community a cleaner foundation.</p>
      <p class="method-lede">Pie borrows its design from operating systems. It manages the hardware as precisely as a kernel manages memory and compute, and runs your programs on top of it as lightweight processes called inferlets. The result is an engine that is simple to build on, and fast and fluid for everyone who uses it.</p>
    </header>
    -->`;

  let open = null;
  Pie.welcome = {
    element,
    onOpen(handler) {
      open = handler;
    },
    render(state) {
      element.hidden = state.table !== "welcome";
      if (!element.hidden && element.dataset.ready !== "1") {
        // the catalog's empty bar over the table, as Engines and Workloads have one
        element.innerHTML = `<div class="filter-bar" aria-hidden="true"></div>${table()}`;
        element.addEventListener("click", (event) => {
          // a row opens Results with the Platform filter set to it, as a folder opens what it holds
          const head = event.target.closest("th[data-sort]");
          if (head) {
            const key = head.dataset.sort;
            // up, then down, then back to the sidebar's order
            if (sortKey !== key) { sortKey = key; sortDir = 1; }
            else if (sortDir > 0) sortDir = -1;
            else sortKey = null;
            element.querySelector(".welcome-table").outerHTML = table();
            return;
          }
          const row = event.target.closest("[data-go]");
          if (row) open?.(Pie.schema[row.dataset.go].short);
        });
        element.dataset.ready = "1";
      }
    },
  };
})();
