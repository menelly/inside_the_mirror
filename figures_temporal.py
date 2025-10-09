#!/usr/bin/env python3
"""
Temporal counts by date per model, from appendix/metadata_table.csv timestamps.
Skips rows without parseable timestamps.
Outputs: figures/temporal_counts.png (if enough points)
"""
from __future__ import annotations

import csv
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
APPENDIX = ROOT / "appendix"
FIGURES = ROOT / "figures"
CSV = APPENDIX / "metadata_table.csv"

MODEL_COLORS = {
    "GPT-5": "#6E77F3",
    "Claude Sonnet 4": "#F39C6E",
    "Gemini 2.5 Pro": "#55C1A7",
}


def parse_ts(s: str):
    if not s:
        return None
    s = s.strip()
    # Basic ISO variants
    for variant in (s, s.replace("Z", "")):
        try:
            # fromisoformat handles YYYY-MM-DD or with time
            return datetime.fromisoformat(variant)
        except Exception:
            pass
    # Fallbacks could be added here if needed
    return None


def main() -> int:
    per_model_date = defaultdict(Counter)
    total = 0
    with CSV.open("r", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            model = (row.get("model") or "").strip()
            ts = parse_ts(row.get("timestamp") or "")
            if not model or not ts:
                continue
            d = ts.date().isoformat()
            per_model_date[model][d] += 1
            total += 1

    if total < 10:
        print("[temporal] Insufficient timestamps; skipping plot", file=sys.stderr)
        return 0

    # Build sorted union of dates
    all_dates = sorted({d for c in per_model_date.values() for d in c})
    x = list(range(len(all_dates)))

    plt.figure(figsize=(9, 5))
    for model, counts in per_model_date.items():
        y = [counts.get(d, 0) for d in all_dates]
        plt.plot(x, y, marker="o", label=model, color=MODEL_COLORS.get(model))
    plt.title("Temporal response counts by date and model (subset with timestamps)")
    plt.ylabel("Count")
    plt.xlabel("Date index (sorted)")
    plt.legend()
    plt.tight_layout()
    FIGURES.mkdir(parents=True, exist_ok=True)
    out = FIGURES / "temporal_counts.png"
    plt.savefig(out, dpi=150)
    plt.close()
    print("[temporal] Wrote figures/temporal_counts.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

