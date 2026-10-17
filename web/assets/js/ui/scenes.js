window.Pie = window.Pie || {};

// The Methods chapters' animations, as Apple explains a chip: one moving picture that is the explanation, and one
// caption that says what is happening as it happens. The picture is a timeline. Each lane is one thing the chip does,
// drawn to scale on one time axis; lanes that run together start together, so the longer one visibly sets the pace.
// Words appear when a step ends. The layout never moves: the words and the result have their place from the start,
// the result dimmed until the animation reaches it. A scene plays once when it scrolls into view and holds its last
// frame; the corner button plays it again. With reduced motion it shows the last frame at once.
(() => {
  const esc = (text) => Pie.format.escape(text);
  const num = (n) => (n >= 100 ? Math.round(n).toLocaleString("en-US") : n >= 10 ? n.toFixed(0) : n.toFixed(1));
  const ms = (s) => `${(s * 1e3).toFixed(s * 1e3 >= 10 ? 0 : 2)} ms`;
  const reduced = () => window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const STEP_MS = 1800;  // how long one step of the timeline takes to watch, whatever its real length

  // a lane: its label, where its bar starts and how long it runs, in seconds, and its colour
  const lane = (key, label, start, length, tone) => ({ key, label, start, length, tone });

  // the machine and model are named once, in the calculation under the animation, so the scene does not repeat them
  const figure = (id, head, lanes, words, result) => {
    const total = Math.max(...lanes.map((l) => l.start + l.length));
    const rows = lanes.map((l) => `
      <div class="sc-lane" data-lane="${l.key}">
        <span class="sc-lane-label">${esc(l.label)}</span>
        <span class="sc-track"><span class="sc-seg is-${l.tone}" style="left: ${(l.start / total) * 100}%; width: ${(l.length / total) * 100}%; --delay: ${(l.start / total) * STEP_MS}ms; --dur: ${(l.length / total) * STEP_MS}ms"><i></i></span></span>
        <span class="sc-lane-value">${ms(l.length)}</span>
      </div>`).join("");
    return `
      <figure class="scene" data-scene="${id}" data-total="${total}">
        <div class="sc-card">
          <div class="sc-top"><p class="sc-head">${esc(head)}</p><button type="button" class="sc-replay" aria-label="Play again" title="Play again"><svg viewBox="0 0 16 16" aria-hidden="true"><path d="M3.5 8a4.5 4.5 0 1 0 1.4-3.3"/><path d="M4.5 2.2v2.7h2.7"/></svg></button></div>
          <div class="sc-timeline">
            <div class="sc-axis" aria-hidden="true"><span></span><span class="sc-axis-scale"><span>0</span><span>${ms(total)}</span></span><span></span></div>
            ${rows}
          </div>
          <div class="sc-words${words ? ` ${words}` : ""}" aria-hidden="true"></div>
          <p class="sc-caption" aria-live="polite"></p>
          <div class="sc-result"><b>${esc(result[0])}</b><span>${esc(result[1])}</span></div>
        </div>
      </figure>`;
  };

  // the steps a scene is made of; every wait checks the run is still current, so a replay or a page change stops it
  const steps = (root, run) => {
    const speed = reduced() ? 0 : 1;
    const live = () => run.id === root.__run && root.isConnected;
    const wait = (t) => new Promise((go, stop) => setTimeout(() => (live() ? go() : stop(new Error("stopped"))), t * speed));
    const $ = (sel) => root.querySelector(sel);
    const $$ = (sel) => [...root.querySelectorAll(sel)];
    return {
      speed,
      wait,
      $,
      $$,
      // one step of the timeline: every lane fills its own stretch, at one pace, and the step ends with the last
      async lanes(pace = 1) {
        const segs = $$(".sc-seg");
        segs.forEach((seg) => {
          seg.style.setProperty("--pace", String(pace * speed));
          seg.classList.remove("is-on");
        });
        void root.offsetWidth;
        segs.forEach((seg) => seg.classList.add("is-on"));
        $$(".sc-lane").forEach((l) => l.classList.add("is-shown"));
        await wait(STEP_MS * pace);
      },
      // wait until a lane has finished within the step
      at(key, pace = 1) {
        const seg = $(`[data-lane="${key}"] .sc-seg`);
        const end = (parseFloat(seg.style.getPropertyValue("--delay")) + parseFloat(seg.style.getPropertyValue("--dur"))) * pace;
        return end;
      },
      clear() {
        $$(".sc-seg").forEach((seg) => {
          seg.classList.add("is-reset");
          seg.classList.remove("is-on");
          void seg.offsetWidth;
          seg.classList.remove("is-reset");
        });
      },
      say(text) {
        const p = $(".sc-caption");
        p.classList.remove("is-in");
        void p.offsetWidth;
        p.textContent = text;
        p.classList.add("is-in");
      },
      word(text, cls = "") {
        const w = document.createElement("span");
        w.className = `sc-word ${cls}`;
        w.textContent = text;
        $(".sc-words").append(w);
        void w.offsetWidth;
        w.classList.add("is-in");
        return w;
      },
      finish(text) {
        if (text) this.say(text);
        $(".sc-result").classList.add("is-in");
      },
      reset() {
        $(".sc-words").replaceChildren();
        $(".sc-caption").textContent = "";
        $(".sc-result").classList.remove("is-in");
        this.clear();
      },
    };
  };

  // run a step, saying one thing when a given lane ends and another when the step does
  const step = async (s, pace, events) => {
    const done = s.lanes(pace);
    let elapsed = 0;
    for (const [t, act] of events.sort((x, y) => x[0] - y[0])) {
      await s.wait(Math.max(0, t - elapsed));
      elapsed = t;
      act();
    }
    await done;
  };

  const SCENES = {
    decode: {
      html: (d) => figure("decode", "Every word reads the whole model.",
        [lane("read", "Reading", 0, d.read, "read"), lane("compute", "Computing", 0, d.compute, "compute")],
        "",
        [`${num(d.tps)} words a second`, "at most: reading sets the pace"],
        `Qwen3.5-4B on ${d.machine}, 4-bit weights: ${d.weightsGB} GB read at ${d.bw} GB/s for every word.`),
      async play(s, d) {
        const words = ["The", "model", "writes"];
        for (let i = 0; i < words.length; i += 1) {
          const pace = i ? 0.6 : 1;
          if (i) s.clear();
          s.say(i ? "And again for the next word: the whole model is read once more." : `Reading all ${d.weightsGB} GB of weights, and computing with them as they arrive.`);
          await step(s, pace, [
            [s.at("compute", pace), () => { if (!i) s.say(`The arithmetic is done in ${ms(d.compute)}. Now the chip waits for memory.`); }],
          ]);
          s.word(words[i]);
          await s.wait(i ? 250 : 500);
        }
        s.finish(`Reading takes ${ms(d.read)} a word, computing ${ms(d.compute)}. Reading sets the pace.`);
      },
    },

    speculation: {
      html: (d) => figure("speculation", "One read checks several guesses.",
        [lane("draft", "Drafting", 0, d.draft, "draft"), lane("read", "Reading", d.draft, d.read, "read"), lane("compute", "Computing", d.draft, d.computeK, "compute")],
        "is-draft",
        [`${d.kept.toFixed(1)} words a read`, `on average, with ${d.k} guesses each accepted ${Math.round(d.a * 100)}% of the time`],
        `A ${d.drafter} B-parameter drafter on ${d.machine}; the model is Qwen3.5-4B, 4-bit.`),
      async play(s, d) {
        const guesses = ["reads", "itself", "once", "per"];
        const drafts = [];
        s.say(`A small drafter quickly guesses the next ${d.k} words.`);
        const draftEnd = s.at("draft");
        await step(s, 1, [
          ...guesses.map((g, i) => [((i + 1) / guesses.length) * draftEnd * 0.95, () => drafts.push(s.word(g, "is-ghost"))]),
          [draftEnd, () => s.say(`Then the model reads its weights once and checks all ${d.k} guesses together.`)],
        ]);
        s.say("It keeps every guess up to the first wrong one, and adds one word of its own.");
        for (let i = 0; i < drafts.length; i += 1) {
          await s.wait(260);
          drafts[i].classList.remove("is-ghost");
          drafts[i].classList.add(i < 3 ? "is-kept" : "is-wrong");
        }
        await s.wait(300);
        s.word("for", "is-kept is-bonus");
        await s.wait(500);
        s.finish(`Four words from one read, where plain decoding gets one. On average ${d.kept.toFixed(1)}.`);
      },
    },

    batching: {
      html: (d) => figure("batching", "One read serves every request.",
        [lane("read", "Reading", 0, d.read, "read"), lane("compute", "Computing", 0, d.compute, "compute")],
        "is-batch",
        [`${num(d.tps)} words a second`, d.bound === "compute" ? "at most: with this many requests, computing sets the pace" : "at most: reading still sets the pace"],
        `${d.batch} requests of Qwen3.5-4B on ${d.machine}, 4-bit weights.`),
      async play(s, d) {
        s.say(`${d.batch} requests share one read of the weights.`);
        await step(s, 1, [
          [s.at("read"), () => s.say(`Reading is done in ${ms(d.read)}, but each request needs its own arithmetic: ${d.batch} words to compute.`)],
        ]);
        for (let i = 0; i < d.batch; i += 1) s.word("", "is-dot");
        await s.wait(600);
        s.finish(`${d.batch} words a step. Computing them takes ${ms(d.compute)}, longer than the read, so computing sets the pace.`);
      },
    },

    prefill: {
      html: (d) => figure("prefill", "The whole prompt goes through at once.",
        [lane("read", "Reading", 0, d.read, "read"), lane("compute", "Computing", 0, d.compute, "compute")],
        "is-batch",
        [`${num(d.tps)} words a second`, "at most: computing sets the pace"],
        `A ${d.tokens}-word prompt, Qwen3.5-4B on ${d.machine}, 4-bit weights.`),
      async play(s, d) {
        for (let i = 0; i < 64; i += 1) s.word("", "is-dot is-prompt");
        s.say(`All ${d.tokens} words of the prompt go in together and share one read of the weights.`);
        await step(s, 1, [
          [s.at("read"), () => s.say(`Reading is done in ${ms(d.read)}. The arithmetic for ${d.tokens} words takes much longer.`)],
        ]);
        await s.wait(300);
        s.finish(`Computing takes ${ms(d.compute)}, ${Math.round(d.compute / d.read)} times the read. Computing sets the pace.`);
      },
    },
  };

  Pie.scenes = {
    html: (id, data) => (SCENES[id] && data ? SCENES[id].html(data) : ""),
    // play when half of it is on screen, once; the corner button plays it again
    start(root, data) {
      const scene = SCENES[root.dataset.scene];
      if (!scene) return () => {};
      const run = async () => {
        root.__run = (root.__run || 0) + 1;
        const s = steps(root, { id: root.__run });
        s.reset();
        root.classList.add("is-playing");
        try {
          await scene.play(s, data);
        } catch {
          // stopped by a replay or by leaving the chapter
        }
        root.classList.remove("is-playing");
      };
      const watch = new IntersectionObserver(([entry]) => {
        if (!entry.isIntersecting) return;
        watch.disconnect();
        run();
      }, { threshold: 0.5 });
      watch.observe(root);
      root.querySelector(".sc-replay")?.addEventListener("click", run);
      return () => {
        watch.disconnect();
        root.__run = (root.__run || 0) + 1;
      };
    },
  };
})();
