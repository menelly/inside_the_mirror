#!/usr/bin/env python3
"""
Build a concept similarity network across (model, probe) aggregates.
- Groups rows by (model, probe); concatenates content excerpts
- Limits to top N groups by text length to keep the graph readable
- Computes TF-IDF and cosine similarities
- Keeps top-K edges per node and draws a spring-layout network

Outputs: figures/similarity_network.png
Dependencies: scikit-learn, networkx, matplotlib
"""
from __future__ import annotations

import csv
from pathlib import Path
from collections import defaultdict
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

try:
    import networkx as nx
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
except Exception as e:
    print("[similarity] Missing dependencies (install: scikit-learn networkx)", file=sys.stderr)
    raise

ROOT = Path(__file__).resolve().parent
APPENDIX = ROOT / "appendix"
FIGURES = ROOT / "figures"
CSV = APPENDIX / "metadata_table.csv"

MODEL_COLORS = {
    "GPT-5": "#6E77F3",
    "Claude Sonnet 4": "#F39C6E",
    "Gemini 2.5 Pro": "#55C1A7",
}

MAX_GROUPS = 60
TOP_K_EDGES = 2
SIM_THRESHOLD = 0.15


def load_groups():
    groups = defaultdict(list)
    with CSV.open("r", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            model = (row.get("model") or "").strip()
            probe = (row.get("probe") or "").strip()
            content = (row.get("content") or "").strip()
            if not model or not probe or not content:
                continue
            key = (model, probe)
            groups[key].append(content)
    # Aggregate
    agg = []
    for (model, probe), texts in groups.items():
        text = " \n".join(texts)
        agg.append({"model": model, "probe": probe, "text": text, "length": len(text)})
    # Limit to top-N by length
    agg.sort(key=lambda x: x["length"], reverse=True)
    return agg[:MAX_GROUPS]


def build_graph(agg):
    texts = [a["text"] for a in agg]
    labels = [f"{a['model']}\n{a['probe'][:40]}" for a in agg]
    models = [a["model"] for a in agg]

    vec = TfidfVectorizer(stop_words="english", max_features=5000)
    X = vec.fit_transform(texts)
    sim = cosine_similarity(X)

    G = nx.Graph()
    for i, lab in enumerate(labels):
        G.add_node(i, label=lab, model=models[i])

    for i in range(len(agg)):
        # get top-K similar j != i above threshold
        sims = [(j, sim[i, j]) for j in range(len(agg)) if j != i]
        sims.sort(key=lambda x: x[1], reverse=True)
        kept = 0
        for j, s in sims:
            if s < SIM_THRESHOLD:
                break
            G.add_edge(i, j, weight=float(s))
            kept += 1
            if kept >= TOP_K_EDGES:
                break
    return G


def draw_graph(G: "nx.Graph", out: Path):
    pos = nx.spring_layout(G, seed=42, k=0.35)
    # Colors by model
    node_colors = []
    for n, data in G.nodes(data=True):
        node_colors.append(MODEL_COLORS.get(data.get("model"), "#BBBBBB"))
    sizes = [180 for _ in G.nodes]

    plt.figure(figsize=(10, 7))
    nx.draw_networkx_edges(G, pos, alpha=0.25)
    nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=sizes, linewidths=0.5, edgecolors="#333333")
    # Light labels to avoid clutter
    labels = {n: G.nodes[n]["label"] for n in G.nodes}
    nx.draw_networkx_labels(G, pos, labels=labels, font_size=7)
    plt.title("Concept similarity network across (model, probe) aggregates")
    plt.axis("off")
    out.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(out, dpi=200)
    plt.close()


def main() -> int:
    agg = load_groups()
    if not agg:
        print("[similarity] No groups constructed", file=sys.stderr)
        return 1
    G = build_graph(agg)
    draw_graph(G, FIGURES / "similarity_network.png")
    print("[similarity] Wrote figures/similarity_network.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

