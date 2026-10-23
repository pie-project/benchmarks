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
