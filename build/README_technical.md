# LLMQualia technical notes (pipeline + reproducibility)

This document describes the minimal commands to regenerate tables, figures, and the paper draft from local sources.

Requirements
- Python 3.10+
- matplotlib (figures)
- Optional: scikit-learn, networkx (similarity network)

Commands
```bash
# 1) Normalize and write tables
python3 pipeline.py

# 2) Core figures
python3 figures.py

# 3) Optional similarity network (install deps if needed)
python3 -m pip install --user scikit-learn networkx
python3 figures_similarity.py

# 4) Optional temporal figure (will skip if insufficient timestamps)
python3 figures_temporal.py

# 5) Assemble Results from curated comparisons
python3 assemble_results.py

# 6) Build the draft
python3 generate_draft.py
```

Outputs
- appendix/metadata_table.csv, summary_counts_by_model.csv, summary_counts_by_model_trial.csv
- figures/model_counts.png, figures/model_trial_counts.png
- figures/similarity_network.png (if optional step run)
- build/02_results.md (assembled), build/paper_draft.md (full draft)
- build/CHANGELOG.md logs actions

Notes
- All outputs are append-only where feasible and version-rotated.
- No network calls required; local files only.
- Canonical model names: GPT-5, Claude Sonnet 4, Gemini 2.5 Pro.

