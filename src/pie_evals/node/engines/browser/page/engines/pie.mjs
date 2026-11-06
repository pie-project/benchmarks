// Pie in the tab: @pie-project/server-web (the runtime and its WebGPU engine as wasm, built at the job's pie
// commit) boots the imported .wgpu.zt; every request is one process of the text-completion-bench inferlet,
// the program pie_bench.py measures native pie with, on the same prompt token ids every engine is sent.
let pie = null;
let client = null;
let program = null;

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
  client = await pie.connect();
  return { pie_summary: summary };
}

export async function generate({ ids, prompt, max_tokens, temperature, top_p, seed, ignore_eos, timing, onToken }) {
  const input = {
    max_tokens, temperature: temperature ?? 0, top_p: top_p ?? 1, ignore_eos: ignore_eos !== false, return_text: false,
    // the first token's stamp and every gap after it, as pie_bench.py asks for one request at a time
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
    // the guest's gaps from its first token rebuild every token's stamp on the tab's clock (pie_bench's reconstruct_token_arrivals)
    let stamps = null;
    if (first != null) {
      stamps = [first];
      for (const g of out.intertoken_us || []) stamps.push(stamps[stamps.length - 1] + g / 1000);
    } else {
      stamps = n ? [end] : [];
    }
    return { prompt_tokens: out.num_prompt_tokens, output_tokens: n, stamps, first_ms: first ?? (n ? end : null) };
  }
}

export async function stats() {
  try {
    return { memory_bytes: await pie.memoryBytes() };
  } catch {
    return {};
  }
}
