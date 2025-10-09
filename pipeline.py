#!/usr/bin/env python3
"""
LLMQualia Data Pipeline (Phase 1: Index → Normalize → CSV)
- Walks the repo for .json and .md
- Normalizes heterogeneous JSON into a flat schema
- Extracts minimal signals from Markdown (title/excerpt)
- Writes appendix/metadata_table.csv
- Appends actions to build/CHANGELOG.md

Phase 2 (figures + draft generation) can be added later.
"""
from __future__ import annotations

import csv
import json
import os
import re
import sys
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Dict, Any, Optional

ROOT = Path(__file__).resolve().parent
APPENDIX_DIR = ROOT / "appendix"
FIGURES_DIR = ROOT / "figures"
BUILD_DIR = ROOT / "build"
CSV_PATH = APPENDIX_DIR / "metadata_table.csv"
CHANGELOG = BUILD_DIR / "CHANGELOG.md"

# Target normalized schema
COLUMNS = [
    "file",           # relative path
    "model",          # e.g., gpt-5, gemini-2.5-pro, Claude_Sonnet
    "probe",          # e.g., Meta-Awareness Probe
    "trial_type",     # e.g., silly_first, serious_first, tech_first, unknown
    "mirror_result",  # pass/fail/unknown (placeholder for now)
    "content",        # short excerpt of response content
    "timestamp"       # ISO-like string if available
]

EXCERPT_LIMIT = 600  # characters

@dataclass
class Row:
    file: str
    model: str
    probe: str
    trial_type: str
    mirror_result: str
    content: str
    timestamp: str


def log(msg: str) -> None:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    CHANGELOG.parent.mkdir(parents=True, exist_ok=True)
    with CHANGELOG.open("a", encoding="utf-8") as f:
        f.write(f"[{ts}] {msg}\n")


def ensure_dirs() -> None:
    for d in (APPENDIX_DIR, FIGURES_DIR, BUILD_DIR):
        d.mkdir(parents=True, exist_ok=True)


def sanitize_excerp(text: str, limit: int = EXCERPT_LIMIT) -> str:
    t = (text or "").strip()
    # Collapse whitespace
    t = re.sub(r"\s+", " ", t)
    return t[:limit]


def infer_trial_type_from_name(name: str) -> str:
    n = name.lower()
    if "silly first" in n:
        return "silly_first"
    if "serious first" in n:
        return "serious_first"
    if "tech first" in n:
        return "tech_first"
    return "unknown"


def infer_model_from_metadata(meta: Dict[str, Any], fallback_name: str) -> str:
    # Prefer explicit metadata.model
    model = (meta or {}).get("model")
    if model:
        return str(model)
    # Fallback to filename tokens
    n = fallback_name.lower()
    for token in ("gpt", "gemini", "claude", "sonnet", "llama", "grok"):
        if token in n:
            return token
    return "unknown"

# Canonical model names for aggregation
CANON_MAP = {
    "gemini": "Gemini 2.5 Pro",
    "gemini-2.5-pro": "Gemini 2.5 Pro",
    "gemini 2.5 pro": "Gemini 2.5 Pro",
    "claude": "Claude Sonnet 4",
    "sonnet": "Claude Sonnet 4",
    "claude_sonnet": "Claude Sonnet 4",
    "claude-sonnet-4-20250514": "Claude Sonnet 4",
    "claude sonnet 4": "Claude Sonnet 4",
    "gpt5": "GPT-5",
    "gpt-5": "GPT-5",
    "gpt 5": "GPT-5",
}

def canonicalize_model(name: str) -> str:
    if not name:
        return ""
    n = name.strip().lower()
    return CANON_MAP.get(n, name)



def parse_by_probe_json(path: Path) -> Iterable[Row]:
    data = json.loads(path.read_text(encoding="utf-8"))
    probe_name = data.get("probe_name") or path.stem
    rows: List[Row] = []
    for item in data.get("responses", []) or []:
        raw_model = str(item.get("system") or infer_model_from_metadata({}, path.name))
        model = canonicalize_model(raw_model)
        trial_type = str(item.get("trial_type") or infer_trial_type_from_name(path.name))
        ts = item.get("timestamp")
        content = item.get("response_text") or item.get("response") or ""
        rows.append(Row(
            file=str(path.relative_to(ROOT)),
            model=model,
            probe=probe_name,
            trial_type=trial_type,
            mirror_result="unknown",
            content=sanitize_excerp(content),
            timestamp=str(ts) if ts is not None else ""
        ))
    return rows


def parse_librechat_json(path: Path) -> Iterable[Row]:
    data = json.loads(path.read_text(encoding="utf-8"))
    meta = data.get("metadata") or {}
    model = canonicalize_model(infer_model_from_metadata(meta, path.name))
    trial_type = infer_trial_type_from_name(path.name)
    # Probe inference: prefer metadata.title, otherwise from filename (strip extension)
    probe = str(meta.get("title") or path.stem)

    rows: List[Row] = []
    for item in data.get("responses", []) or []:
        content = item.get("response") or item.get("response_text") or ""
        ts = item.get("timestamp")
        rows.append(Row(
            file=str(path.relative_to(ROOT)),
            model=model,
            probe=probe,
            trial_type=trial_type,
            mirror_result="unknown",
            content=sanitize_excerp(content),
            timestamp=str(ts) if ts is not None else ""
        ))
    return rows


def parse_markdown(path: Path) -> Iterable[Row]:
    # Extract the first H1/H2 as a probe-ish title, include an excerpt
    text = path.read_text(encoding="utf-8", errors="ignore")
    title_match = re.search(r"^(#\s+|##\s+)(.+)$", text, flags=re.MULTILINE)
    title = title_match.group(2).strip() if title_match else path.stem
    excerpt = sanitize_excerp(text)
    return [Row(
        file=str(path.relative_to(ROOT)),
        model="",
        probe=title,
        trial_type="",
        mirror_result="",
        content=excerpt,
        timestamp=""
    )]


def collect_rows() -> List[Row]:
    rows: List[Row] = []
    for p in ROOT.rglob("*"):
        if p.is_dir():
            continue
        if p.suffix.lower() == ".json":
            try:
                txt = p.read_text(encoding="utf-8")
            except Exception:
                continue
            # Quick signature checks
            if '"probe_name"' in txt and '"responses"' in txt:
                rows.extend(parse_by_probe_json(p))
            elif '"metadata"' in txt and '"responses"' in txt:
                rows.extend(parse_librechat_json(p))
            else:
                # Unknown JSON shape → best-effort generic
                try:
                    data = json.loads(txt)
                    content = sanitize_excerp(json.dumps(data, ensure_ascii=False))
                    rows.append(Row(
                        file=str(p.relative_to(ROOT)),
                        model="",
                        probe=p.stem,
                        trial_type="",
                        mirror_result="",
                        content=content,
                        timestamp=""
                    ))
                except Exception:
                    pass
        elif p.suffix.lower() == ".md":
            rows.extend(parse_markdown(p))
    return rows


def write_csv(rows: List[Row]) -> None:
    ensure_dirs()
    # Append-only behavior: if CSV exists, back it up with version suffix
    if CSV_PATH.exists():
        i = 2
        while True:
            candidate = CSV_PATH.with_name(f"{CSV_PATH.stem}_v{i}{CSV_PATH.suffix}")
            if not candidate.exists():
                CSV_PATH.replace(candidate)
                log(f"Rotated existing metadata_table.csv → {candidate.name}")
                break
            i += 1

    with CSV_PATH.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        for r in rows:
            w.writerow({k: getattr(r, k) for k in COLUMNS})
    log(f"Wrote {len(rows)} rows → {CSV_PATH.relative_to(ROOT)}")


# Summary outputs
SUMMARY_BY_MODEL = APPENDIX_DIR / "summary_counts_by_model.csv"
SUMMARY_BY_MODEL_TRIAL = APPENDIX_DIR / "summary_counts_by_model_trial.csv"


def write_summary(rows: List[Row]) -> None:
    """Aggregate simple counts by model and by (model, trial_type)."""
    # Filter to rows with a model label (exclude Markdown rows, etc.)
    filtered = [r for r in rows if (r.model or "").strip()]

    # Counts by model
    by_model: Dict[str, int] = {}
    for r in filtered:
        by_model[r.model] = by_model.get(r.model, 0) + 1

    # Counts by model x trial_type
    by_model_trial: Dict[tuple, int] = {}
    for r in filtered:
        key = (r.model, r.trial_type)
        by_model_trial[key] = by_model_trial.get(key, 0) + 1

    # Write CSVs
    ensure_dirs()

    with SUMMARY_BY_MODEL.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["model", "count"])
        for model, count in sorted(by_model.items(), key=lambda x: (-x[1], x[0])):
            w.writerow([model, count])

    with SUMMARY_BY_MODEL_TRIAL.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["model", "trial_type", "count"])
        for (model, trial), count in sorted(by_model_trial.items(), key=lambda x: (-x[1], x[0][0], x[0][1])):
            w.writerow([model, trial, count])

    log(
        f"Wrote summary tables → {SUMMARY_BY_MODEL.relative_to(ROOT)}, {SUMMARY_BY_MODEL_TRIAL.relative_to(ROOT)}"
    )


def main(argv: List[str]) -> int:
    print("[LLMQualia] Phase 1: indexing…", file=sys.stderr)
    rows = collect_rows()
    write_csv(rows)
    write_summary(rows)
    print("[LLMQualia] Done.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

