#!/usr/bin/env python3
"""
Generate simple figures from appendix summaries:
- figures/model_counts.png
- figures/model_trial_counts.png

Uses only matplotlib (no pandas dependency).
"""
from __future__ import annotations

import csv
from pathlib import Path
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
APPENDIX = ROOT / "appendix"
FIGURES = ROOT / "figures"


def read_counts_by_model(path: Path):
    data = []
    with path.open("r", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            model = row["model"].strip()
            count = int(row["count"]) if row["count"].strip() else 0
            if model:
                data.append((model, count))
    return data


def read_counts_by_model_trial(path: Path):
    data = []
    with path.open("r", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            model = row["model"].strip()
            trial = row["trial_type"].strip()
            count = int(row["count"]) if row["count"].strip() else 0
            if model and trial:
                data.append((model, trial, count))
    return data


def plot_model_counts(data, out: Path):
    models = [m for m, _ in data]
    counts = [c for _, c in data]
    plt.figure(figsize=(7, 4))
    bars = plt.bar(models, counts, color=["#6E77F3", "#55C1A7", "#F39C6E"][:len(models)])
    plt.title("Response counts by model")
    plt.ylabel("Count")
    plt.xticks(rotation=15)
    for b, c in zip(bars, counts):
        plt.text(b.get_x() + b.get_width()/2, b.get_height() + 0.5, str(c), ha="center", va="bottom", fontsize=9)
    plt.tight_layout()
    out.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out, dpi=150)
    plt.close()


def plot_model_trial_counts(data, out: Path):
    # Get unique models and trials in stable order
    models = sorted({m for m, _, _ in data})
    trials = sorted({t for _, t, _ in data})
    # Build matrix
    matrix = [[0 for _ in trials] for _ in models]
    index = {(m, t): i for i, (m, t) in enumerate([(m, t) for m in models for t in trials])}
    for m, t, c in data:
        mi = models.index(m)
        ti = trials.index(t)
        matrix[mi][ti] = c
    # Stacked bars by trial type
    plt.figure(figsize=(8, 5))
    bottoms = [0]*len(models)
    colors = ["#6E77F3", "#55C1A7", "#F39C6E", "#E6B94C", "#C97CF3"]
    for idx, t in enumerate(trials):
        vals = [matrix[mi][idx] for mi in range(len(models))]
        plt.bar(models, vals, bottom=bottoms, label=t, color=colors[idx % len(colors)])
        bottoms = [bottoms[i] + vals[i] for i in range(len(models))]
    plt.title("Response counts by model × trial type")
    plt.ylabel("Count")
    plt.xticks(rotation=15)
    plt.legend(title="trial_type", bbox_to_anchor=(1.04, 1), loc="upper left")
    plt.tight_layout()
    out.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out, dpi=150)
    plt.close()


def main() -> int:
    by_model = read_counts_by_model(APPENDIX / "summary_counts_by_model.csv")
    if not by_model:
        print("[figures] No data in summary_counts_by_model.csv", file=sys.stderr)
        return 1
    plot_model_counts(by_model, FIGURES / "model_counts.png")

    by_model_trial = read_counts_by_model_trial(APPENDIX / "summary_counts_by_model_trial.csv")
    if by_model_trial:
        plot_model_trial_counts(by_model_trial, FIGURES / "model_trial_counts.png")

    print("[figures] Wrote figures")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

