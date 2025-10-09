This study consolidates existing artifacts from the LLMQualia project into a searchable, normalized corpus and assembles a draft paper with minimal, reproducible transformations.

Data sources
- by_probe/*.json: per-probe collections with fields like probe_name, responses[{system, trial_type, exchange_number, response_text, thinking, timestamp, source_file}]
- LibreChat_*_responses_only.json: LibreChat exports with metadata (title, model) and responses[{response, timestamp}]
- comparsion_file/*.md: curated comparative writeups per probe

Normalization
- Implemented in pipeline.py (stdlib). Walks the repo for *.json and *.md.
- JSON signatures are routed to parsers; minimal text excerpt (<=600 chars) retained for indexing.
- Target schema: file, model, probe, trial_type, mirror_result (unused here), content, timestamp.
- Model names canonicalized to: GPT-5, Claude Sonnet 4, Gemini 2.5 Pro.
- Trial type inferred from filenames when not explicitly present (silly_first, serious_first, tech_first, unknown).
- Outputs: appendix/metadata_table.csv (append-only; prior versions rotated), summary_counts_by_model.csv, summary_counts_by_model_trial.csv.

Figure generation
- figures.py (matplotlib) renders: model_counts.png and model_trial_counts.png from summary CSVs.
- figures/figures_alt_text.md documents accessible descriptions for each figure.

Results assembly
- assemble_results.py concatenates comparsion_file/*.md into build/02_results.md with section headers and separators, preserving original text.

Reproducibility & logging
- All write operations are append-only where feasible and logged to build/CHANGELOG.md with timestamps.
- No external network calls are required; the pipeline uses local files and stdlib + matplotlib.

Planned extensions (not executed in this draft)
- Similarity graph: TF-IDF over content excerpts with cosine similarity and network visualization (scikit-learn + networkx).
- Temporal analysis contingent on timestamp coverage and alignment across sources.

