const SHORT = "The capital of France is";

function longPrompt(words) {
  const out = [];
  for (let i = 1; out.length < words; i++) out.push(`${i},`);
  return "Count: " + out.join(" ") + " and the next number is";
}

const now = () => (typeof performance !== "undefined" ? performance.now() : Date.now());

async function complete(client, program, input) {
  const t0 = now();
  const proc = await client.launchProcess(program, input);
  const tLaunch = now();
  for (;;) {
    const { event, value } = await proc.recv();
    if (event === "return") {
      return { ms: now() - t0, launchMs: tLaunch - t0, ret: JSON.parse(value) };
    }
    if (event === "error") throw new Error(value);
  }
}

function median(xs) {
  const s = [...xs].sort((a, b) => a - b);
  return s.length ? s[Math.floor(s.length / 2)] : NaN;
}

export async function runBench(client, program, log = () => {}, opts = {}) {
  const r = {};

  const warm = await complete(client, program, { prompt: SHORT, max_tokens: 4 });
  r.warm_ms = +warm.ms.toFixed(1);
  log(`warm: ${r.warm_ms} ms`);

  const ttft = [];
  for (let i = 0; i < 5; i++) ttft.push((await complete(client, program, { prompt: SHORT, max_tokens: 1 })).ms);
  r.ttft_short_ms = +median(ttft).toFixed(1);
  log(`ttft short: ${r.ttft_short_ms} ms (median of 5)`);

  const t64 = [];
  for (let i = 0; i < 3; i++) t64.push((await complete(client, program, { prompt: SHORT, max_tokens: 64 })).ms);
  r.gen64_ms = +median(t64).toFixed(1);
  r.decode_ms_per_token = +((r.gen64_ms - r.ttft_short_ms) / 63).toFixed(2);
  r.decode_tok_s = +(1000 / r.decode_ms_per_token).toFixed(1);
  log(`64 tokens: ${r.gen64_ms} ms → ${r.decode_ms_per_token} ms/token, ${r.decode_tok_s} tok/s`);

  for (const words of [200, 600]) {
    const prompt = longPrompt(words);
    const t = [];
    for (let i = 0; i < 3; i++) t.push((await complete(client, program, { prompt, max_tokens: 1 })).ms);
    r[`ttft_${words}w_ms`] = +median(t).toFixed(1);
    log(`ttft ${words}-word prompt (${prompt.length} chars): ${r[`ttft_${words}w_ms`]} ms`);
  }

  for (const n of [1, 2, 4, 8]) {
    const t0 = now();
    const runs = await Promise.all(
      Array.from({ length: n }, (_, i) =>
        complete(client, program, { prompt: `${SHORT} (${i})`, max_tokens: 32 }),
      ),
    );
    const wall = now() - t0;
    const tokens = runs.reduce((s, x) => s + x.ret.count, 0);
    r[`conc${n}_wall_ms`] = +wall.toFixed(1);
    r[`conc${n}_tok_s`] = +((tokens * 1000) / wall).toFixed(1);
    r[`conc${n}_lat_ms`] = +median(runs.map((x) => x.ms)).toFixed(1);
    log(`${n} concurrent × 32 tokens: ${r[`conc${n}_wall_ms`]} ms wall, ${r[`conc${n}_tok_s`]} tok/s aggregate, median latency ${r[`conc${n}_lat_ms`]} ms`);
  }

  const many = [];
  for (let i = 0; i < 30; i++) many.push((await complete(client, program, { prompt: SHORT, max_tokens: 8 })).ms);
  r.repeat30_median_ms = +median(many).toFixed(1);
  r.repeat30_max_ms = +Math.max(...many).toFixed(1);
  log(`30 × 8 tokens: median ${r.repeat30_median_ms} ms, max ${r.repeat30_max_ms} ms`);

  if (opts.carried) {
    await complete(client, opts.carried, { prompt: SHORT, max_tokens: 4 });
    const t1 = [];
    const t64c = [];
    for (let i = 0; i < 3; i++) t1.push((await complete(client, opts.carried, { prompt: SHORT, max_tokens: 1 })).ms);
    for (let i = 0; i < 3; i++) t64c.push((await complete(client, opts.carried, { prompt: SHORT, max_tokens: 64 })).ms);
    r.carried_ttft_ms = +median(t1).toFixed(1);
    r.carried_decode_ms_per_token = +((median(t64c) - median(t1)) / 63).toFixed(2);
    r.carried_decode_tok_s = +(1000 / r.carried_decode_ms_per_token).toFixed(1);
    log(`device-carried: ttft ${r.carried_ttft_ms} ms, ${r.carried_decode_ms_per_token} ms/token, ${r.carried_decode_tok_s} tok/s`);
    const t0 = now();
    const runs = await Promise.all(Array.from({ length: 4 }, (_, i) => complete(client, opts.carried, { prompt: `${SHORT} (${i})`, max_tokens: 32, seed: i + 1 })));
    const wall = now() - t0;
    r.carried_conc4_tok_s = +((runs.reduce((s, x) => s + x.ret.count, 0) * 1000) / wall).toFixed(1);
    log(`device-carried 4 concurrent × 32: ${r.carried_conc4_tok_s} tok/s aggregate`);
  }

  if (opts.memory) {
    const before = await opts.memory();
    for (let i = 0; i < 200; i++) await complete(client, program, { prompt: SHORT, max_tokens: 2 });
    const after = await opts.memory();
    r.memory_before_200_runs_mib = +before.toFixed(0);
    r.memory_after_200_runs_mib = +after.toFixed(0);
    log(`memory: ${before.toFixed(0)} MiB → ${after.toFixed(0)} MiB after 200 more runs`);
  }
  return r;
}
