"""Keep one open pie issue per platform listing the Outliers card's red dots.

The site works out its outliers in the browser (Pie.board.outliers, in pie-project/website's public/benchmarks); this
loads the published page on the built data in headless Chrome, asks it for them, and writes each platform's issue on
pie-project/pie ("[NVIDIA] Benchmarks", labelled benchmarks): opened once, then only its description edited, and only
when the list changes. Run after the data is built, on the folder data.pie-project.org serves:

    python tools/outlier_issues.py site
"""

from __future__ import annotations

import functools
import http.server
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import urllib.request
from pathlib import Path

REPO = "pie-project/pie"
LABEL = "benchmarks"
SITE = "https://benchmarks.pie-project.org"
PAGE = "https://pie-project.org/benchmarks"  # the page itself, in pie-project/website
# every platform has its issue, those without data yet too, so reports have a home the day they arrive
PLATFORMS = {"mac": "Apple", "nvidia": "NVIDIA", "amd": "AMD", "tpu": "TPU", "android": "Mobile", "web": "WebGPU", "cerebras": "Cerebras"}
SETUPS = ["Single Decode", "Single Prefill", "Batched Decode", "Batched Prefill"]
WORKLOADS = {"raw": "Single Decode and Prefill", "raw_decode": "Single Decode", "raw_prefill": "Single Prefill", "spec": "Speculative Decode",
             "spec_decode": "Speculative Decode", "throughput": "Batched Decode", "prefill_batch": "Batched Prefill"}
CHROME = os.environ.get("CHROME", "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")

# the page that asks the site for its outliers once the data has loaded, the names it shows beside them
HARNESS = """<!doctype html><body><iframe id="f" src="index.html" style="width:1400px;height:900px"></iframe><pre id="out"></pre>
<script>
const f = document.getElementById("f"), out = document.getElementById("out");
f.onload = () => setTimeout(() => { try {
  const w = f.contentWindow, P = w.Pie, names = P.store.names;
  const list = P.board.outliers().map((o) => ({ ...o,
    platform: P.platformOf(P.store.index.hardware[o.hardware] || {}),
    machine: names.of("hardware", o.hardware), modelName: names.model(o.model), bestName: names.engine(o.best), engineName: names.engine(o.engine) }));
  const hardware = {}, machines = {}, models = {};
  for (const h of P.store.tables.hardware || []) { hardware[h.id] = P.platformOf(h); machines[h.id] = names.of("hardware", h.id); }
  for (const m of P.store.tables.models || []) models[m.id] = names.model(m.id);
  out.textContent = JSON.stringify({ list, hardware, machines, models });
} catch (e) { out.textContent = "ERROR " + e; } }, 6000);
</script>"""


class Page(http.server.SimpleHTTPRequestHandler):
    """The harness and data/ from the built data folder; every other file of the page from the website. On 127.0.0.1
    the page reads data/ beside it (its boot/data.js), so it draws this build's data."""

    def do_GET(self):
        if self.path == "/zz-outliers.html":
            return self.reply(HARNESS.encode(), "text/html")
        if self.path.startswith("/data/"):
            self.path = self.path[len("/data"):]
            return super().do_GET()
        try:
            with urllib.request.urlopen(PAGE + self.path.split("?")[0], timeout=60) as r:
                self.reply(r.read(), r.headers.get("Content-Type", "application/octet-stream"))
        except Exception:
            self.send_error(404)

    def reply(self, body: bytes, kind: str) -> None:
        self.send_response(200)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass


def outliers(site: Path) -> list[dict]:
    """The site's red dots, read by loading it in headless Chrome."""
    handler = functools.partial(Page, directory=str(site))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    profile = tempfile.mkdtemp()
    try:
        dom = subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--virtual-time-budget=30000", f"--user-data-dir={profile}",
                              "--dump-dom", f"http://127.0.0.1:{server.server_address[1]}/zz-outliers.html"],
                             capture_output=True, text=True, timeout=180).stdout
    finally:
        server.shutdown()
        shutil.rmtree(profile, ignore_errors=True)
    found = re.search(r'<pre id="out">(.*?)</pre>', dom, re.S)
    text = (found.group(1) if found else "").replace("&quot;", '"').replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")
    if not text.startswith("{"):
        raise SystemExit(f"the site gave no outliers: {text[:200] or 'nothing'}")
    return json.loads(text)


def body(platform: str, cells: list[dict], reports: list[dict] = (), names: dict | None = None, closed: list[dict] = ()) -> str:
    """A platform's issue description: its outliers in two sections, above the theoretical limit and slower than the
    strongest competitor, each with a table per setup, worst first."""
    num = lambda v, unit: f"{round(v):,} {unit}"
    parts = []
    # the site's own type names, each with its colour (Pie Reports' Type filter)
    for above, heading in ((True, "🟧 Exceeds Theoretical Limit"),):
        kind = [c for c in cells if c["above"] == above]
        if not kind:
            continue
        parts.append(f"## {heading} [{len(kind)}]")
        for setup in SETUPS:
            group = sorted((c for c in kind if c["label"] == setup), key=lambda c: -c["gain"] if above else c["gain"])
            if not group:
                continue
            # the last column opens Pie Reports on just that cell
            rows = "\n".join(f"| {c['engineName']} | {c['modelName']}{' (slice)' if c.get('miniature') else ''} | {c['machine']} | {num(c['pie'], c['unit'])} | [Open]({SITE}/#reports/{c['hardware']}/{c['model']}/{c['setup']}) |" for c in group)
            parts.append(f"### {setup} [{len(group)}]\n\n| Engine | Model | Machine | Measured | |\n|---|---|---|---|---|\n{rows}")
    # the reports people filed on the site, newest first, each opening Pie Reports on its machine and model
    if reports:
        names = names or {}
        line = lambda t: str(t or "").replace("|", "\\|").replace("\n", " ").strip()
        rows = "\n".join(f"| {line(names.get('models', {}).get(r['model'], r['model']))} | {line(names.get('machines', {}).get(r['hardware'], r['hardware']))} | "
                         f"{line(WORKLOADS.get(r.get('workload'), r.get('workload')))} | {line(r.get('value')) or '—'} | {line(r.get('note'))} | {line(r.get('reporter')) or '—'} | "
                         f"[Open]({SITE}/#reports/{r['hardware']}/{r['model']}) |" for r in reports)
        parts.append(f"## ⬜ Reports [{len(reports)}]\n\n| Model | Machine | Workload | Value | What is off | Reported by | |\n|---|---|---|---|---|---|---|\n{rows}")
    if not cells and not reports:
        parts.append("No reports yet.")
    # the ones a maintainer closed on the site, kept at the foot so the history stays readable
    if closed:
        rows = "\n".join(f"| {c['modelName']} | {c['machine']} | {c['label']} | {'Exceeds Theoretical Limit' if c['above'] else 'Behind Competitor'} | "
                         f"[Open]({SITE}/#reports/{c['hardware']}/{c['model']}/{c['setup']}) |" for c in closed)
        parts.append(f"## ✅ Closed [{len(closed)}]\n\n| Model | Machine | Setup | Type | |\n|---|---|---|---|---|\n{rows}")
    return "\n\n".join(parts) + "\n"


def gh(*args: str) -> str:
    return subprocess.run(["gh", *args], capture_output=True, text=True, check=True).stdout


def sync(site_data: dict, site: Path) -> None:
    # the site keeps no store (no accounts, no filed reports, no closed outliers): an issue lists what the data flags now,
    # and a visitor's report is an issue of its own
    all_cells = site_data["list"]
    closed_cells = []
    people = []
    # the issues carry the benchmarks label, made on pie the first time
    if LABEL not in gh("label", "list", "-R", REPO, "--limit", "200", "--json", "name", "--jq", ".[].name").split():
        gh("label", "create", LABEL, "-R", REPO, "--color", "5E5CE6", "--description", "Found by the benchmarks site")
    numbers = {}  # platform -> its issue, for the site's Issue column (trackers.json)
    for code, platform in PLATFORMS.items():
        title = f"[{platform}] Benchmarks"
        mine = [r for r in people if site_data["hardware"].get(r["hardware"]) == code]
        text = body(platform, [c for c in all_cells if c["platform"] == code], mine, site_data,
                    [c for c in closed_cells if c["platform"] == code])
        found = json.loads(gh("issue", "list", "-R", REPO, "--state", "open", "--search", f'in:title "{title}"', "--json", "number,title,body"))
        issue = next((i for i in found if i["title"] == title), None)
        if issue is None:
            url = gh("issue", "create", "-R", REPO, "--title", title, "--body", text, "--label", LABEL).strip()
            numbers[code] = int(url.rsplit("/", 1)[1])
            print(f"{title}: opened {url}")
            continue
        numbers[code] = issue["number"]
        if issue["body"].strip() != text.strip():
            gh("issue", "edit", str(issue["number"]), "-R", REPO, "--body", text)
            print(f"{title}: updated #{issue['number']}")
        else:
            print(f"{title}: unchanged #{issue['number']}")
    (site / "trackers.json").write_text(json.dumps(numbers))


if __name__ == "__main__":
    site = Path(sys.argv[1] if len(sys.argv) > 1 else "site")
    sync(outliers(site), site)
