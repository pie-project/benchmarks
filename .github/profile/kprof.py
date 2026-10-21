"""Per-kernel device time from Pie's Metal `kernel-profile=2` lines in a bench stderr.

    python kprof.py stderr.txt

Each fire prints `kernels: fire of N row(s), T ms on the device:` and then one line per kernel
(`  ms  launches  name`). A fire that runs the DFlash selector walk is a draft; another fire of 2-16 rows
is a verify; anything wider is a prompt. Times are relative: profiling serializes the kernels.
"""
import collections
import re
import sys

HEAD = re.compile(r"kernels: fire of (\d+) row\(s\), ([\d.]+) ms")
LINE = re.compile(r"^\s*([\d.]+) ms\s+(\d+) launch\(es\)\s+(.+?)\s*$")


def family(name):
    n = name.lower()
    for key, label in (("selector", "draft selector"), ("routed", "moe routed"), ("moe", "moe other"),
                       ("gdn", "gdn/linear-attn"), ("delta", "gdn/linear-attn"), ("conv", "gdn/linear-attn"),
                       ("attn", "attention"), ("sdpa", "attention"), ("argmax", "sampling"),
                       ("qmm", "dense qmm"), ("qmv", "dense qmv"), ("norm", "norms"), ("rope", "rope")):
        if key in n:
            return label
    return "other"


def main(path):
    fires = []
    cur = None
    for line in open(path, errors="replace"):
        line = re.sub(r"^\[[^\]]*\]\s*", "", line.rstrip("\n"))  # the bench's timestamp prefix
        m = HEAD.search(line)
        if m:
            cur = {"rows": int(m.group(1)), "ms": float(m.group(2)), "k": []}
            fires.append(cur)
            continue
        m = LINE.match(line)
        if m and cur is not None:
            cur["k"].append((m.group(3), float(m.group(1)), int(m.group(2))))
    for f in fires:
        names = " ".join(n for n, _, _ in f["k"])
        f["kind"] = "draft" if "selector" in names else ("verify" if 2 <= f["rows"] <= 16 else
                                                         "decode1" if f["rows"] == 1 else "prompt")
    by = collections.defaultdict(list)
    for f in fires:
        by[f["kind"]].append(f)
    print(f"{len(fires)} fires: " + ", ".join(f"{k} {len(v)}" for k, v in by.items()))
    for kind in ("draft", "verify", "decode1"):
        fs = by.get(kind, [])
        if not fs:
            continue
        rows = collections.Counter(f["rows"] for f in fs)
        mean = sum(f["ms"] for f in fs) / len(fs)
        print(f"\n== {kind}: {len(fs)} fires, rows {dict(rows)}, mean {mean:.2f} ms (serialized)")
        fam, ker = collections.Counter(), collections.Counter()
        for f in fs:
            for n, ms, _ in f["k"]:
                fam[family(n)] += ms / len(fs)
                ker[n] += ms / len(fs)
        listed = sum(fam.values())
        for k, v in fam.most_common():
            print(f"   {v:7.2f} ms {v / listed:6.1%}  {k}")
        print("   top kernels:")
        for k, v in ker.most_common(12):
            print(f"   {v:7.2f} ms  {k[:110]}")
        watched = [(k, v) for k, v in ker.items() if any(w in k for w in ("rs_copy", "gated_delta", "conv1d", "split_rows"))]
        if watched:
            print("   recurrent-state kernels:")
            for k, v in sorted(watched, key=lambda kv: -kv[1]):
                print(f"   {v:7.3f} ms  {k[:110]}")


if __name__ == "__main__":
    main(sys.argv[1])
