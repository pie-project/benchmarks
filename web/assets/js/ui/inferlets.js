window.Pie = window.Pie || {};

// Inferlets: a headline that says what they are, then a terminal that runs one in the tab.
// The terminal boots pie on WebGPU (assets/pie-web) on the first click and runs the
// prefill-while-typing inferlet: while the visitor types, the stable part of the message is
// prefilled; on Enter only the last few tokens remain, so the first token comes back fast.
(() => {
  const element = document.getElementById("inferlets");

  const PIE = "assets/pie-web/";
  const INFERLET = PIE + "prefill_while_typing.wasm";
  // The weights are not in this repository; the tab fetches them once (by range) and keeps
  // them in the origin's private file system. `?model=` points at another artifact.
  const MODEL = "https://huggingface.co/antonmeln/qwen-3.5-0.8b-wgpu/resolve/main/qwen--qwen3-5-0-8b.qwen35-d0-8b-u4g64-kv-bf16.wgpu.zt";
  // `?mode=plain` prefills the whole message at Enter instead, for comparison.
  const MODE = new URLSearchParams(location.search).get("mode") === "plain" ? "plain" : "typeahead";
  const CONFIG = 'max_forward_tokens = 512\nmax_forward_requests = 4\nmax_state_slots = 4\nmax_model_len = 4608\ndevice_kv_budget = "256MiB"\n';

  const content = `
    <header class="inf-hero">
      <h1 class="inf-title">Absolute hardware control.</h1>
      <p class="inf-label">The most humane intelligence ever.</p>
      <p class="inf-text">Inferlets are programmable OS processes that manage how a model thinks, as it runs. The most granular control over your tokens in the world.</p>
    </header>
    <!-- the live demo window, hidden for now
    <section class="store-shelf">
      <div class="term is-live" id="tw">
        <div class="term-bar">
          <span class="term-lights" aria-hidden="true"><i></i><i></i><i></i></span>
          <span class="term-status"><span class="term-ttft" id="tw-ttft" hidden></span><span class="term-gpu" id="tw-gpu" hidden></span></span>
        </div>
        <div class="term-body" id="tw-body">
          <div class="term-cover" id="tw-hint">
            <span class="term-cover-cta">Start the demo<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="10"/><path d="M10 8.5v7l6-3.5z"/></svg></span>
          </div>
          <div class="term-line" id="tw-line" hidden><span class="term-prompt">›</span><input id="tw-input" type="text" autocomplete="off" autocorrect="off" autocapitalize="off" spellcheck="false" aria-label="Message"></div>
        </div>
      </div>
    </section>
    -->`;

  // The GPU, named on page load without the engine: WebGPU says whether there is one,
  // WebGL's unmasked renderer usually says which ("ANGLE (Apple, ANGLE Metal Renderer:
  // Apple M5 Max, Unspecified Version)" → "Apple M5 Max").
  function gpuName(info) {
    try {
      const gl = document.createElement("canvas").getContext("webgl");
      const ext = gl?.getExtension("WEBGL_debug_renderer_info");
      let name = ext ? String(gl.getParameter(ext.UNMASKED_RENDERER_WEBGL) || "") : "";
      gl?.getExtension("WEBGL_lose_context")?.loseContext();
      const angle = name.match(/^ANGLE \((.*)\)$/);
      if (angle) name = angle[1].split(/,\s*/)[1] ?? "";
      name = name
        .replace(/^ANGLE [\w ]*Renderer:\s*/, "")
        .replace(/\s*\(0x[0-9a-f]+\).*$/i, "")
        .replace(/\s*Direct3D.*$/i, "")
        .replace(/\s*(\(TM\)|\(R\))/gi, "")
        .trim();
      if (name) return name;
    } catch {}
    return info?.description || "";
  }

  async function detectGpu(el) {
    let adapter = null;
    try {
      adapter = navigator.gpu ? await navigator.gpu.requestAdapter() : null;
    } catch {}
    if (!adapter) {
      el.className = "term-gpu is-none";
      el.textContent = "No WebGPU";
    } else {
      const name = gpuName(adapter.info);
      el.className = "term-gpu";
      el.textContent = name || "GPU detected";
      el.title = el.textContent;
    }
    el.hidden = false;
  }

  function demo(root) {
    const $ = (id) => root.querySelector("#" + id);
    const body = $("tw-body"), line = $("tw-line"), input = $("tw-input"), hint = $("tw-hint"), badge = $("tw-ttft");
    let phase = "idle"; // idle → booting → ready → answering
    let proc = null;
    let sentText = null, timer = 0;
    let answer = null, enterAt = 0, firstAt = 0, shown = "";

    const say = (text, cls = "is-dim") => {
      const div = document.createElement("div");
      div.className = "term-out " + cls;
      div.textContent = text;
      body.insertBefore(div, line);
      body.scrollTop = body.scrollHeight;
      return div;
    };
    const send = (msg) => proc.signal(JSON.stringify(msg));

    // The answer is Markdown: draw its bold, italics, code, headings and lists the way a rich terminal does.
    const esc = (t) => t.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    const inline = (t) => esc(t)
      .replace(/`([^`]+)`/g, "<code>$1</code>")
      .replace(/\*\*([^*]+)\*\*/g, "<b>$1</b>")
      .replace(/__([^_]+)__/g, "<b>$1</b>")
      .replace(/(^|[^*\w])\*([^*\s][^*]*?)\*(?!\w)/g, "$1<i>$2</i>")
      .replace(/(^|[^_\w])_([^_\s][^_]*?)_(?!\w)/g, "$1<i>$2</i>");
    const markdown = (text) => {
      let fenced = false;
      return text.split("\n").map((row) => {
        if (/^\s*```/.test(row)) { fenced = !fenced; return ""; }
        if (fenced) return `<span class="md-code">${esc(row)}</span>`;
        let m;
        if ((m = row.match(/^\s{0,3}#{1,6}\s+(.*)$/))) return `<b class="md-h">${inline(m[1])}</b>`;
        if ((m = row.match(/^(\s*)[*+-]\s+(.*)$/))) return `${m[1]}<span class="md-bullet">•</span> ${inline(m[2])}`;
        if ((m = row.match(/^(\s*)(\d+[.)])\s+(.*)$/))) return `${m[1]}<span class="md-bullet">${m[2]}</span> ${inline(m[3])}`;
        if (/^\s*([-*_])\s*\1\s*\1[\s\1]*$/.test(row)) return `<span class="md-rule">${"─".repeat(24)}</span>`;
        return inline(row);
      }).join("\n");
    };
    // a small model can loop: a paragraph that repeats the one before it is shown once
    const unloop = (text) => text.split(/\n{2,}/).filter((block, i, all) => i === 0 || block.trim() !== all[i - 1].trim()).join("\n\n");
    // "TTFT 44 ms" is drawn as a grey label and a white figure, as macOS shows a reading in a title bar
    const showBadge = (text, title) => {
      const m = text.match(/^TTFT\s+(.*)$/);
      badge.innerHTML = m ? `<span class="term-ttft-label">TTFT</span><span class="term-ttft-value">${m[1]}</span>` : text;
      badge.title = title || "";
      badge.hidden = false;
    };

    async function boot() {
      phase = "booting";
      hint.remove();
      say("Pie runs Qwen3.5 0.8B on your GPU, in this tab.");
      if (!navigator.gpu || typeof WebAssembly.Suspending !== "function") {
        say("This demo needs a browser with WebGPU (a recent Chrome or Edge).");
        return;
      }
      const status = say("Starting Pie…");
      try {
        const adapter = await navigator.gpu.requestAdapter();
        if (!adapter) throw new Error("This demo needs a browser with WebGPU (no GPU adapter is available).");
        // ?model= picks another of the site's own models; a link elsewhere is ignored, so no shared link can make the demo run someone else's weights
        const asked = (() => { try { return new URL(new URLSearchParams(location.search).get("model") || MODEL, document.baseURI); } catch { return null; } })();
        const model = (asked && asked.origin === location.origin ? asked : new URL(MODEL, document.baseURI)).href;
        const head = await fetch(model, { method: "HEAD" }).catch(() => null);
        if (!head?.ok) {
          status.textContent = "The model for this demo is not available right now. Try again later.";
          phase = "idle";
          return;
        }
        const pie = await import(new URL(PIE + "pie.mjs", document.baseURI).href);
        await pie.load();
        let from = "network";
        await pie.bootLazy(model, CONFIG, (got, total, src) => {
          from = src;
          const pct = total ? Math.min(100, Math.floor((got / total) * 100)) : 0;
          status.textContent = `${src === "cache" ? "Loading" : "Downloading"} Qwen3.5 0.8B (${(total / 1048576).toFixed(0)} MB, once)… ${pct}%`;
        });
        status.textContent = "Compiling the inferlet…";
        const bytes = new Uint8Array(await (await fetch(INFERLET)).arrayBuffer());
        const program = await pie.install(bytes, "prefill-while-typing.wasm");
        const client = await pie.connect();
        proc = await client.launchProcess(program, {});
        pump();
        status.textContent = `Ready${from === "cache" ? "" : " (the model is cached for your next visit)"}. Type a message and press Enter.`;
        phase = "ready";
        line.hidden = false;
        input.focus();
      } catch (e) {
        status.className = "term-out is-error";
        status.textContent = String(e?.message ?? e);
        phase = "idle";
      }
    }

    async function pump() {
      for (;;) {
        const { event, value } = await proc.recv();
        if (event === "return" || event === "error") {
          if (event === "error") say(String(value), "is-error");
          line.hidden = true;
          return;
        }
        if (event !== "message") continue;
        let m;
        try { m = JSON.parse(value); } catch { continue; }
        if (m.ev === "tok" && answer) {
          if (!firstAt) {
            firstAt = performance.now();
            showBadge(`TTFT ${Math.round(firstAt - enterAt)} ms`);
          }
          shown = m.reset ? m.t : shown + m.t;
          answer.innerHTML = markdown(unloop(shown.replace(/<\|[^|]*\|>/g, "").trimEnd()));
          body.scrollTop = body.scrollHeight;
        } else if (m.ev === "done") {
          showBadge(
            `TTFT ${Math.round(firstAt ? firstAt - enterAt : m.ttft_ms)} ms`,
            `${m.prefilled_while_typing} of ${m.prompt_tokens} prompt tokens were prefilled while you typed; ` +
              `${m.prefilled_at_enter} were left for Enter (${m.prefill_ms.toFixed(0)} ms of prefill).`,
          );
          finish();
        } else if (m.ev === "error") {
          say(m.why, "is-error");
          finish();
        }
      }
    }

    function finish() {
      answer = null;
      phase = "ready";
      sentText = null;
      line.hidden = false;
      input.disabled = false;
      input.focus();
      body.scrollTop = body.scrollHeight;
    }

    // While typing: a word boundary sends the text at once, otherwise after 150 ms idle.
    function typed() {
      if (phase !== "ready") return;
      clearTimeout(timer);
      const text = input.value;
      const flush = () => {
        if (phase !== "ready" || MODE === "plain" || input.value === sentText || !input.value.trim()) return;
        sentText = input.value;
        send({ op: "text", text: sentText });
      };
      if (/[\s.,;:!?]$/.test(text)) flush();
      else timer = setTimeout(flush, 150);
    }

    function enter() {
      const text = input.value.trim();
      if (phase !== "ready" || !text) return;
      clearTimeout(timer);
      phase = "answering";
      say("› " + text, "is-echo");
      input.value = "";
      input.disabled = true;
      line.hidden = true;
      answer = say("", "is-answer");
      shown = "";
      firstAt = 0;
      enterAt = performance.now();
      send({ op: "enter", text, mode: MODE });
    }

    root.addEventListener("click", () => {
      if (phase === "idle") boot();
      else if (!line.hidden) input.focus();
    });
    input.addEventListener("input", typed);
    input.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.isComposing) {
        e.preventDefault();
        enter();
      }
    });
  }

  Pie.inferlets = {
    element,
    render(state) {
      element.hidden = state.table !== "inferlets";
      if (element.hidden || element.dataset.ready === "1") return;
      element.innerHTML = `<div class="method-inner">${content}</div>`;
      element.dataset.ready = "1";
      // the demo window is commented out above: start it only when it is on the page
      const tw = element.querySelector("#tw");
      if (tw) {
        demo(tw);
        detectGpu(element.querySelector("#tw-gpu"));
      }
    },
  };
})();
