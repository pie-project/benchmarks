"""What is still missing from a device evaluation (matrix/device-eval.yaml) on one platform.

Reads the site's data (web/data/db.js, a local path or the published URL https://data.pie-project.org/db.js) and prints, for each representative
model: which variant was measured (full or miniature), every engine x setup cell, and the pie-vs-vLLM quality
check. Exit status 0 only when every cell is done: a number, or a declared reason the engine cannot run it.

    python tools/device_coverage.py --platform l40s-x1 --tag 0.5.3-b5
    python tools/device_coverage.py --platform l40s-x1 --tag 0.5.3-b5 --db https://data.pie-project.org/db.js
    python tools/device_coverage.py --platform l40s-x1 --tag 0.5.3-b5 --json   # machine-readable, for an agent loop
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent


def load_db(src: str) -> dict:
    text = urllib.request.urlopen(src).read().decode() if src.startswith("http") else Path(src).read_text()
    return json.loads(text[text.index("{"): text.rindex("}") + 1])


def tag_rows(src: str, db: dict, tag: str) -> list[dict]:
    """The tag's rows: in db.js, or in the tags/<tag>.json beside it (tools/split_db.py)."""
    if tag in db["snapshots"]:
        return db["snapshots"][tag]
    split = src.rsplit("/", 1)[0] + f"/tags/{tag}.json"
    try:
        text = urllib.request.urlopen(split).read().decode() if split.startswith("http") else Path(split).read_text()
    except (OSError, ValueError):
        return []
    return json.loads(text).get("snapshots", [])


def parity_unsupported(artifact: str | None, platform: str) -> str | None:
    """The support.yaml reason vLLM cannot be pie's parity reference for this artifact here, or None. A rule
    that names a workload, a tp or a program other than parity speaks for something else."""
    arts = {a["id"]: a for a in yaml.safe_load((ROOT / "matrix/models.yaml").read_text())["artifacts"]}
    plats = {p["id"]: p for p in yaml.safe_load((ROOT / "matrix/platforms.yaml").read_text())["platforms"]}
    a, p = arts.get(artifact or ""), plats.get(platform, {})
    if a is None:
        return None
    have = {"engine": "vllm", "program": "parity", "artifact": a["id"], "family": a.get("family"),
            "scheme": a.get("scheme"), "artifact_kind": a.get("kind", "full"), "platform": platform,
            "arch": p.get("arch"), "backend": p.get("backend"), "os": p.get("os")}
    for rule in yaml.safe_load((ROOT / "matrix/support.yaml").read_text()).get("unsupported", []):
        when = rule["when"]
        if when.get("engine") != "vllm" or any(k.removeprefix("not_") not in have for k in when):
            continue
        if all((have[k[4:]] not in v if isinstance(v, list) else have[k[4:]] != v) if k.startswith("not_")
               else (have[k] in v if isinstance(v, list) else have[k] == v) for k, v in when.items()):
            return rule["reason"]
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--platform", required=True, help="platform id, e.g. l40s-x1")
    ap.add_argument("--tag", required=True, help="the run's tag on the site, e.g. 0.5.3-b5")
    ap.add_argument("--db", default=str(ROOT / "web/data/db.js"))
    ap.add_argument("--spec", default=str(ROOT / "matrix/device-eval.yaml"))
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    spec = yaml.safe_load(Path(a.spec).read_text())
    db = load_db(a.db)
    # a stale row is an older tag's cell the site shows in a gap: it is not this run's measurement
    rows = [r for r in tag_rows(a.db, db, a.tag) if r["hardware"] == a.platform and not r.get("stale")]
    parity = [q for q in db.get("quality_parity", []) if q.get("platform") == a.platform and q.get("tag") == a.tag]
    qspec = spec["quality"]
    from pie_evals.quality.kl import DECISIVE
    assert qspec["decisive_margin"] == DECISIVE, "matrix/device-eval.yaml decisive_margin must match quality/kl.py DECISIVE"

    report, gaps = [], 0
    for m in spec["models"]:
        candidates = [m["model"], *m.get("alternates", [])]
        # the variant measured: the first candidate with any row for this platform and tag
        variant = next((c for c in candidates if any(r["model"] == c for r in rows)), None)
        mini = variant is not None and any(r["model"] == variant and r.get("miniature") for r in rows)
        cells = {}
        for engine in spec["engines"]:
            for s in spec["setups"]:
                hit = [r for r in rows if r["model"] == variant and r["engine"] == engine and r["workload"] == s["workload"]]
                ok = [r for r in hit if r["status"] == "pass" and r.get(s["metric"])]
                unsup = [r for r in hit if r["status"] == "unsupported"]
                if ok:
                    cells[f"{engine}/{s['id']}"] = {"status": "pass", "value": max(r[s["metric"]] for r in ok)}
                elif unsup:
                    cells[f"{engine}/{s['id']}"] = {"status": "unsupported", "why": unsup[0].get("note", "")}
                else:
                    why = next((r.get("note", "") for r in hit), "")
                    cells[f"{engine}/{s['id']}"] = {"status": hit[0]["status"] if hit else "missing", "why": why}
        q = [p for p in parity if p.get("model") == variant]
        if not q:
            quality = {"status": "missing"}
        else:
            # the newest run of the variant: an earlier artifact's row (a retired miniature) can sit later in the list
            p = max(q, key=lambda r: str(r.get("date") or ""))
            kl, top1 = p.get("kl_mean"), p.get("top1_agree_decisive" if p.get("miniature") else "top1_agree")
            declared = parity_unsupported(p.get("artifact"), a.platform) if p.get("ref_unsupported") and p.get("pie_ok") in (True, "True") else None
            if declared:
                quality = {"status": "unsupported", "why": f"{p.get('ref_engine', 'reference')}: {declared}"}
            elif p.get("ref_unsupported"):
                quality = {"status": "fail", "why": f"{p.get('ref_engine', 'reference')}: {p['ref_unsupported']}"}
            # a miniature cut so short its reference never leads by the decisive margin (gemma-4-31b's 18 of 60
            # layers: the top-1 holds 0.14% of the mass) has no top-1 to gate on; its KL still decides
            elif kl is None or (top1 is None and not (p.get("miniature") and p.get("positions") and p.get("decisive_positions") == 0)):
                quality = {"status": "fail", "why": "no positions compared (pie did not load or produced no tokens)"}
            elif kl > max(qspec["max_kl"], 2 * qspec.get("ref_self_kl", {}).get(m["model"], 0.0)) or (top1 is not None and top1 < qspec["min_top1"] and m["model"] not in qspec.get("kl_only", [])):
                quality = {"status": "anomaly", "kl": kl, "top1": top1}
            else:
                quality = {"status": "pass", "kl": kl, "top1": top1}
        done = variant is not None and all(c["status"] in ("pass", "unsupported") for c in cells.values()) and quality["status"] in ("pass", "unsupported")
        gaps += 0 if done else 1
        report.append({"n": m["n"], "model": m["model"], "variant": variant, "miniature": mini, "cells": cells,
                       "quality": quality, "done": done})

    if a.json:
        print(json.dumps({"platform": a.platform, "tag": a.tag, "complete": gaps == 0, "models": report}, indent=1))
        return 0 if gaps == 0 else 1
    short = {"pass": "ok", "unsupported": "n/a", "missing": "--", "fail": "FAIL", "noisy": "noisy", "anomaly": "ANOM"}
    heads = [f"{e}/{s['id']}" for e in spec["engines"] for s in spec["setups"]]
    print(f"{a.platform} @ {a.tag}: {len(report) - gaps} of {len(report)} models complete")
    print("  #  model                          variant                       " + " ".join(h.split("/")[0][:2] + h.split("/")[1][0] + h.split("_")[-1][0] for h in heads) + "  quality")
    for r in report:
        marks = " ".join(f"{short.get(r['cells'][h]['status'], '?'):>4}" for h in heads)
        name = (r["variant"] or "-") + (" (mini)" if r["miniature"] else "")
        print(f"{r['n']:>3}  {r['model'][:30]:30} {name[:29]:29} {marks}  {short.get(r['quality']['status'], '?')}")
    for r in report:
        for h, c in r["cells"].items():
            if c["status"] not in ("pass",) and c.get("why"):
                print(f"  {r['model']} {h}: {c['status']}: {c['why'][:160]}")
        if r["quality"]["status"] not in ("pass",):
            print(f"  {r['model']} quality: {r['quality']}")
    return 0 if gaps == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
