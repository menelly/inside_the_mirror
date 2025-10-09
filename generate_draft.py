#!/usr/bin/env python3
"""
Concatenate paper sections into build/paper_draft.md.
Order (include if exists):
  00_title_and_authors.md
  01_abstract.md
  03_methods.md
  02_results.md
  04_discussion.md
  05_ethics_and_safety.md
  06_related_work.md
  07_conclusion_and_limitations.md
Logs to build/CHANGELOG.md.
"""
from __future__ import annotations

from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent
BUILD = ROOT / "build"
CHANGELOG = BUILD / "CHANGELOG.md"

ORDER = [
    "00_title_and_authors.md",
    "01_abstract.md",
    "03_methods.md",
    "02_results.md",
    "04_discussion.md",
    "05_ethics_and_safety.md",
    "06_related_work.md",
    "07_conclusion_and_limitations.md",
    "08_references.md",
]


def log(msg: str) -> None:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    BUILD.mkdir(parents=True, exist_ok=True)
    with CHANGELOG.open("a", encoding="utf-8") as f:
        f.write(f"[{ts}] {msg}\n")


def main() -> int:
    parts = []
    for name in ORDER:
        p = BUILD / name
        if p.exists():
            parts.append(p.read_text(encoding="utf-8").strip())
            parts.append("\n\n")
    out = BUILD / "paper_draft.md"
    out.write_text("".join(parts), encoding="utf-8")
    log(f"Assembled {len(parts)//2} sections -> {out.relative_to(ROOT)}")
    print(f"[draft] Wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

