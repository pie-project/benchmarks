import argparse
import concurrent.futures as cf
import json
import math
import os
import pathlib
import platform
import shutil
import subprocess
import sys
import threading
import time

import httpx
import yaml

REV = "b968826d9c46dd6066d109eabc6255188de91218"
SYS_PATH = "/usr/bin:/bin:/usr/sbin:/sbin"
TEST_OFFSET = 1500000
ASSISTANT_OPEN = "<|im_start|>assistant\n<think>\n\n</think>\n\n"
ENGINE_Q = ("{ engine { phase generation model { key context output reasoning } appliedModelSettings { model config "
            "{ contextTokens requestTokens maxConcurrentRequests cacheMultiple } } driver gatewayVersion piePid "
            "endpoint { url } conditions { code detail } cacheUsage { usedPages totalPages } } runs { active queued } }")
USAGE_Q = ("query($m: String) { usage(window: DAY, model: $m) { status summary { models requests completedRequests "
           "cutShortByLength failedRequests stoppedRequests promptTokens completionTokens cachedTokens tokensPerSecond "
           "speedReplies prefill { tokensPerSecond requests } ttftMedianMs ttftP90Ms queueMedianMs modelStarts "
           "bootMedianMs } } }")
SETTINGS_M = ("mutation($patch: SettingsPatch!) { setSettings(patch: $patch) { __typename ... on Ack { revision } "
              "... on Refused { code detail } ... on Conflict { revision current } } }")
RESOLVED_Q = ("{ settings { revision modelSettings { model contextTokens requestTokens maxConcurrentRequests } "
              "resolvedModelSettings { model effective { status config { contextTokens requestTokens "
              "maxConcurrentRequests cacheMultiple } conditions { code detail } } } } }")
SAMPLING = {"temperature": 1.0, "topP": 1.0, "topK": 1000, "minP": 0.0, "presencePenalty": 0.0}
T0 = time.monotonic()


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')} +{minutes():.1f}m] {msg}", flush=True)


def minutes():
    return (time.monotonic() - T0) / 60


def sh(cmd):
    try:
        return subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30).stdout.strip()
    except Exception as e:
        return str(e)


class Etude:
    def __init__(self, app, home, out):
        c = pathlib.Path(app) / "Contents"
        cands = [c / "Helpers" / "etude", c / "Helpers" / "Etude Helper.app" / "Contents" / "MacOS" / "etude-helper"]
        self.bin = next(p for p in cands if p.is_file())
        self.pie = c / "Helpers" / "pie"
        self.home = pathlib.Path(home)
        self.state = self.home / "Library" / "Application Support" / "Etude"
        self.out = pathlib.Path(out)
        self.env = {"HOME": str(self.home), "PATH": SYS_PATH, "LANG": "C", "LC_ALL": "C",
                    "TMPDIR": str(self.home / "tmp"), "ETUDE_CORE_ENGINE_DISCOVERY": "off",
                    "HF_HOME": str(self.home / "hf"), "HF_HUB_OFFLINE": "1"}
        self.proc = None
        self.calls = []

    def run(self, *args, timeout=600):
        t = time.monotonic()
        r = subprocess.run([str(self.bin), "--json", *args], env=self.env, capture_output=True, text=True,
                           timeout=timeout)
        dt = time.monotonic() - t
        self.calls.append({"args": list(args)[:3], "rc": r.returncode, "s": round(dt, 1)})
        try:
            data = json.loads(r.stdout) if r.stdout.strip() else None
        except ValueError:
            data = r.stdout
        return r.returncode, data, r.stderr.strip()

    def cli(self, *args, timeout=600):
        rc, data, err = self.run(*args, timeout=timeout)
        if rc != 0:
            raise RuntimeError(f"etude {' '.join(args[:3])}: rc {rc}: {err[:2000]}")
        return data

    def gql(self, query, timeout=300, **variables):
        args = ["gql", query]
        for k, v in variables.items():
            args += ["--var", f"{k}={json.dumps(v)}"]
        return self.run(*args, timeout=timeout)

    def start(self, seed_settings=True):
        self.home.mkdir(parents=True, exist_ok=True)
        os.chmod(self.home, 0o700)
        (self.home / "tmp").mkdir(exist_ok=True)
        (self.state / "settings").mkdir(parents=True, exist_ok=True)
        f = self.state / "settings" / "core.json"
        if seed_settings:
            f.write_text(json.dumps({"version": 1, "settings": {
                "revision": 0, "modelSettings": [], "port": {"mode": "AUTOMATIC", "port": 11435},
                "idleUnloadSecs": 0, "loadOnRequest": False}, "receipt": None}))
        elif f.exists():
            f.unlink()
        logf = open(self.out / "core.log", "ab")
        self.proc = subprocess.Popen([str(self.bin), "core", "--foreground"], env=self.env, stdin=subprocess.DEVNULL,
                                     stdout=logf, stderr=subprocess.STDOUT, start_new_session=True)
        sock = self.state / "run" / "core.sock"
        deadline = time.monotonic() + 180
        while time.monotonic() < deadline:
            if self.proc.poll() is not None:
                raise RuntimeError(f"core exited {self.proc.returncode}: {tail(self.out / 'core.log')}")
            if sock.exists():
                rc, data, err = self.run("status", timeout=120)
                if rc == 0:
                    return data
            time.sleep(1)
        raise RuntimeError(f"core not ready: {tail(self.out / 'core.log')}")

    def installed(self):
        st = self.cli("status")
        return st, {m["key"]: m for m in st.get("models") or [] if m.get("installed")}

    def import_model(self, zt, timeout=3600):
        _, before = self.installed()
        t = time.monotonic()
        self.cli("models", "import", str(zt))
        last = 0
        while time.monotonic() - t < timeout:
            st, now = self.installed()
            new = [k for k in now if k not in before]
            if new:
                return new[0], now[new[0]], time.monotonic() - t
            busy = [{"key": m.get("key"), "acquisition": m.get("acquisition"), "conditions": m.get("conditions")}
                    for m in st.get("models") or []
                    if (m.get("acquisition") or {}).get("phase") not in (None, "IDLE", "COMPLETE")]
            for b in busy:
                if (b["acquisition"] or {}).get("phase") in ("BLOCKED", "CANCELLED"):
                    raise RuntimeError(f"import of {zt.name} stopped: {json.dumps(b)[:2000]}")
            if time.monotonic() - last > 60:
                log(f"  importing {zt.name}: {json.dumps(busy)[:600]}")
                last = time.monotonic()
            time.sleep(5)
        raise RuntimeError(f"import of {zt} not installed after {timeout}s")

    def stop(self):
        if self.proc is None:
            return
        for args in (("down",), ("quit", "--yes")):
            try:
                rc, data, err = self.run(*args, timeout=300)
                log(f"etude {' '.join(args)}: rc {rc} {json.dumps(data)[:300]} {err[:300]}")
            except Exception as e:
                log(f"etude {' '.join(args)}: {e}")
        try:
            self.proc.wait(timeout=120)
        except subprocess.TimeoutExpired:
            self.run("quit", "--force", timeout=120)
            try:
                self.proc.wait(timeout=60)
            except subprocess.TimeoutExpired:
                os.killpg(self.proc.pid, 9)
        log(f"core exited {self.proc.returncode}")
        self.proc = None


def trim(status):
    status = status or {}
    return {"engine": status.get("engine"), "connect": status.get("connect"), "runs": status.get("runs")}


def resolved_lanes(et, key):
    rc, data, err = et.gql(RESOLVED_Q, timeout=600)
    for r in (((data or {}).get("settings") or {}).get("resolvedModelSettings") or []) if rc == 0 else []:
        if r.get("model") == key:
            return ((r.get("effective") or {}).get("config") or {}).get("maxConcurrentRequests") or 2
    return 2


def tail(p, n=40):
    try:
        return "\n".join(pathlib.Path(p).read_text(errors="replace").splitlines()[-n:])
    except OSError:
        return ""


def run_logged(cmd, logfile, env=None, timeout=None):
    t = time.monotonic()
    with open(logfile, "ab") as f:
        f.write(("$ " + " ".join(map(str, cmd)) + "\n").encode())
        f.flush()
        p = subprocess.Popen([str(c) for c in cmd], env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                             stdin=subprocess.DEVNULL, start_new_session=True)
        fired = threading.Event()

        def kill():
            fired.set()
            try:
                os.killpg(p.pid, 9)
            except OSError:
                pass

        timer = threading.Timer(timeout, kill) if timeout else None
        if timer:
            timer.start()
        try:
            for line in p.stdout:
                f.write(line)
                f.flush()
                if b"\r" not in line:
                    sys.stdout.write(line.decode(errors="replace"))
                    sys.stdout.flush()
            p.wait()
        finally:
            if timer:
                timer.cancel()
    return (-9 if fired.is_set() else p.returncode), time.monotonic() - t


def convert(pie, src, dst, sku, scratch, logfile):
    scratch = pathlib.Path(scratch)
    shutil.rmtree(scratch, ignore_errors=True)
    (scratch / "tmp").mkdir(parents=True)
    os.chmod(scratch, 0o700)
    env = {"PATH": SYS_PATH, "HOME": str(scratch), "PIE_HOME": str(scratch), "TMPDIR": str(scratch / "tmp"),
           "LANG": "C", "LC_ALL": "C"}
    rc, dt = run_logged([pie, "model", "import", src, "--out", dst, "--keep-source", "--deployment", sku], logfile,
                        env=env, timeout=5400)
    shutil.rmtree(scratch, ignore_errors=True)
    if rc != 0 or not pathlib.Path(dst).is_file():
        raise RuntimeError(f"pie model import {sku} failed rc {rc}: {tail(logfile)}")
    return {"sku": sku, "seconds": round(dt, 1), "bytes": pathlib.Path(dst).stat().st_size}


def post(base, key, body, timeout=900):
    r = httpx.post(base.rstrip("/") + "/chat/completions", content=json.dumps(body, ensure_ascii=False).encode(),
                   headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"}, timeout=timeout)
    if r.status_code != 200:
        raise RuntimeError(f"HTTP {r.status_code}: {r.text[:800]}")
    return r.json()


def speed_probe(base, key, model):
    body = {"model": model, "messages": [{"role": "user", "content": "Explain in detail, in about 500 words, how a "
                                          "hash table handles collisions."}],
            "max_tokens": 320, "temperature": 0, "enable_thinking": False, "stream": True,
            "stream_options": {"include_usage": True}}
    t0 = time.monotonic()
    first = last = None
    usage = {}
    with httpx.stream("POST", base.rstrip("/") + "/chat/completions", content=json.dumps(body).encode(),
                      headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                      timeout=900) as r:
        if r.status_code != 200:
            raise RuntimeError(f"HTTP {r.status_code}: {r.read()[:500]}")
        for line in r.iter_lines():
            if not line.startswith("data:"):
                continue
            d = line[5:].strip()
            if d == "[DONE]":
                break
            obj = json.loads(d)
            for c in obj.get("choices") or []:
                delta = c.get("delta") or {}
                if delta.get("content") or delta.get("reasoning_content"):
                    now = time.monotonic()
                    first = first or now
                    last = now
            if obj.get("usage"):
                usage = obj["usage"]
    n = int(usage.get("completion_tokens") or 0)
    return {"ttft_s": round(first - t0, 3) if first else None, "completion_tokens": n,
            "prompt_tokens": usage.get("prompt_tokens"),
            "decode_tok_s": round((n - 1) / (last - first), 1) if first and last and last > first and n > 1 else None}


def parity(base, key, model, tok, episodes, first):
    from pieswarm.tasks import Episode
    from pieswarm.team.client import text_messages

    cases = []
    ep = Episode("codeteam", 3, TEST_OFFSET, budget_tokens=1024, chunk_tokens=1024, lam=0.25, interfaces="given",
                 hint=1)
    for a in range(3 if first else 0):
        cases.append((f"seed {TEST_OFFSET} agent {a} turn 1", ep.shared_prompt() + ep.private_prompt(a)))
    for r in [] if first else episodes[:4]:
        for a, segs in enumerate(r.get("transcript") or []):
            idx = [i for i, s in enumerate(segs) if s["kind"] == "inject" and s["text"].endswith(ASSISTANT_OPEN)]
            if not idx:
                continue
            k = idx[-1]
            ctx = "".join(s["text"] for s in segs[:k + 1])
            turns = 1 + sum(1 for s in segs[:k + 1] if s["kind"] == "gen")
            cases.append((f"seed {r['seed']} attempt {r['attempt']} agent {a} turn {turns}", ctx))
    rows = []
    for name, ctx in cases:
        want = len(tok.encode(ctx, add_special_tokens=False).ids)
        try:
            resp = post(base, key, {"model": model, "messages": text_messages(ctx), "max_tokens": 1,
                                    "temperature": 0, "stop": ["</tool_call>"], "enable_thinking": False,
                                    "stream": False})
            got = (resp.get("usage") or {}).get("prompt_tokens")
            rows.append({"case": name, "training_tokens": want, "etude_prompt_tokens": got, "match": got == want,
                         "messages": len(text_messages(ctx))})
        except Exception as e:
            rows.append({"case": name, "training_tokens": want, "error": str(e)[:300]})
    if not first:
        return rows, None
    ctx0 = ep.shared_prompt() + ep.private_prompt(0)
    try:
        resp = post(base, key, {"model": model, "messages": text_messages(ctx0), "max_tokens": 400, "temperature": 0,
                                "stop": ["</tool_call>"], "enable_thinking": False, "stream": False})
        ch = (resp.get("choices") or [{}])[0]
        msg = ch.get("message") or {}
        sample = {"finish_reason": ch.get("finish_reason"), "content": (msg.get("content") or "")[:1500],
                  "tool_calls": msg.get("tool_calls"), "reasoning": (msg.get("reasoning_content") or "")[:300],
                  "usage": resp.get("usage")}
    except Exception as e:
        sample = {"error": str(e)[:500]}
    return rows, sample


def load_jsonl(p):
    p = pathlib.Path(p)
    if not p.is_file():
        return []
    return [json.loads(x) for x in p.read_text().splitlines() if x.strip()]


def wilson(k, n, z=1.96):
    if n == 0:
        return [0.0, 0.0]
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [round(max(0.0, c - h), 4), round(min(1.0, c + h), 4)]


def score(episodes):
    from pieswarm.demo.scoring import missing_teammate_import
    from pieswarm.scoring.codeteam import coordination_metrics, score_episode

    py = os.path.realpath(sys.executable)

    def one(r):
        res = r.get("result") or {}
        if not res.get("codeteam"):
            return None, None, None
        return score_episode(res, python=py), coordination_metrics(res), missing_teammate_import(res)

    with cf.ThreadPoolExecutor(8) as ex:
        scored = list(ex.map(one, episodes))
    n = len(episodes)
    rows = []
    for r, (s, c, miss) in zip(episodes, scored):
        res = r.get("result") or {}
        rows.append({"seed": r.get("seed"), "attempt": r.get("attempt"), "error": r.get("error"),
                     "all_pass": bool(s and s["success"]), "pass_frac": round(s["score"], 4) if s else 0.0,
                     "failure": (s or {}).get("details", {}).get("failure"),
                     "tokens": sum(res.get("tokens") or []), "messages": (c or {}).get("messages"),
                     "missing_import": miss, "names_match": (c or {}).get("names_match"),
                     "wall_s": (r.get("timing") or {}).get("wall_s"), "end_reason": res.get("end_reason")})
    k = sum(x["all_pass"] for x in rows)
    known_miss = [x["missing_import"] for x in rows if x["missing_import"] is not None]
    out = {"episodes": n, "errors": sum(1 for x in rows if x["error"]), "all_pass": round(k / n, 4) if n else 0.0,
           "all_pass_k": k, "all_pass_ci95": wilson(k, n),
           "pass_frac": round(sum(x["pass_frac"] for x in rows) / n, 4) if n else 0.0,
           "tokens_per_episode": round(sum(x["tokens"] for x in rows) / n) if n else 0,
           "messages_per_episode": round(sum(x["messages"] or 0 for x in rows) / n, 1) if n else 0,
           "missing_import_rate": round(sum(known_miss) / len(known_miss), 3) if known_miss else None,
           "wall_per_episode_s": round(sum(x["wall_s"] or 0 for x in rows) / n, 1) if n else 0,
           "failures": {}, "per_problem": {}}
    for x in rows:
        if not x["all_pass"]:
            f = x["failure"] or ("driver_error" if x["error"] else "unknown")
            out["failures"][f] = out["failures"].get(f, 0) + 1
        out["per_problem"].setdefault(str(x["seed"]), []).append(int(x["all_pass"]))
    out["per_problem"] = {s: f"{sum(v)}/{len(v)}" for s, v in sorted(out["per_problem"].items())}
    return out, rows


def chunk_pack(work, pack, c, offset, groups, attempts):
    d = pathlib.Path(work) / f"pack-{c}"
    shutil.rmtree(d, ignore_errors=True)
    d.mkdir()
    team = yaml.safe_load((pack / "team.yaml").read_text())
    team["eval"] = dict(team.get("eval") or {}, seeds_offset=offset, groups=groups, attempts=attempts)
    (d / "team.yaml").write_text(yaml.safe_dump(team, sort_keys=False, allow_unicode=True, width=110))
    for name in ("adapter", "model"):
        (d / name).symlink_to((pack / name).resolve())
    return d


def eval_arm(a, arm, base, key_file, model, conc, chunks, budget_s, venv):
    out = pathlib.Path(a.out)
    pack = pathlib.Path(a.work) / "pack"
    per = a.problems // a.chunks
    eps, summaries, done = [], [], []
    t = time.monotonic()
    for c in chunks:
        left = budget_s - (time.monotonic() - t)
        if left < 300:
            log(f"{arm}: budget left {left:.0f}s, skipping chunk {c}")
            break
        d = chunk_pack(a.work, pack, c, TEST_OFFSET + c * per, per, a.attempts)
        tag = f"{arm}-c{c}"
        cmd = [pathlib.Path(venv) / "bin" / "pieswarm", "team", "eval", d, "--base-url", base, "--api-key-file",
               key_file, "--model", model, "--mode", "text", "--concurrency", conc, "--max-wall-s", 1800,
               "--label", tag, "--out", out / f"{tag}.jsonl", "--json", out / f"{tag}.json"]
        log(f"{arm}: chunk {c} (seeds {TEST_OFFSET + c * per}..{TEST_OFFSET + (c + 1) * per - 1}) x{a.attempts}, "
            f"concurrency {conc}")
        rc, dt = run_logged(cmd, out / f"{arm}-eval.log", env=dict(os.environ), timeout=left)
        part = load_jsonl(out / f"{tag}.jsonl")
        js = out / f"{tag}.json"
        if rc != 0 or not part:
            log(f"{arm}: chunk {c} rc {rc} after {dt:.0f}s, {len(part)} episodes")
            if not part:
                break
        eps += part
        if js.is_file():
            summaries.append(json.loads(js.read_text()))
        done.append(c)
    return eps, summaries, done


def merge_summaries(ss):
    if not ss:
        return {}
    wall = sum(s["wall_s"] for s in ss)
    srv = sum(s["server_tokens_per_episode"] * s["episodes"] for s in ss)
    reqs = sum(s["requests_per_episode"] * s["episodes"] for s in ss)
    lat = sum(s["mean_latency_s"] * s["requests_per_episode"] * s["episodes"] for s in ss)
    refused = {}
    for s in ss:
        for k, v in (s.get("refused_extras") or {}).items():
            refused.setdefault(k, sorted(set(refused.get(k, [])) | set(v)))
    return {"wall_s": round(wall, 1), "server_completion_tokens": round(srv),
            "gen_tokens_per_s": round(srv / wall, 1) if wall else 0.0,
            "per_request_tok_s": round(srv / lat, 1) if lat else 0.0,
            "mean_latency_s": round(lat / reqs, 2) if reqs else 0.0,
            "requests_per_episode": round(reqs / sum(s["episodes"] for s in ss), 1),
            "driver_errors": sum(s["errors"] for s in ss), "refused_extras": refused,
            "first_error": next((s.get("first_error") for s in ss if s.get("first_error")), None),
            "mode": ss[0].get("mode"), "end_reasons": [s.get("end_reasons") for s in ss]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--app", required=True)
    ap.add_argument("--work", required=True)
    ap.add_argument("--home", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--assets", required=True)
    ap.add_argument("--venv", required=True)
    ap.add_argument("--problems", type=int, default=16)
    ap.add_argument("--attempts", type=int, default=2)
    ap.add_argument("--chunks", type=int, default=2)
    ap.add_argument("--lanes", type=int, default=12)
    ap.add_argument("--context", type=int, default=16384)
    ap.add_argument("--quant", default="true")
    ap.add_argument("--arm-budget-min", type=float, default=110)
    ap.add_argument("--quant-deadline-min", type=float, default=230)
    a = ap.parse_args()
    work, out, assets = pathlib.Path(a.work), pathlib.Path(a.out), pathlib.Path(a.assets)
    out.mkdir(parents=True, exist_ok=True)
    quant = a.quant.lower() == "true"
    report = {"started": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
              "machine": {"chip": sh("sysctl -n machdep.cpu.brand_string"),
                          "memory_gib": round(int(sh("sysctl -n hw.memsize") or 0) / 2**30),
                          "macos": sh("sw_vers -productVersion"), "python": platform.python_version(),
                          "disk_free_gib": round(shutil.disk_usage(work).free / 2**30)},
              "app": {"version": sh(f"/usr/libexec/PlistBuddy -c 'Print :CFBundleShortVersionString' "
                                    f"'{a.app}/Contents/Info.plist'"),
                      "build": sh(f"/usr/libexec/PlistBuddy -c 'Print :CFBundleVersion' '{a.app}/Contents/Info.plist'")},
              "config": {"problems": a.problems, "attempts": a.attempts, "chunks": a.chunks, "lanes": a.lanes,
                         "context": a.context, "quant": quant, "test_seeds_offset": TEST_OFFSET},
              "timings": {}, "arms": {}}

    def save():
        (out / "report.json").write_text(json.dumps(report, indent=1))

    et = Etude(a.app, a.home, out)
    report["app"]["cli"] = str(et.bin)
    try:
        from huggingface_hub import snapshot_download
        from tokenizers import Tokenizer

        from pieswarm.export.merge import merge_adapter

        t = time.monotonic()
        hf_dir = pathlib.Path(snapshot_download("Qwen/Qwen3-8B", revision=REV, local_dir=str(work / "hf-base"),
                                                allow_patterns=["*.json", "*.safetensors", "*.txt", "LICENSE*"]))
        report["timings"]["download_base_s"] = round(time.monotonic() - t, 1)
        base_dir = work / "Qwen3-8B"
        base_dir.mkdir(exist_ok=True)
        for f in hf_dir.iterdir():
            if f.is_file() and not f.name.startswith("."):
                os.link(f, base_dir / f.name)
        log(f"base downloaded: {sum(p.stat().st_size for p in base_dir.glob('*.safetensors')) / 1e9:.2f} GB")

        pack = work / "pack"
        (pack / "adapter").mkdir(parents=True, exist_ok=True)
        shutil.copyfile(assets / "team.yaml", pack / "team.yaml")
        for f in ("adapter_model.safetensors", "adapter_config.json"):
            shutil.copyfile(assets / f, pack / "adapter" / f)
        t = time.monotonic()
        info = merge_adapter(base_dir, pack / "adapter", work / "trained-team-8b")
        report["timings"]["merge_s"] = round(time.monotonic() - t, 1)
        report["merge"] = info
        log(f"merged: {json.dumps(info)}")
        (pack / "model").symlink_to(work / "trained-team-8b")
        tok = Tokenizer.from_file(str(work / "trained-team-8b" / "tokenizer.json"))
        save()

        zt = work / "zt"
        zt.mkdir(exist_ok=True)
        jobs = [("trained-bf16", work / "trained-team-8b", zt / "trained-team-8b.zt", "qwen3-8b-bf16-kv-bf16"),
                ("base-bf16", base_dir, zt / "qwen3-8b-base.zt", "qwen3-8b-bf16-kv-bf16")]
        if quant:
            jobs.append(("trained-u4g64", work / "trained-team-8b", zt / "trained-team-8b-u4g64.zt",
                         "qwen3-8b-u4g64-kv-bf16"))
        report["convert"] = {}
        for arm, src, dst, sku in jobs:
            try:
                report["convert"][arm] = convert(et.pie, src, dst, sku, work / f"pie-{arm}", out / "convert.log")
                log(f"converted {arm}: {json.dumps(report['convert'][arm])}")
            except Exception as e:
                report["convert"][arm] = {"error": str(e)[:3000]}
                log(f"convert {arm} failed: {e}")
            save()

        try:
            report["core_start"] = trim(et.start(seed_settings=True))
        except Exception as e:
            log(f"core start with seeded settings failed: {e}; retrying with defaults")
            et.stop()
            report["core_start"] = trim(et.start(seed_settings=False))
            rc, data, err = et.gql(SETTINGS_M, patch={"port": {"mode": "AUTOMATIC"}})
            log(f"port automatic: rc {rc} {data} {err[:300]}")
        log(f"core up: engine {json.dumps((report['core_start'] or {}).get('engine'))[:300]}")
        keys = {}
        report["imports"] = {}
        for arm, src, dst, sku in jobs:
            if not dst.is_file():
                continue
            try:
                k, m, dt = et.import_model(dst)
                keys[arm] = k
                report["imports"][arm] = {"key": k, "name": m.get("name"), "seconds": round(dt, 1), "path": m.get("path")}
                log(f"imported {arm}: {k} in {dt:.0f}s")
                dst.unlink()
            except Exception as e:
                report["imports"][arm] = {"error": str(e)[:3000]}
                log(f"import {arm} failed: {e}")
            save()
        rows = [dict(SAMPLING, model=k, contextTokens=a.context, requestTokens=a.context,
                     maxConcurrentRequests=a.lanes) for k in keys.values()]
        rc, data, err = et.gql(SETTINGS_M, patch={"modelSettings": rows})
        report["settings"] = {"requested": rows, "rc": rc, "result": data, "stderr": err[:1000]}
        log(f"setSettings: rc {rc} {json.dumps(data)[:400]} {err[:400]}")
        if rc != 0 or "Ack" not in json.dumps(data):
            rows = [{"model": k, "contextTokens": a.context, "requestTokens": a.context} for k in keys.values()]
            rc, data, err = et.gql(SETTINGS_M, patch={"modelSettings": rows})
            report["settings"]["fallback"] = {"requested": rows, "rc": rc, "result": data, "stderr": err[:1000]}
            log(f"setSettings without lanes and sampling: rc {rc} {json.dumps(data)[:400]} {err[:400]}")
        if rc != 0 or "Ack" not in json.dumps(data):
            rows = [{"model": k, "contextTokens": 40960, "requestTokens": a.context} for k in keys.values()]
            rc, data, err = et.gql(SETTINGS_M, patch={"modelSettings": rows})
            report["settings"]["fallback2"] = {"requested": rows, "rc": rc, "result": data, "stderr": err[:1000]}
            log(f"setSettings native context: rc {rc} {json.dumps(data)[:400]} {err[:400]}")
        rc, data, err = et.gql(RESOLVED_Q, timeout=600)
        report["settings"]["resolved"] = data if rc == 0 else err[:2000]
        save()

        chunks = list(range(a.chunks))
        order = [x for x in ("trained-bf16", "base-bf16", "trained-u4g64") if x in keys]
        for i, arm in enumerate(order):
            if arm == "trained-u4g64" and minutes() > a.quant_deadline_min:
                report["arms"][arm] = {"skipped": f"time: {minutes():.0f} min elapsed"}
                continue
            key = keys[arm]
            entry = report["arms"].setdefault(arm, {"key": key})
            try:
                if i:
                    rc, data, err = et.run("down", timeout=600)
                    log(f"etude down: rc {rc} {json.dumps(data)[:200]} {err[:200]}")
                t = time.monotonic()
                r = et.cli("up", "--model", key, timeout=3000)
                entry["boot_s"] = round(time.monotonic() - t, 1)
                eng = (r or {}).get("engine") or {}
                if eng.get("phase") != "READY" or (eng.get("model") or {}).get("key") != key:
                    raise RuntimeError(f"up: {json.dumps(r)[:1500]}")
                rc, data, err = et.gql(ENGINE_Q)
                entry["engine"] = data if rc == 0 else err[:1500]
                applied = ((data or {}).get("engine") or {}).get("appliedModelSettings") or {}
                lanes = int(((applied.get("config") or {}).get("maxConcurrentRequests")) or resolved_lanes(et, key))
                entry["lanes"] = lanes
                conc = max(1, lanes // 2)
                entry["concurrency"] = conc
                con = et.cli("connect")
                base, key_file = con["base_url"], con["key_file"]
                api_key = pathlib.Path(key_file).read_text().strip()
                log(f"{arm}: READY in {entry['boot_s']}s, lanes {lanes}, concurrency {conc}, {base}")
                t = time.monotonic()
                post(base, api_key, {"model": key, "messages": [{"role": "user", "content": "Say ok."}],
                                     "max_tokens": 8, "temperature": 0, "enable_thinking": False})
                entry["first_request_s"] = round(time.monotonic() - t, 1)
                entry["speed_probe"] = speed_probe(base, api_key, key)
                log(f"{arm}: first request {entry['first_request_s']}s, probe {entry['speed_probe']}")
                entry["parity"], entry["sample"] = parity(base, api_key, key, tok, [], first=True)
                log(f"{arm}: first-turn parity {json.dumps(entry['parity'])}")
                log(f"{arm}: greedy sample {json.dumps(entry['sample'])[:1500]}")
                budget = a.arm_budget_min * 60 if arm != "trained-u4g64" else max(
                    600, min(a.arm_budget_min, a.quant_deadline_min + 90 - minutes()) * 60)
                arm_chunks = chunks if arm == "trained-bf16" else report["arms"].get("trained-bf16", {}).get(
                    "chunks_done", chunks)
                eps, summaries, done = eval_arm(a, arm, base, key_file, key, conc, arm_chunks, budget, a.venv)
                entry["chunks_done"] = done
                entry["driver"] = merge_summaries(summaries)
                save()
                try:
                    entry["score"], rows_ = score(eps)
                    (out / f"{arm}-scored.json").write_text(json.dumps(rows_, indent=1))
                    log(f"{arm}: {json.dumps(entry['score'])[:600]}")
                except Exception as e:
                    entry["score_error"] = str(e)[:2000]
                    log(f"{arm}: scoring failed: {e}")
                try:
                    more, _ = parity(base, api_key, key, tok, eps, first=False)
                    entry["parity"] = entry.get("parity", []) + more
                    log(f"{arm}: parity {json.dumps(more)[:1200]}")
                except Exception as e:
                    entry["parity_error"] = str(e)[:2000]
                    log(f"{arm}: parity failed: {e}")
                rc, data, err = et.gql(USAGE_Q, m=key)
                if rc != 0:
                    rc, data, err = et.gql(USAGE_Q.replace("($m: String)", "").replace(", model: $m", ""))
                entry["etude_usage"] = data if rc == 0 else err[:1500]
                rc, data, err = et.gql(ENGINE_Q)
                entry["engine_after"] = data if rc == 0 else err[:1500]
            except Exception as e:
                entry["error"] = str(e)[:4000]
                log(f"{arm} failed: {e}")
                log(tail(out / "core.log"))
            save()
    finally:
        try:
            et.stop()
        except Exception as e:
            log(f"stop: {e}")
        report["cli_calls"] = et.calls
        report["finished"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        report["minutes"] = round(minutes(), 1)
        save()
        (out / "summary.md").write_text(render(report))
        print(render(report), flush=True)
    ok = report["arms"].get("trained-bf16", {}).get("score") and report["arms"].get("base-bf16", {}).get("score")
    return 0 if ok else 1


def render(rep):
    h100 = {"trained-bf16": (0.352, 0.403, "35.2% +-9.2 (64x4)"), "base-bf16": (0.074, 0.080, "7.4% +-4.3 (64x4)")}
    lines = [f"## Trained 8B coding team in Étude {rep['app'].get('version')} ({rep['app'].get('build')}) on "
             f"{rep['machine'].get('chip')}, {rep['machine'].get('memory_gib')} GB, macOS {rep['machine'].get('macos')}",
             "", f"Test problems {TEST_OFFSET}.., {rep['config']['problems']} x {rep['config']['attempts']} attempts, "
             "pieswarm team eval --mode text, same seeds for every arm.", "",
             "| arm | all tests pass | 95% CI | pass fraction | episodes | driver errors | tokens/ep | gen tok/s (eval, "
             "aggregate) | per request tok/s | single-stream decode tok/s | Étude decode tok/s | Étude prefill tok/s | "
             "lanes x conc | boot s | H100 all-pass / pass frac |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for arm, e in rep.get("arms", {}).items():
        s, d = e.get("score") or {}, e.get("driver") or {}
        u = (((e.get("etude_usage") or {}).get("usage") or {}).get("summary") or {}) if isinstance(
            e.get("etude_usage"), dict) else {}
        hv = h100.get(arm)
        if not s:
            lines.append(f"| {arm} | {e.get('skipped') or ('error: ' + str(e.get('error'))[:120])} |" + " |" * 14)
            continue
        lines.append(
            f"| {arm} | {100 * s['all_pass']:.1f}% ({s['all_pass_k']}/{s['episodes']}) | "
            f"{100 * s['all_pass_ci95'][0]:.0f}-{100 * s['all_pass_ci95'][1]:.0f}% | {s['pass_frac']:.3f} | "
            f"{s['episodes']} | {s['errors']} | {s['tokens_per_episode']} | {d.get('gen_tokens_per_s')} | "
            f"{d.get('per_request_tok_s')} | {(e.get('speed_probe') or {}).get('decode_tok_s')} | "
            f"{u.get('tokensPerSecond')} | {(u.get('prefill') or {}).get('tokensPerSecond')} | "
            f"{e.get('lanes')} x {e.get('concurrency')} | {e.get('boot_s')} | "
            f"{hv[2] + ' / ' + str(hv[1]) if hv else '-'} |")
    lines += ["", "Prompt parity (training token count vs Étude prompt_tokens, text mode):", ""]
    for arm, e in rep.get("arms", {}).items():
        p = e.get("parity") or []
        if p:
            m = sum(1 for x in p if x.get("match"))
            lines.append(f"- {arm}: {m}/{len(p)} match; " + "; ".join(
                f"{x['case']}: {x.get('training_tokens')} vs {x.get('etude_prompt_tokens', x.get('error'))}"
                for x in p[:8]))
    lines += ["", "Timings: " + json.dumps(rep.get("timings")), "Convert: " + json.dumps(rep.get("convert")),
              "Imports: " + json.dumps(rep.get("imports")), f"Total {rep.get('minutes')} min."]
    for arm, e in rep.get("arms", {}).items():
        d = e.get("driver") or {}
        if d.get("refused_extras") or d.get("first_error"):
            lines.append(f"- {arm}: refused extras {d.get('refused_extras')}, first error {d.get('first_error')}")
        if e.get("score"):
            lines.append(f"- {arm}: failures {e['score']['failures']}, missing import {e['score']['missing_import_rate']}, "
                         f"msgs/ep {e['score']['messages_per_episode']}, per problem {e['score']['per_problem']}")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    sys.exit(main())
