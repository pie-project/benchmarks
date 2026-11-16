import argparse
import http.client
import json
import os
import shutil
import signal
import statistics
import subprocess
import sys
import threading
import time
import urllib.request
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE = Path.home() / ".cache" / "etude-army"
HF_CACHE = Path(os.environ.get("HF_HUB_CACHE") or Path.home() / ".cache/huggingface/hub")
REQUEST = 32768

MODELS = {
    "qwen3.6-35b-a3b": {
        "repo": "mlx-community/Qwen3.6-35B-A3B-4bit",
        "revision": "38740b847e4cb78f352aba30aa41c76e08e6eb46",
        "sku": "qwen36-35b-a3b-u4g64-kv-bf16",
        "files": {
            "config.json": 23591,
            "model-00001-of-00004.safetensors": 5288196018,
            "model-00002-of-00004.safetensors": 5368472749,
            "model-00003-of-00004.safetensors": 5368324139,
            "model-00004-of-00004.safetensors": 4377211365,
            "model.safetensors.index.json": 215755,
            "tokenizer.json": 19989343,
            "tokenizer_config.json": 1139,
        },
    },
    "qwen3.8-27b": {
        "repo": "mlx-community/Qwen3.8-27B-4bit",
        "revision": "3e6447f082e89cc7f0bc6e5441afd38dfce760ff",
        "sku": "qwen38-27b-u4g64-kv-bf16",
        "files": {
            "config.json": 4932,
            "model-00001-of-00003.safetensors": 5343268662,
            "model-00002-of-00003.safetensors": 5354185130,
            "model-00003-of-00003.safetensors": 5357087557,
            "model.safetensors.index.json": 218281,
            "tokenizer.json": 19989325,
            "tokenizer_config.json": 1165,
        },
    },
    "qwen3.5-9b": {
        "repo": "mlx-community/Qwen3.5-9B-4bit",
        "revision": "8b2b98c00a6b4d291155e4890773ca8f769aee53",
        "sku": "qwen35-d9b-u4g64-kv-bf16",
        "files": {
            "config.json": 3331,
            "model-00001-of-00002.safetensors": 5349771222,
            "model-00002-of-00002.safetensors": 600449850,
            "model.safetensors.index.json": 123592,
            "tokenizer.json": 19989343,
            "tokenizer_config.json": 1139,
        },
    },
}

SYSTEM = """You are a coding agent working inside a git repository on the user's Mac.
You help with software engineering tasks: fixing bugs, adding features, refactoring, explaining code and reviewing changes.

# How you work
- Read before you write. Use the read, glob, grep and list tools to understand the code you are about to change, its callers and its tests.
- Keep changes minimal and focused on the task. Match the style, naming and structure of the surrounding code. Do not reformat code you did not change.
- Never invent APIs. If you are unsure whether a function, flag or file exists, look it up with grep or read first.
- After an edit, run the project's own checks (tests, linters, type checkers) with the bash tool and fix what they report.
- Do not commit, push, or rewrite git history unless the user asks.
- Never print or log secrets, tokens or keys. Never weaken security checks to make a test pass.
- Prefer small, reversible steps. When a command fails, read the error carefully before trying again.
- Use the todowrite tool to plan multi-step work and keep it current.

# Answers
- Be concise and direct. Lead with the result, then the evidence.
- Quote code with file paths and line numbers so the user can follow along.
- When you review code, list concrete problems first (bugs, races, error handling, resource leaks, security), then smaller issues (naming, duplication, tests), each with a short suggested fix.

# Project instructions
"""

TOOLS = [
    ("bash", "Run a shell command in the repository with a timeout. Use it for builds, tests, linters, git status and other commands. Commands run in a persistent shell; quote paths with spaces. Avoid interactive commands and long-running servers. Output longer than 30000 characters is truncated, so prefer filtered output (grep, head, tail).", {"command": ("string", "The command to run"), "timeout": ("integer", "Timeout in milliseconds, up to 600000"), "description": ("string", "Five to ten words describing what the command does")}, ["command"]),
    ("read", "Read a file from the repository. Returns up to 2000 lines starting at offset, each prefixed with its line number. Use offset and limit for long files. Reading a directory, a binary file or a missing file returns an error.", {"filePath": ("string", "Absolute path of the file"), "offset": ("integer", "Line to start from"), "limit": ("integer", "Number of lines to read")}, ["filePath"]),
    ("edit", "Replace exact text in a file. oldString must match the file exactly, including indentation, and must be unique unless replaceAll is true. Read the file first; edits to files you have not read fail.", {"filePath": ("string", "Absolute path of the file"), "oldString": ("string", "Text to replace"), "newString": ("string", "Replacement text"), "replaceAll": ("boolean", "Replace every occurrence")}, ["filePath", "oldString", "newString"]),
    ("write", "Write a whole file, creating parent directories. Overwrites an existing file, so read it first. Prefer edit for changes to existing files.", {"filePath": ("string", "Absolute path of the file"), "content": ("string", "Full file content")}, ["filePath", "content"]),
    ("glob", "Find files by glob pattern such as src/**/*.py, sorted by modification time. Use it to locate files by name.", {"pattern": ("string", "Glob pattern"), "path": ("string", "Directory to search from")}, ["pattern"]),
    ("grep", "Search file contents with a regular expression (ripgrep syntax). Returns matching files and lines. Filter with include, such as *.rs or *.{ts,tsx}.", {"pattern": ("string", "Regular expression"), "path": ("string", "Directory to search"), "include": ("string", "File pattern to include")}, ["pattern"]),
    ("list", "List the files and directories under a path, ignoring common build and dependency folders.", {"path": ("string", "Directory to list"), "ignore": ("array", "Glob patterns to ignore")}, []),
    ("todowrite", "Create or update the task list for the current work. Each item has content, status (pending, in_progress, completed, cancelled) and priority. Keep exactly one item in progress.", {"todos": ("array", "The full updated todo list")}, ["todos"]),
    ("apply_patch", "Apply a unified diff patch to one or more files. Each hunk must match the current file contents with three lines of context.", {"patch": ("string", "The patch text")}, ["patch"]),
    ("task", "Start a subagent for an independent, well-scoped search or analysis task and return its final report. Give it a complete, self-contained prompt.", {"description": ("string", "Three to five words"), "prompt": ("string", "The full task for the subagent")}, ["description", "prompt"]),
]


def tools():
    out = []
    for name, description, props, required in TOOLS:
        properties = {}
        for key, (kind, text) in props.items():
            properties[key] = {"type": kind, "description": text}
            if kind == "array":
                properties[key]["items"] = {"type": "object"} if key == "todos" else {"type": "string"}
        out.append({"type": "function", "function": {"name": name, "description": description, "parameters": {"type": "object", "properties": properties, "required": required}}})
    return out


def sources():
    files = sorted(p for p in list((ROOT / "src").rglob("*.py")) + list((ROOT / "server").rglob("*.py")) if p.stat().st_size > 20000)
    return [(str(p.relative_to(ROOT)), p.read_text(errors="replace")) for p in files]


class Prompts:
    def __init__(self):
        readme = (ROOT / "README.md").read_text(errors="replace")
        self.system = SYSTEM + readme
        self.tools = tools()
        self.files = sources()
        self.chars = 24000

    def user(self, index, nonce):
        name, text = self.files[index % len(self.files)]
        body = (text * (1 + self.chars // max(len(text), 1)))[: self.chars]
        return (f"Request {nonce}. Review `{name}` below as a senior engineer. Do not call any tools; answer directly in text. "
                f"List every bug, risk and improvement you see, each with the line it concerns and a short code fix. "
                f"Be thorough: write at least 800 words.\n\n```python\n{body}\n```")

    def messages(self, index, nonce):
        return [{"role": "system", "content": self.system}, {"role": "user", "content": self.user(index, nonce)}]


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def snapshot(key):
    spec = MODELS[key]
    org, name = spec["repo"].split("/")
    hf = HF_CACHE / f"models--{org}--{name}" / "snapshots" / spec["revision"]
    if all((hf / f).is_file() and (hf / f).stat().st_size == size for f, size in spec["files"].items()):
        return hf, False
    target = CACHE / f"{org}--{name}@{spec['revision'][:12]}"
    target.mkdir(parents=True, exist_ok=True)
    missing = sum(size for f, size in spec["files"].items() if not ((target / f).is_file() and (target / f).stat().st_size == size))
    free = shutil.disk_usage(target).free
    if missing and free < missing + 30 * 2**30:
        raise RuntimeError(f"not enough disk for {key}: need {missing / 2**30:.1f} GiB + 30 GiB margin, have {free / 2**30:.1f} GiB")
    for f, size in spec["files"].items():
        path = target / f
        have = path.stat().st_size if path.is_file() else 0
        if have == size:
            continue
        url = f"https://huggingface.co/{spec['repo']}/resolve/{spec['revision']}/{f}"
        for attempt in range(5):
            have = path.stat().st_size if path.is_file() else 0
            req = urllib.request.Request(url, headers={"Range": f"bytes={have}-"} if have else {})
            try:
                with urllib.request.urlopen(req, timeout=120) as r, open(path, "ab" if have and r.status == 206 else "wb") as out:
                    t0 = time.monotonic()
                    while True:
                        chunk = r.read(16 << 20)
                        if not chunk:
                            break
                        out.write(chunk)
                    log(f"  {f}: {size / 2**30:.2f} GiB in {time.monotonic() - t0:.0f}s")
                if path.stat().st_size == size:
                    break
            except Exception as e:
                log(f"  {f}: attempt {attempt + 1} failed: {e}")
                time.sleep(5)
        if path.stat().st_size != size:
            raise RuntimeError(f"download of {f} incomplete")
    return target, True


def find(root, name):
    preferred = root / "Resources" / ("inferlets/" + name if name.endswith(".wasm") else name)
    if preferred.is_file():
        return preferred
    found = sorted(p for p in root.rglob(name) if p.is_file())
    if not found:
        raise RuntimeError(f"{name} not found under {root}")
    return found[0]


class Gateway:
    def __init__(self, app, model, lanes, request, out):
        contents = Path(app) / "Contents"
        self.gateway = find(contents, "etude-gateway")
        self.engine = find(contents, "etude-engine")
        self.inferlets = find(contents, "etude-chat.wasm").parent
        self.stage = Path(out) / f"stage-{uuid.uuid4().hex[:8]}"
        for d in ("engine", "home", "tmp"):
            (self.stage / d).mkdir(parents=True, exist_ok=True)
        self.key_file = self.stage / "engine" / "api-key"
        self.log = self.stage / "gateway.log"
        self.model, self.lanes, self.request = model, lanes, request
        self.proc = None
        self.port = None
        self.model_id = None
        self.boot_s = None

    def start(self, path, sku, timeout=1200):
        args = [str(self.gateway), "serve", "--port", "0", "--engine-bin", str(self.engine), "--engine-home", str(self.stage / "engine"),
                "--model", str(path), "--sku", sku, "--inferlet-dir", str(self.inferlets), "--api-key-file", str(self.key_file),
                "--driver", "metal", "--max-concurrent-runs", str(self.lanes), "--context-tokens", str(self.lanes * self.request),
                "--request-tokens", str(self.request)]
        env = {"HOME": str(self.stage / "home"), "TMPDIR": str(self.stage / "tmp"), "PATH": "/usr/bin:/bin:/usr/sbin:/sbin", "LANG": "C", "LC_ALL": "C"}
        t0 = time.monotonic()
        self.proc = subprocess.Popen(args, env=env, stdout=open(self.log, "wb"), stderr=subprocess.STDOUT, start_new_session=True)
        while time.monotonic() - t0 < timeout:
            for line in self.events():
                if line.get("event") == "ready":
                    self.port = int(line["gateway_port"])
                    self.model_id = line.get("model")
                    self.boot_s = round(time.monotonic() - t0, 1)
                    return
            if self.proc.poll() is not None:
                raise RuntimeError(f"gateway exited {self.proc.returncode}: {self.tail()}")
            time.sleep(1)
        raise RuntimeError(f"gateway not ready in {timeout}s: {self.tail()}")

    def events(self):
        out = []
        try:
            for raw in self.log.read_text(errors="replace").splitlines():
                if raw.startswith("{"):
                    try:
                        out.append(json.loads(raw))
                    except ValueError:
                        pass
        except FileNotFoundError:
            pass
        return out

    def tail(self, n=30):
        try:
            return "\n".join(self.log.read_text(errors="replace").splitlines()[-n:])
        except FileNotFoundError:
            return ""

    def key(self):
        return self.key_file.read_text().strip()

    def stop(self):
        if self.proc and self.proc.poll() is None:
            try:
                os.killpg(self.proc.pid, signal.SIGTERM)
                self.proc.wait(timeout=60)
            except Exception:
                try:
                    os.killpg(self.proc.pid, signal.SIGKILL)
                except Exception:
                    pass
        time.sleep(3)


def stream(port, key, model, messages, tools, max_tokens, t_start):
    body = {"model": model, "messages": messages, "tools": tools, "max_tokens": max_tokens, "temperature": 0.7, "stream": True,
            "stream_options": {"include_usage": True}, "enable_thinking": False}
    rec = {"ok": False, "ttft": None, "end": None, "first": None, "completion": 0, "prompt": 0, "cached": 0, "error": None}
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=1800)
    try:
        conn.request("POST", "/v1/chat/completions", body=json.dumps(body), headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
        r = conn.getresponse()
        if r.status != 200:
            rec["error"] = f"http {r.status}: {r.read()[:400].decode(errors='replace')}"
            return rec
        for raw in r:
            line = raw.decode(errors="replace").strip()
            if not line.startswith("data:"):
                continue
            data = line[5:].strip()
            if data == "[DONE]":
                break
            obj = json.loads(data)
            if obj.get("error"):
                rec["error"] = json.dumps(obj["error"])[:400]
                break
            for c in obj.get("choices") or []:
                d = c.get("delta") or {}
                if d.get("content") or d.get("reasoning_content") or d.get("tool_calls"):
                    now = time.monotonic()
                    if rec["first"] is None:
                        rec["first"] = now
                        rec["ttft"] = now - t_start
            u = obj.get("usage")
            if u:
                rec["completion"] = int(u.get("completion_tokens") or 0)
                rec["prompt"] = int(u.get("prompt_tokens") or 0)
                rec["cached"] = int((u.get("prompt_tokens_details") or {}).get("cached_tokens") or 0)
        rec["end"] = time.monotonic()
        rec["ok"] = rec["error"] is None and rec["completion"] > 0
        if not rec["ok"] and rec["error"] is None:
            rec["error"] = "no tokens"
    except Exception as e:
        rec["error"] = f"{type(e).__name__}: {e}"
    finally:
        conn.close()
    return rec


def kind(error):
    e = (error or "").lower()
    for k in ("channel closed", "engine_unavailable", "timeout", "context", "no tokens"):
        if k in e:
            return k.replace(" ", "_")
    return "other" if e else None


def burst(gw, prompts, n, offset, max_tokens):
    results = [None] * n
    barrier = threading.Barrier(n + 1)
    key = gw.key()

    def worker(i):
        msgs = prompts.messages(offset + i, uuid.uuid4().hex)
        barrier.wait()
        results[i] = stream(gw.port, key, gw.model_id, msgs, prompts.tools, max_tokens, t0[0])

    t0 = [0.0]
    threads = [threading.Thread(target=worker, args=(i,)) for i in range(n)]
    for t in threads:
        t.start()
    t0[0] = time.monotonic()
    barrier.wait()
    for t in threads:
        t.join()
    ok = [r for r in results if r["ok"]]
    row = {"n": n, "ok": len(ok), "failures": {}}
    for r in results:
        if not r["ok"]:
            k = kind(r["error"])
            row["failures"][k] = row["failures"].get(k, 0) + 1
            row.setdefault("errors", []).append(r["error"])
    if ok:
        toks = sum(r["completion"] for r in ok)
        first = min(r["first"] for r in ok)
        last = max(r["end"] for r in ok)
        row.update({
            "completion_tokens": toks,
            "prompt_tokens_mean": round(statistics.mean(r["prompt"] for r in ok)),
            "agg_decode_tok_s": round(toks / max(last - first, 1e-6), 1),
            "e2e_tok_s": round(toks / max(last - t0[0], 1e-6), 1),
            "per_stream_tok_s": round(statistics.mean(r["completion"] / max(r["end"] - r["first"], 1e-6) for r in ok), 1),
            "ttft_s_p50": round(statistics.median(r["ttft"] for r in ok), 2),
            "ttft_s_max": round(max(r["ttft"] for r in ok), 2),
            "wall_s": round(last - t0[0], 1),
            "prefix_hit": round(sum(r["cached"] for r in ok) / max(sum(r["prompt"] for r in ok), 1), 3),
        })
    return row


def calibrate(gw, prompts, target):
    key = gw.key()
    points = []
    for chars in (8000, 32000):
        prompts.chars = chars
        r = stream(gw.port, key, gw.model_id, prompts.messages(0, uuid.uuid4().hex), prompts.tools, 1, time.monotonic())
        if not r["prompt"]:
            raise RuntimeError(f"calibration failed: {r['error']}")
        points.append((chars, r["prompt"]))
    (c1, p1), (c2, p2) = points
    per = (p2 - p1) / (c2 - c1)
    prompts.chars = max(2000, int(c1 + (target - p1) / per))
    shared = p1 - per * c1
    log(f"calibrated: {per * 1000:.0f} tokens/kchar, shared prefix ~{shared:.0f} tokens, file slice {prompts.chars} chars")
    return {"tokens_per_kchar": round(per * 1000, 1), "shared_prefix_tokens": round(shared), "file_chars": prompts.chars}


def sweep(args):
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    prompts = Prompts()
    report = {"started": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "app": args.app, "machine": machine(), "request_tokens": REQUEST,
              "max_tokens": args.max_tokens, "target_prompt_tokens": args.prompt_tokens, "models": {}}
    deadline = time.monotonic() + args.budget_min * 60
    for key in args.models.split(","):
        entry = report["models"].setdefault(key, {"sku": MODELS[key]["sku"], "rows": []})
        if time.monotonic() > deadline:
            entry["skipped"] = "time budget"
            continue
        try:
            t0 = time.monotonic()
            path, downloaded = snapshot(key)
            entry.update({"snapshot": str(path), "downloaded": downloaded, "fetch_s": round(time.monotonic() - t0)})
            log(f"{key}: snapshot {path} ({'downloaded' if downloaded else 'cached'})")
        except Exception as e:
            entry["error"] = f"snapshot: {e}"
            log(f"{key}: {entry['error']}")
            continue
        calibrated = False
        for n in [int(w) for w in args.widths.split(",")]:
            if time.monotonic() > deadline:
                entry.setdefault("skipped_widths", []).append(n)
                continue
            gw = Gateway(args.app, key, n, REQUEST, out)
            try:
                gw.start(path, MODELS[key]["sku"])
                log(f"{key} N={n}: gateway ready on {gw.port} in {gw.boot_s}s ({gw.model_id})")
                stream(gw.port, gw.key(), gw.model_id, [{"role": "system", "content": prompts.system}, {"role": "user", "content": "Say ok."}], prompts.tools, 8, time.monotonic())
                if not calibrated:
                    entry["calibration"] = calibrate(gw, prompts, args.prompt_tokens)
                    calibrated = True
                for rep in range(args.reps):
                    row = burst(gw, prompts, n, 1 + rep * 64 + n, args.max_tokens)
                    row.update({"rep": rep, "boot_s": gw.boot_s})
                    entry["rows"].append(row)
                    log(f"{key} N={n} rep={rep}: {json.dumps(row)}")
                entry.setdefault("gateway_requests", {})[str(n)] = [e for e in gw.events() if e.get("event") == "request"][-args.reps * n:]
            except Exception as e:
                entry["rows"].append({"n": n, "error": str(e)[:2000]})
                log(f"{key} N={n}: {e}")
            finally:
                gw.stop()
                keep_log(gw, out, key, n)
            (out / "sweep.json").write_text(json.dumps(report, indent=1))
        if entry.get("downloaded") and key not in args.keep.split(","):
            shutil.rmtree(entry["snapshot"], ignore_errors=True)
    report["summary"] = summarize(report)
    (out / "sweep.json").write_text(json.dumps(report, indent=1))
    (out / "summary.md").write_text(render(report))
    print(render(report))


def keep_log(gw, out, key, n):
    try:
        shutil.copy(gw.log, out / f"gateway-{key}-n{n}.log")
        shutil.rmtree(gw.stage, ignore_errors=True)
    except Exception:
        pass


def summarize(report):
    summary = {}
    for key, entry in report["models"].items():
        by_n = {}
        for row in entry.get("rows", []):
            if "agg_decode_tok_s" in row:
                by_n.setdefault(row["n"], []).append(row)
        base = statistics.mean(r["agg_decode_tok_s"] for r in by_n[1]) if 1 in by_n else None
        lines = []
        for n in sorted(by_n):
            rows = by_n[n]
            agg = statistics.mean(r["agg_decode_tok_s"] for r in rows)
            fails = {}
            for r in [r for r in entry["rows"] if r.get("n") == n]:
                for k, v in (r.get("failures") or {}).items():
                    fails[k] = fails.get(k, 0) + v
            lines.append({"n": n, "agg_decode_tok_s": round(agg, 1), "speedup": round(agg / base, 2) if base else None,
                          "e2e_tok_s": round(statistics.mean(r["e2e_tok_s"] for r in rows), 1),
                          "per_stream_tok_s": round(statistics.mean(r["per_stream_tok_s"] for r in rows), 1),
                          "ttft_s_p50": round(statistics.mean(r["ttft_s_p50"] for r in rows), 2),
                          "ttft_s_max": max(r["ttft_s_max"] for r in rows),
                          "prefix_hit": round(statistics.mean(r["prefix_hit"] for r in rows), 3),
                          "prompt_tokens": round(statistics.mean(r["prompt_tokens_mean"] for r in rows)), "failures": fails})
        summary[key] = lines
    return summary


def render(report):
    out = []
    for key, lines in report.get("summary", {}).items():
        if report["models"][key].get("skipped"):
            out.append(f"\n### {key}: skipped ({report['models'][key]['skipped']})")
            continue
        out.append(f"\n### {key} ({report['models'][key].get('sku')})\n")
        out.append("| N | agg decode tok/s | speedup | e2e tok/s | per-stream tok/s | TTFT p50 / max (s) | prefix hit | prompt tok | failures |")
        out.append("|---|---|---|---|---|---|---|---|---|")
        for l in lines:
            out.append(f"| {l['n']} | {l['agg_decode_tok_s']} | {l['speedup']}x | {l['e2e_tok_s']} | {l['per_stream_tok_s']} | {l['ttft_s_p50']} / {l['ttft_s_max']} | {l['prefix_hit']:.0%} | {l['prompt_tokens']} | {l['failures'] or '-'} |")
        for row in report["models"][key].get("rows", []):
            if row.get("error"):
                out.append(f"\nN={row['n']} error: {row['error'][:300]}")
        err = report["models"][key].get("error")
        if err:
            out.append(f"\nerror: {err}")
    return "\n".join(out) + "\n"


def machine():
    def sh(cmd):
        try:
            return subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=20).stdout.strip()
        except Exception as e:
            return str(e)
    return {"chip": sh("sysctl -n machdep.cpu.brand_string"), "memory_gib": round(int(sh("sysctl -n hw.memsize") or 0) / 2**30),
            "macos": sh("sw_vers -productVersion"), "other_engines": sh("pgrep -lf 'etude|pie|llama|mlx|ollama' | grep -v bench.py | head -20"),
            "disk_free_gib": round(shutil.disk_usage(Path.home()).free / 2**30)}


def serve(args):
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    path, downloaded = snapshot(args.model)
    gw = Gateway(args.app, args.model, args.lanes, args.request, out)
    gw.start(path, MODELS[args.model]["sku"])
    info = {"pid": gw.proc.pid, "port": gw.port, "key_file": str(gw.key_file), "model": gw.model_id, "context": args.request,
            "log": str(gw.log), "snapshot": str(path), "downloaded": downloaded}
    (out / "gateway.json").write_text(json.dumps(info, indent=1))
    log(f"gateway {gw.model_id} on {gw.port}, lanes {args.lanes}, request {args.request}")


def stop(args):
    info = json.loads((Path(args.out) / "gateway.json").read_text())
    try:
        os.killpg(info["pid"], signal.SIGTERM)
        time.sleep(5)
        os.killpg(info["pid"], signal.SIGKILL)
    except ProcessLookupError:
        pass


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("sweep")
    s.add_argument("--app", required=True)
    s.add_argument("--models", default="qwen3.6-35b-a3b,qwen3.8-27b,qwen3.5-9b")
    s.add_argument("--widths", default="1,2,4,8,16")
    s.add_argument("--reps", type=int, default=2)
    s.add_argument("--max-tokens", type=int, default=512)
    s.add_argument("--prompt-tokens", type=int, default=10000)
    s.add_argument("--budget-min", type=int, default=200)
    s.add_argument("--keep", default="")
    s.add_argument("--out", required=True)
    g = sub.add_parser("serve")
    g.add_argument("--app", required=True)
    g.add_argument("--model", default="qwen3.6-35b-a3b")
    g.add_argument("--lanes", type=int, default=3)
    g.add_argument("--request", type=int, default=65536)
    g.add_argument("--out", required=True)
    t = sub.add_parser("stop")
    t.add_argument("--out", required=True)

    a = ap.parse_args()
    {"sweep": sweep, "serve": serve, "stop": stop}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
