import { createRequire } from "node:module";
import { homedir } from "node:os";
import { pathToFileURL } from "node:url";
import { runBench } from "./bench.mjs";

const root = (process.env.PIE_ROOT ?? `${homedir()}/pie`).replace(/\/?$/, "/");
const { PieClient } = await import(pathToFileURL(`${root}packages/javascript/client/src/index.js`).href);
const require = createRequire(pathToFileURL(`${root}packages/javascript/client/package.json`).href);
const WsWebSocket = require("ws");
globalThis.WebSocket = class extends WsWebSocket {
  constructor(url) {
    super(url, { headers: { "x-pie-identity": "bench" } });
  }
};

const uri = process.argv[2] ?? "ws://127.0.0.1:28417/v1/ws";

const client = new PieClient(uri);
await client.connect();
const program = await client.installProgram(`${root}examples/target/wasm32-wasip3/release/text_completion.wasm`, null, true);
const carried = await client.installProgram(`${root}examples/target/wasm32-wasip3/release/naive_baseline.wasm`, null, true);
const result = { host: "native", uri, bench: await runBench(client, program, console.log, { carried }) };
await client.close();
console.log("RESULT " + JSON.stringify(result));
