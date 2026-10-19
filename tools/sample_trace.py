"""Write the sample traces the Profiler opens without a file: web/data/traces/sample-*.pie.

    python3 tools/sample_trace.py

A small simulation of Pie serving agents on one Mac, written in the .pie format (docs/pie-trace-format.md).
Each agent loops: its prompt waits in the queue, is prefilled in 512-token chunks, decodes a reply, thinks a
moment, then waits 0.5-2 s on a tool. The scheduler batches every decoding agent into one step and adds at
most one prefill chunk, so a second prompt queues behind the first. KV pages grow with each agent's context
and drop when the scheduler evicts a tool-waiting agent to make room; that agent's next prefill starts cold.
The GPU is idle whenever every agent is thinking or waiting on a tool. Seeded, so the files are stable.
"""
from __future__ import annotations

import json
import math
import random
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "web" / "data" / "traces"

PAGE_TOKENS = 16
KV_PAGE_BYTES = 262144
CHUNK = 512  # prefill tokens per step
WINDOW = 10_000  # µs: the gpu_busy / gpu_share window
STEP_CPU = 300  # µs of scheduling and encoding before the GPU starts a step
STEP_TAIL = 80  # µs after the GPU ends before the next step can start
WEIGHTS_BYTES = 480_000_000
TOOLS = ["search", "read_file", "python", "browse", "grep"]


def gpu_us(prefill_tokens: int, decode_tokens: int) -> int:
    """A step's GPU time: a fixed launch cost, ~0.2 ms per prefill token, ~0.5 ms per decoding agent."""
    return int(7_000 + 200 * prefill_tokens + 500 * decode_tokens)


class Agent:
    def __init__(self, aid: int, kind: str, start: int, turns: int, rng: random.Random):
        self.id = aid
        self.label = f"agent-{aid} ({kind})"
        self.key = f"agent-{aid}"
        self.start = start
        self.rng = rng
        # each turn: the new prompt tokens (task first, then a tool result) and the reply length
        self.turns = [(rng.randint(900, 1800) if i == 0 else rng.randint(150, 900), rng.randint(25, 130)) for i in range(turns)]
        self.turn = 0
        self.length = 0  # tokens in the conversation so far
        self.ctx = 0  # of those, the tokens whose KV is still held
        self.state = "waiting"  # waiting -> ready -> prefill -> decode -> (tool -> ready ...) -> done
        self.ready_at = start
        self.todo = 0  # prefill tokens still to compute, or decode tokens still to produce
        self.cached = 0
        self.spans: list[dict] = []
        self.open: dict | None = None
        self.end: int | None = None

    def pages(self) -> int:
        return math.ceil(self.ctx / PAGE_TOKENS)

    def span(self, name: str, ts: int, end: int, **args):
        """Extend the open span of this phase, or close it and open a new one."""
        if self.open and self.open["name"] == name and self.open["end"] == ts and name != "tool":
            self.open["end"] = end
            for key, value in args.items():
                self.open["args"][key] = self.open["args"].get(key, 0) + value if key == "tokens" else value
            return
        self.close()
        self.open = {"name": name, "ts": ts, "end": end, "args": dict(args)}

    def close(self):
        if self.open and self.open["end"] > self.open["ts"]:
            self.spans.append(self.open)
        self.open = None


def simulate(name: str, agents: list[Agent], kv_pages_total: int, rng: random.Random) -> dict:
    steps, gpus, kv, evicts = [], [], [], []
    t, step = 0, 0
    last_kv = None

    def emit_kv(ts: int):
        nonlocal last_kv
        held = {a.key: a.pages() for a in agents}
        args = {**held, "free": kv_pages_total - sum(held.values())}
        if args != last_kv:
            kv.append({"ph": "C", "name": "kv_pages", "pid": 2, "tid": 1, "ts": ts, "args": args})
            last_kv = args

    emit_kv(0)
    while True:
        for a in agents:
            if a.state in ("waiting", "tool") and a.ready_at <= t:
                a.state = "ready"
                a.length += a.turns[a.turn][0]
                a.cached = a.ctx
                a.todo = a.length - a.ctx  # an evicted agent prefills its whole conversation again
        live = [a for a in agents if a.state != "done"]
        if not live:
            break
        decoding = [a for a in agents if a.state == "decode"]
        prefilling = [a for a in agents if a.state == "prefill"]
        ready = sorted((a for a in agents if a.state == "ready"), key=lambda a: a.ready_at)
        chosen = prefilling[0] if prefilling else (ready[0] if ready else None)
        if not decoding and not chosen:
            # nothing for the GPU: the scheduler sleeps until the next agent comes back
            t = min(a.ready_at for a in live) + rng.randint(100, 300)
            continue

        chunk = min(CHUNK, chosen.todo) if chosen else 0
        need = 0
        if chosen:
            need += math.ceil((chosen.ctx + chunk) / PAGE_TOKENS) - chosen.pages()
        need += sum(math.ceil((a.ctx + 1) / PAGE_TOKENS) - a.pages() for a in decoding)
        free = kv_pages_total - sum(a.pages() for a in agents)
        while need > free:
            # make room: the tool-waiting agent holding the most pages loses them all
            victims = [a for a in agents if a.state in ("tool", "ready") and a.ctx and a is not chosen]
            if not victims:
                break
            victim = max(victims, key=lambda a: a.pages())
            evicts.append({"ph": "i", "s": "t", "name": "evict", "pid": 2, "tid": 1, "ts": t, "args": {"agent": victim.id, "pages": victim.pages()}})
            free += victim.pages()
            victim.ctx = 0
            if victim.state == "ready":
                victim.todo = victim.length
                victim.cached = 0
            emit_kv(t)
        if need > free and chosen and decoding:
            # still no room: the prompt waits until a reply finishes and frees its pages
            need -= math.ceil((chosen.ctx + chunk) / PAGE_TOKENS) - chosen.pages()
            if chosen.state == "ready":
                ready = [a for a in ready if a is not chosen] + [chosen]
            chosen, chunk = None, 0

        gpu = gpu_us(chunk, len(decoding))
        g0 = t + STEP_CPU + rng.randint(0, 120)
        g1 = g0 + gpu
        end = g1 + STEP_TAIL
        step += 1
        per = {}
        if chosen:
            per[str(chosen.id)] = {"prefill": chunk, "decode": 0}
        for a in decoding:
            per.setdefault(str(a.id), {"prefill": 0, "decode": 0})["decode"] += 1
        steps.append({"ph": "X", "name": "step", "pid": 2, "tid": 1, "ts": t, "dur": end - t, "args": {
            "step": step, "prefill_tokens": chunk, "decode_tokens": len(decoding), "agents": per, "gpu_us": gpu}})
        gpus.append({"ph": "X", "name": "gpu", "pid": 2, "tid": 2, "ts": g0, "dur": gpu, "args": {"step": step}})

        def queue(a, until):
            if a.open and a.open["name"] == "queued":
                a.open["end"] = until
            else:
                a.span("queued", a.ready_at, until)

        for a in ready:
            if a is not chosen:
                queue(a, end)
        for a in prefilling:
            if a is not chosen:
                a.span("queued", t, end)  # a prompt part-way through, held back for room
        if chosen:
            if chosen.state == "ready":
                queue(chosen, t)
                chosen.state = "prefill"
                chosen.span("prefill", t, end, tokens=chunk, cached_tokens=chosen.cached)
            else:
                chosen.span("prefill", t, end, tokens=chunk)
            chosen.todo -= chunk
            chosen.ctx += chunk
            if chosen.todo <= 0:
                chosen.state = "decode"
                chosen.todo = chosen.turns[chosen.turn][1]
        for a in decoding:
            a.span("decode", t, end, tokens=1)
            a.ctx += 1
            a.length += 1
            a.todo -= 1
            if a.todo <= 0:
                a.close()
                a.turn += 1
                think = rng.randint(50_000, 300_000)
                if a.turn >= len(a.turns):
                    a.state = "done"
                    a.end = end + think
                    a.ctx = 0
                else:
                    a.state = "tool"
                    wait = rng.randint(500_000, 2_000_000)
                    a.span("tool", end + think, end + think + wait, tool=rng.choice(TOOLS))
                    a.ready_at = end + think + wait + rng.randint(5_000, 40_000)
        emit_kv(end)
        t = end

    for a in agents:
        a.close()
    duration = max(a.end for a in agents) + 20_000
    counters = window_counters(agents, steps, gpus, duration) + memory_counters(gpus, kv_pages_total, duration, rng)

    events = [
        {"ph": "M", "name": "process_name", "pid": 1, "args": {"name": "Agents"}},
        {"ph": "M", "name": "process_name", "pid": 2, "args": {"name": "Engine"}},
        {"ph": "M", "name": "thread_name", "pid": 2, "tid": 1, "args": {"name": "Scheduler"}},
        {"ph": "M", "name": "thread_name", "pid": 2, "tid": 2, "args": {"name": "GPU"}},
    ]
    for a in agents:
        events.append({"ph": "M", "name": "thread_name", "pid": 1, "tid": a.id, "args": {"name": a.label}})
        events.append({"ph": "i", "s": "t", "name": "start", "pid": 1, "tid": a.id, "ts": a.start})
        for s in a.spans:
            events.append({"ph": "X", "name": s["name"], "pid": 1, "tid": a.id, "ts": s["ts"], "dur": s["end"] - s["ts"], "args": s["args"]})
        events.append({"ph": "i", "s": "t", "name": "end", "pid": 1, "tid": a.id, "ts": a.end})
    events += steps + gpus + kv + evicts + counters
    return {
        "format": "pie-trace",
        "version": 1,
        "meta": {
            "pie_version": "0.5.3", "commit": "905e7b531", "started_at": "2026-10-18T12:00:00Z",
            "model": "qwen3.5-0.8b", "scheme": "affine_u4_g64", "device": "metal",
            "hardware": {"name": "Apple M5 Max", "memory_gb": 128, "bandwidth_gbs": 614},
            "kv_page_bytes": KV_PAGE_BYTES, "kv_pages_total": kv_pages_total,
            "weights_bytes": WEIGHTS_BYTES,
            "sample": name,
        },
        "traceEvents": events,
    }


def window_counters(agents, steps, gpus, duration):
    """gpu_busy and gpu_share per 10 ms window, emitted when a value changes."""
    out, last = [], None
    tokens = {s["args"]["step"]: s["args"] for s in steps}
    i = 0
    for w0 in range(0, duration, WINDOW):
        w1 = w0 + WINDOW
        busy, share = 0, {a.key: 0.0 for a in agents}
        while i < len(gpus) and gpus[i]["ts"] + gpus[i]["dur"] <= w0:
            i += 1
        j = i
        while j < len(gpus) and gpus[j]["ts"] < w1:
            g = gpus[j]
            overlap = min(w1, g["ts"] + g["dur"]) - max(w0, g["ts"])
            if overlap > 0:
                busy += overlap
                args = tokens[g["args"]["step"]]
                total = args["prefill_tokens"] + args["decode_tokens"]
                for aid, n in args["agents"].items():
                    share[f"agent-{aid}"] += overlap * (n["prefill"] + n["decode"]) / total
            j += 1
        pct = round(100 * busy / WINDOW, 1)
        shares = {k: round(100 * v / WINDOW, 1) for k, v in share.items()}
        if (pct, shares) != last:
            out.append({"ph": "C", "name": "gpu_busy", "pid": 2, "tid": 1, "ts": w1, "args": {"pct": pct}})
            out.append({"ph": "C", "name": "gpu_share", "pid": 2, "tid": 1, "ts": w1, "args": shares})
            last = (pct, shares)
    return out


def memory_counters(gpus, kv_pages_total, duration, rng):
    """Device memory every 100 ms: the weights, the KV pool, and scratch while the GPU works."""
    out, last, i = [], None, 0
    base = WEIGHTS_BYTES + kv_pages_total * KV_PAGE_BYTES
    for ts in range(0, duration, 100_000):
        while i < len(gpus) and gpus[i]["ts"] + gpus[i]["dur"] < ts - 100_000:
            i += 1
        busy = i < len(gpus) and gpus[i]["ts"] < ts
        gb = round((base + (rng.randint(90, 160) * 1_000_000 if busy else 24_000_000)) / 1e9, 2)
        if gb != last:
            out.append({"ph": "C", "name": "memory", "pid": 2, "tid": 1, "ts": ts, "args": {"allocated_gb": gb}})
            last = gb
    return out


def write(path: Path, trace: dict):
    events = ",\n".join(json.dumps(e, separators=(",", ":")) for e in trace["traceEvents"])
    head = {k: v for k, v in trace.items() if k != "traceEvents"}
    text = json.dumps(head, indent=2)[:-2] + ',\n  "traceEvents": [\n' + events + "\n  ]\n}\n"
    json.loads(text)  # still one valid JSON object
    path.write_text(text)
    print(f"{path.relative_to(OUT.parents[2])}: {len(trace['traceEvents'])} events, {len(text) // 1024} KB")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rng = random.Random(7)
    write(OUT / "sample-1-agent.pie", simulate("1 agent", [Agent(1, "react", 40_000, 6, rng)], 1024, rng))
    rng = random.Random(11)
    agents = [Agent(1, "react", 40_000, 8, rng), Agent(2, "coder", 450_000, 7, rng), Agent(3, "research", 1_100_000, 8, rng)]
    write(OUT / "sample-3-agents.pie", simulate("3 agents", agents, 704, rng))


if __name__ == "__main__":
    main()
