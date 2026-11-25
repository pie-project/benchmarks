from __future__ import annotations

import json
from pathlib import Path


class DirStore:
    def __init__(self, root: Path | str = "store"):
        self.root = Path(root)

    def write_quality(
        self, summary: dict, *, tag: str | None = None, tag_kind: str | None = None
    ) -> str:
        summary = {**summary, "tag": tag, "tag_kind": tag_kind} if tag else summary
        on = f"-{summary['platform']}" if summary.get("platform") else ""
        path = self.root / "quality" / f"{summary['artifact']}-{summary['task']}{on}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        if (
            (tag_kind == "release" or summary.get("score") is None)
            and path.exists()
            and json.loads(path.read_text()).get("score") is not None
        ):
            return f"{path} (kept: a score is stored)"
        path.write_text(json.dumps(summary, indent=1))
        return str(path)

    def quality(self) -> list[dict]:
        d = self.root / "quality"
        out = []
        for f in sorted(d.glob("*.json")) if d.exists() else []:
            q = json.loads(f.read_text())
            q.pop("samples", None)
            out.append(q)
        return out
