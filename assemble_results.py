#!/usr/bin/env python3
"""
Assemble Results section from comparsion_file/*.md into build/02_results.md
- Preserves original markdown
- Orders files alphabetically by filename
- Adds an H2 header for each included file
- Appends a log entry to build/CHANGELOG.md
"""
from __future__ import annotations

import sys
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "comparsion_file"
OUT_DIR = ROOT / "build"
OUT = OUT_DIR / "02_results.md"
CHANGELOG = OUT_DIR / "CHANGELOG.md"


def log(msg: str) -> None:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with CHANGELOG.open("a", encoding="utf-8") as f:
        f.write(f"[{ts}] {msg}\n")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    files = sorted([p for p in SRC.glob("*.md") if p.is_file()])
    if not files:
        print("[assemble] No comparison files found.", file=sys.stderr)
        return 1

    parts = ["## Results: Comparative Analyses\n\n"]
    for p in files:
        title = p.stem
        try:
            content = p.read_text(encoding="utf-8")
        except Exception as e:
            content = f"[Error reading {p.name}: {e}]\n"
        parts.append(f"### {title}\n\n")
        parts.append(content.strip())
        parts.append("\n\n---\n\n")

    OUT.write_text("\n".join(parts), encoding="utf-8")
    log(f"Assembled {len(files)} comparison files → {OUT.relative_to(ROOT)}")
    print(f"[assemble] Wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

