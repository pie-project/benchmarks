// One browser engine in headless Chrome on WebGPU, reached over HTTP.
//
//   node bridge.mjs --engine webllm|llamacpp|pie --port N --files DIR [--model URL] [--options JSON]
//
// Serves the page (page/), the engine's own files (--files: the weights, its wasm) at /files/, boots
// Chrome with WebGPU on the machine's GPU (Vulkan on Linux), loads the model in the tab and answers:
//   GET  /health  200 once the model is loaded (503 before)
//   GET  /info    the adapter, the browser and the engine's own load summary
//   POST /run     {requests: [{prompt, ids, max_tokens}], concurrency, warmup, sampling}: runs them in the
//                 tab, at most `concurrency` at once, each timed with the tab's own clock (performance.now):
//                 when it was sent, its first token, every later token and its end
// browser_bench.py is the client: it builds the same prompts openai_bench.py sends every other engine.
import { createServer } from "node:http";
import { createReadStream } from "node:fs";
import { stat } from "node:fs/promises";
import { createRequire } from "node:module";
import { dirname, extname, join, normalize, resolve, sep } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const argv = process.argv.slice(2);
const arg = (name, dflt) => {
  const i = argv.indexOf(`--${name}`);
  return i >= 0 ? argv[i + 1] : dflt;
};
const engine = arg("engine");
const port = Number(arg("port", "8000"));
const files = resolve(arg("files", "."));
const options = JSON.parse(arg("options", "{}"));

const TYPES = {
  ".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8", ".mjs": "text/javascript; charset=utf-8",
  ".wasm": "application/wasm", ".json": "application/json", ".txt": "text/plain; charset=utf-8", ".toml": "text/plain; charset=utf-8",
};
const roots = { "/files/": files, "/vendor/": join(here, "node_modules"), "/": join(here, "page") };

async function sendFile(req, res, file) {
  let info;
  try {
    info = await stat(file);
  } catch {
    return false;
  }
  if (!info.isFile()) return false;
  const headers = {
    "content-type": TYPES[extname(file)] ?? "application/octet-stream", "cache-control": "no-store",
    // cross-origin isolated: pie's runtime shares memory with its worker (SharedArrayBuffer)
    "cross-origin-opener-policy": "same-origin", "cross-origin-embedder-policy": "require-corp",
    "cross-origin-resource-policy": "same-origin", "accept-ranges": "bytes",
  };
  const range = req.headers.range?.match(/^bytes=(\d+)-(\d*)$/);
  if (range) {
    const start = Number(range[1]);
    const end = range[2] ? Math.min(Number(range[2]), info.size - 1) : info.size - 1;
    res.writeHead(206, { ...headers, "content-range": `bytes ${start}-${end}/${info.size}`, "content-length": end - start + 1 });
    if (req.method === "HEAD") return res.end(), true;
    createReadStream(file, { start, end }).pipe(res);
    return true;
  }
  res.writeHead(200, { ...headers, "content-length": info.size });
  if (req.method === "HEAD") return res.end(), true;
  createReadStream(file).pipe(res);
  return true;
}

let page = null;
let ready = false;
let loadError = null;
let info = {};
const body = (req) => new Promise((ok, bad) => {
  const parts = [];
  req.on("data", (c) => parts.push(c));
  req.on("end", () => ok(Buffer.concat(parts).toString("utf8")));
  req.on("error", bad);
});
const json = (res, code, obj) => {
  res.writeHead(code, { "content-type": "application/json" });
  res.end(JSON.stringify(obj));
};
// one /run at a time: a bench never overlaps two
let running = Promise.resolve();

const server = createServer(async (req, res) => {
  const url = new URL(req.url, "http://x");
  try {
    if (url.pathname === "/health") return loadError ? json(res, 500, { error: loadError }) : json(res, ready ? 200 : 503, { ready });
    if (url.pathname === "/info") return json(res, 200, info);
    if (url.pathname === "/run" && req.method === "POST") {
      if (!ready) return json(res, 503, { error: "not loaded" });
      const job = JSON.parse(await body(req));
      const turn = running.then(() => watched(page.evaluate((j) => window.bench.run(j), job)));
      running = turn.catch(() => {});
      try {
        return json(res, 200, await turn);
      } catch (e) {
        if (!(e instanceof Stalled)) throw e;
        // the engine stopped making progress (no token, no finished request) with requests in flight: the batch
        // fails, and a fresh tab boots the engine again for the next one
        console.log(`bridge: ${e.message}; reloading the tab`);
        await reboot().catch((err) => console.log(`bridge: reboot failed: ${err?.message ?? err}`));
        return json(res, 200, { error: e.message, results: [] });
      }
    }
    const path = normalize(decodeURIComponent(url.pathname));
    for (const [prefix, root] of Object.entries(roots)) {
      if (!path.startsWith(prefix)) continue;
      const file = resolve(root, "." + path.slice(prefix.length - 1) + (path.endsWith("/") ? "index.html" : ""));
      if (!file.startsWith(resolve(root) + sep)) break;
      if (await sendFile(req, res, file)) return;
      break;
    }
    res.writeHead(404).end("not found");
  } catch (e) {
    json(res, 500, { error: String(e?.stack ?? e) });
  }
});
await new Promise((ok) => server.listen(port, "127.0.0.1", ok));
console.log(`bridge: ${engine} on http://127.0.0.1:${port}/ (files ${files})`);

const require = createRequire(join(here, "package.json"));
const { chromium } = require("playwright");
// WebGPU on the real GPU: Dawn's Vulkan backend on the NVIDIA driver (its graphics libraries mounted:
// NVIDIA_DRIVER_CAPABILITIES=all), never SwiftShader. Headless has no window surface, so Chrome's own Vulkan
// runs without one; Dawn hides shader-f16 on NVIDIA's Vulkan driver unless vulkan_enable_f16_on_nvidia is on,
// and every engine here gets the same toggles.
const chromeArgs = [
  "--no-sandbox", "--enable-unsafe-webgpu", "--ignore-gpu-blocklist", "--use-angle=vulkan", "--enable-features=Vulkan",
  "--disable-vulkan-surface", "--enable-dawn-features=allow_unsafe_apis,vulkan_enable_f16_on_nvidia",
  "--disable-background-timer-throttling", "--disable-renderer-backgrounding", "--disable-backgrounding-occluded-windows",
  ...(process.env.BROWSER_EXTRA_ARGS || "").split(/\s+/).filter(Boolean),
];
// Playwright's own Chromium build (pinned with it in package.json), unless CHROME_BIN names another. A profile on
// disk, made fresh for this launch: an in-memory one has no storage quota for the weights WebLLM and pie keep in
// the origin's caches (Cache API, OPFS), and a fresh one has nothing in them from an earlier run
const { mkdtempSync, rmSync } = await import("node:fs");
const { tmpdir } = await import("node:os");
const profile = mkdtempSync(join(process.env.BROWSER_PROFILE_ROOT || tmpdir(), "bridge-profile-"));
const context = await chromium.launchPersistentContext(profile, {
  headless: true, args: chromeArgs, executablePath: process.env.CHROME_BIN || undefined,
  channel: process.env.CHROME_BIN ? undefined : "chromium",
});
const version = context.browser()?.version() ?? (await context.newCDPSession(context.pages()[0] ?? (await context.newPage())).then((s) => s.send("Browser.getVersion")).then((v) => v.product).catch(() => "unknown"));
page = context.pages()[0] ?? (await context.newPage());
const cleanup = () => { try { rmSync(profile, { recursive: true, force: true }); } catch {} };
page.on("console", (m) => console.log(`[tab] ${m.text()}`));
page.on("pageerror", (e) => console.log(`[tab] pageerror: ${e.message}`));
page.on("crash", () => {
  console.log("[tab] crashed");
  loadError = "the tab crashed";
  ready = false;
});
context.on("close", () => {
  console.log("bridge: the browser went away");
  cleanup();
  process.exit(3);
});
const q = new URLSearchParams({ engine, options: JSON.stringify(options) });
class Stalled extends Error {}
const STALL_MS = Number(process.env.BROWSER_STALL_S || 300) * 1000;
// a run that sees no progress for STALL_MS is abandoned (pie's tab has been seen to spin without end under load)
function watched(run) {
  return new Promise((ok, bad) => {
    const timer = setInterval(async () => {
      const age = await Promise.race([page.evaluate(() => window.bench.age()).catch(() => Infinity), new Promise((r) => setTimeout(() => r(Infinity), 20000))]);
      if (age > STALL_MS) {
        clearInterval(timer);
        bad(new Stalled(`no progress in ${Math.round(age / 1000)} s`));
      }
    }, 15000);
    run.then((v) => { clearInterval(timer); ok(v); }, (e) => { clearInterval(timer); bad(e); });
  });
}
async function reboot() {
  ready = false;
  const old = page;
  page = await context.newPage();
  page.on("console", (m) => console.log(`[tab] ${m.text()}`));
  page.on("pageerror", (e) => console.log(`[tab] pageerror: ${e.message}`));
  await old.close().catch(() => {});
  await page.goto(`http://127.0.0.1:${port}/index.html?${q}`);
  info = { ...(await page.evaluate(() => window.bench.boot())), browser: version, chrome_args: chromeArgs, reboots: (info.reboots || 0) + 1 };
  ready = true;
}
await page.goto(`http://127.0.0.1:${port}/index.html?${q}`);
try {
  info = await page.evaluate(() => window.bench.boot());
  info.browser = version;
  info.chrome_args = chromeArgs;
  console.log(`bridge: loaded ${JSON.stringify(info)}`);
  ready = true;
} catch (e) {
  loadError = String(e?.message ?? e);
  console.log(`bridge: load failed: ${loadError}`);
  await context.close().catch(() => {});
  cleanup();
  process.exit(2);
}
for (const sig of ["SIGTERM", "SIGINT"]) process.on(sig, async () => {
  await context.close().catch(() => {});
  cleanup();
  process.exit(0);
});
