"""A profile run's results into the job log, so no artifact needs downloading: each cell's rounds, tokens per
round and decode rate from its bench.json inter-token gaps, and each request's output hash."""
import glob, json, os, sys
root = sys.argv[1]
for path in sorted(glob.glob(os.path.join(root, "**/bench.json"), recursive=True)):
    d = json.load(open(path))
    toks = rounds = 0; dec = 0.0; hashes = []
    for r in d.get("requests", []):
        gaps = r.get("intertoken_us") or []
        toks += len(gaps) + 1; rounds += 1 + sum(g > 3000 for g in gaps); dec += sum(gaps) / 1e6
        hashes.append((r.get("output_token_sha256") or "")[:12])
    n = len(d.get("requests", []))
    if n and dec:
        print(f"{os.path.relpath(path, root)}: {toks} tok, {rounds} rounds, {toks / rounds:.2f} tok/round, "
              f"round {dec / max(rounds - n, 1) * 1e3:.2f} ms, decode {toks / dec:.1f} tok/s, idle "
              f"{d['summary']['config'].get('device idle us', '-')} us")
        print("   hashes " + " ".join(hashes))
        # a speculative program's own counts (pie_bench keeps them per request): rows verified, fire prices
        specs = [r["speculation"] for r in d.get("requests", []) if r.get("speculation")]
        if specs:
            widths = {}
            for s in specs:
                for w in s.get("verify") or []:
                    widths[w] = widths.get(w, 0) + 1
            rounds = sum(s.get("rounds") or 0 for s in specs)
            kept = sum(s.get("accepted") or 0 for s in specs)
            drafted = sum(s.get("drafted") or 0 for s in specs)
            plain = sum(s.get("plain_fires") or 0 for s in specs)
            print(f"   spec: {rounds} drafting rounds, {plain} plain fires, {(kept + rounds) / max(rounds, 1):.2f} "
                  f"tok/drafting round, accepted {kept}/{drafted}, rows " +
                  " ".join(f"{w}:{n}" for w, n in sorted(widths.items())))
            expected = sum(s.get("budget_expected") or 0 for s in specs)
            if expected:
                print(f"   budget: expected {expected / max(rounds, 1):.2f} tok/round, emitted {(kept + rounds) / max(rounds, 1):.2f}; "
                      "last model " + " ".join(f"{t:.2f}" for t in (specs[-1].get("budget_model") or [])))
            print("   last request's prices ms " + " ".join(f"{w}:{p:.2f}" for w, p in (specs[-1].get("prices_ms") or [])))
