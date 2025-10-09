#!/usr/bin/env python3
"""
Validate normalized corpus and write a brief report to build/VALIDATION.md.
Checks: totals, by-model counts, unknown trial_type count, empty content rows, unique probes.
"""
from __future__ import annotations

import csv
from pathlib import Path
from collections import Counter
from datetime import datetime

ROOT = Path(__file__).resolve().parent
APPENDIX = ROOT / "appendix"
BUILD = ROOT / "build"
CSV = APPENDIX / "metadata_table.csv"


def main() -> int:
    BUILD.mkdir(parents=True, exist_ok=True)
    by_model = Counter()
    unknown_trial = 0
    empty_content = 0
    probes = set()
    total = 0

    with CSV.open("r", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            total += 1
            model = (row.get("model") or "").strip()
            trial = (row.get("trial_type") or "").strip()
            content = (row.get("content") or "").strip()
            probe = (row.get("probe") or "").strip()
            if model:
                by_model[model] += 1
            if trial == "unknown" or trial == "unknown_trial":
                unknown_trial += 1
            if not content:
                empty_content += 1
            if probe:
                probes.add(probe)

    report = [
        "# VALIDATION\n",
        f"Generated: {datetime.now().isoformat()}\n\n",
        f"Total rows: {total}\n",
        f"Unique probes: {len(probes)}\n",
        f"Empty content rows: {empty_content}\n",
        f"Unknown trial_type rows: {unknown_trial}\n\n",
        "## Counts by model\n",
    ]
    for model, count in by_model.most_common():
        report.append(f"- {model}: {count}\n")

    (BUILD / "VALIDATION.md").write_text("".join(report), encoding="utf-8")
    print("[validate] Wrote build/VALIDATION.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

