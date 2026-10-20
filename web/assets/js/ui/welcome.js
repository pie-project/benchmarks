window.Pie = window.Pie || {};

(() => {
  const element = document.getElementById("welcome");

  // each row's second line says what is measured there: the stack, then how many machines the data holds
  const STACK = { mac: "Metal", nvidia: "CUDA", tpu: "XLA", amd: "ROCm", cerebras: "Wafer-scale", android: "Vulkan", web: "In the browser" };
  const detailOf = (id, platform) => {
    const n = SOON.has(id) || !Pie.platform?.machines ? 0 : Pie.platform.machines(platform);
    return [STACK[id], n ? `${n} ${n === 1 ? "machine" : "machines"}` : ""].filter(Boolean).join(" · ");
  };
  const platforms = () => Object.entries(Pie.schema).filter(([, s]) => s.view === "platform" && s.platform);
  // the platforms not yet running in CI; every other one has numbers, though a local checkout may not hold them
  const SOON = new Set(["android", "web"]);
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

  // every platform as a row of the site's data table, as Results and Quality list theirs: the platform with its mark,
  // its stack, how many machines ran there and so whether it is measured (any machine in the data); every row opens its platform's page
  // a header sorts its column, a second click reverses it and a third clears it, back to the sidebar's order
  let sort = null;
  const COLUMNS = [
    { key: "label", label: "Platform" },
    { key: "stack", label: "Stack" },
    { key: "machines", label: "Machines", numeric: true },
    { key: "status", label: "Status" },
  ];
  const table = () => {
    let list = platforms().map(([id, s], order) => {
      const machines = Pie.platform?.machines ? Pie.platform.machines(s.platform) : 0;
      return { id, s, order, label: s.label, stack: STACK[id] || "", machines, status: machines ? "Measured" : "Not measured" };
    });
    if (sort) {
      list = [...list].sort((a, b) => {
        const x = a[sort.key], y = b[sort.key];
        return (typeof x === "number" ? x - y : String(x).localeCompare(String(y))) * sort.direction || a.order - b.order;
      });
    }
    const rows = list.map(({ id, s, stack, machines: n, status }) => `<tr class="is-link" data-go="${id}">
        <td><span class="welcome-cell"><span class="sidebar-glyph" style="--tint: ${s.tint}">${Pie.icon(id)}</span>${s.label}</span></td>
        <td class="welcome-stack">${stack}</td>
        <td class="is-numeric${n ? "" : " is-empty"}">${n || "–"}</td>
        <td${n ? "" : ' class="is-empty"'}>${status}</td>
        <td class="welcome-go">${CHEVRON}</td>
      </tr>`).join("");
    const head = COLUMNS.map((c) => `<th${c.numeric ? ' class="is-numeric"' : ""} data-sort="${c.key}">${c.label}${sort?.key === c.key ? `<span class="column-sort">${sort.direction > 0 ? "↑" : "↓"}</span>` : ""}</th>`).join("");
    return `<table class="data-table welcome-table">
      <thead><tr>${head}<th class="welcome-go"></th></tr></thead>
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
    <!-- Inferlets, hidden for now
    <header class="method-head welcome-intro is-second">
      <div>
        <span class="welcome-icon is-inferlets" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M12 3 4 7.5v9L12 21l8-4.5v-9L12 3z"/><path d="M4 7.5 12 12l8-4.5M12 12v9"/></svg></span>
        <p class="welcome-eyebrow">Alpha</p>
        <h1>Inferlets</h1>
        <p class="welcome-tagline">Think like a human.</p>
        <p class="method-lede">Precise control over memory and the inference loop. Let your model draft, branch and rethink, just like you do.</p>
      </div>
      <button class="welcome-cta is-secondary" type="button" data-go="inferlets">Try It Now<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M6 3.5 10.5 8 6 12.5"/></svg></button>
    </header>
    -->
    <!-- Liszt Services, hidden for now
    <header class="method-head welcome-intro is-second">
      <div>
        <span class="welcome-icon is-services" aria-hidden="true"><svg viewBox="0 0 24 24">${Pie.icons.services}</svg></span>
        <p class="welcome-eyebrow">Alpha</p>
        <h1>Liszt Services</h1>
        <p class="welcome-tagline">Your hardware, at its limit.</p>
        <p class="method-lede">Liszt manages both the hardware and the thinking in agentic workloads, on an efficient runtime from a single Mac to a GPU cluster.</p>
      </div>
      <button class="welcome-cta is-secondary" type="button" data-go="services">Learn More<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M6 3.5 10.5 8 6 12.5"/></svg></button>
    </header>
    -->
    <!-- the Profiler, hidden for now
    <header class="method-head welcome-intro is-second">
      <div>
        <span class="welcome-icon is-profiler" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M3 12h4l2.5-6 5 12 2.5-6h4"/></svg></span>
        <p class="welcome-eyebrow">Alpha</p>
        <h1>Profiler</h1>
        <p class="welcome-tagline">See where the time goes.</p>
        <p class="method-lede">Every agent, every tool call, every idle moment, on one timeline. Find the gaps and give your hardware its time back.</p>
      </div>
      <button class="welcome-cta is-secondary" type="button" data-go="profiler">Start Profiling<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M6 3.5 10.5 8 6 12.5"/></svg></button>
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

  Pie.welcome = {
    element,
    render(state) {
      element.hidden = state.table !== "welcome";
      if (!element.hidden && element.dataset.ready !== "1") {
        element.innerHTML = table();
        element.addEventListener("click", (event) => {
          const header = event.target.closest("[data-sort]");
          if (header) {
            const key = header.dataset.sort;
            // a third click clears the sort, back to the sidebar's order
            const first = key === "machines" ? -1 : 1;
            sort = sort?.key !== key ? { key, direction: first } : sort.direction === first ? { key, direction: -first } : null;
            element.innerHTML = table();
            return;
          }
          // a row opens its platform, as its sidebar item does
          const row = event.target.closest("[data-go]");
          if (row) document.querySelector(`.sidebar-item[data-table="${row.dataset.go}"]`)?.click();
        });
        element.dataset.ready = "1";
      }
    },
  };
})();
