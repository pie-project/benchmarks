let pie = null;
let client = null;
let program = null;
let topkProgram = null;

export async function load(o) {
  pie = await import(new URL(o.pie_module, location.href).href);
  await pie.load({ worker: o.worker !== false, log: o.log });
  let last = 0;
  const summary = await pie.bootLazy(new URL(o.model_url, location.href).href, o.config || "", (got, total) => {
    const pct = total ? Math.floor((got / total) * 100) : 0;
    if (pct >= last + 10) { last = pct; console.log(`pie: weights ${pct}% of ${(total / 2 ** 30).toFixed(2)} GiB`); }
  });
  const bytes = new Uint8Array(await (await fetch(new URL(o.inferlet_url, location.href))).arrayBuffer());
  program = await pie.install(bytes, "text-completion-bench.wasm");
  if (o.topk_url) topkProgram = await pie.install(new Uint8Array(await (await fetch(new URL(o.topk_url, location.href))).arrayBuffer()), "first-token-topk.wasm");
  client = await pie.connect();
  return { pie_summary: summary };
}

export async function generate({ ids, prompt, max_tokens, temperature, top_p, seed, ignore_eos, return_text, topk, timing, onToken }) {
  if (topk) {
    const proc = await client.launchProcess(topkProgram, { prompt_tokens: ids, k: topk });
    for (;;) {
      const { event, value } = await proc.recv();
      if (event === "error") throw new Error(String(value));
      if (event === "return") { onToken(); return { prompt_tokens: ids.length, output_tokens: 1, topk: JSON.parse(value) }; }
    }
  }
  const input = {
    max_tokens, temperature: temperature ?? 0, top_p: top_p ?? 1, ignore_eos: ignore_eos !== false, return_text: !!return_text,
    report_timing: !!timing,
  };
  if (ids) input.prompt_tokens = ids; else input.prompt = prompt;
  if (seed != null) input.seed = seed;
  const proc = await client.launchProcess(program, input);
  let first = null;
  for (;;) {
    const { event, value } = await proc.recv();
    if (event === "message" && String(value) === "t0") { first = performance.now(); continue; }
    if (event === "error") throw new Error(String(value));
    if (event !== "return") continue;
    const end = performance.now();
    const out = JSON.parse(value);
    const n = Number(out.num_output_tokens ?? 0);
    let stamps = null;
    if (first != null) {
      stamps = [first];
      for (const g of out.intertoken_us || []) stamps.push(stamps[stamps.length - 1] + g / 1000);
    } else {
      stamps = n === 1 ? [end] : [];
    }
    return { prompt_tokens: out.num_prompt_tokens, output_tokens: n, stamps, first_ms: first ?? (n === 1 ? end : null), text: out.text };
  }
}

export async function stats() {
  try {
    return { memory_bytes: await pie.memoryBytes() };
  } catch {
    return {};
  }
}
