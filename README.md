# Efficient FunSearch (CS5491 Project)

Sample-efficient FunSearch implementation with **behavioral deduplication** and **diversity-guided selection** for online bin packing search.

## Overview

This project upgrades a baseline FunSearch-style workflow by:

1. **Behavioral deduplication before full evaluation**
   - Build behavioral fingerprints from probe inputs (5-15 probes)
   - Filter behaviorally equivalent candidates (similarity threshold > 0.95)

2. **Performance + diversity candidate selection**
   - Rank candidates by combined score to reduce search collapse

3. **Unified metrics and ablation registry**
   - Sample efficiency: `eta = N_unique / N_total`
   - Duplicate rate and other efficiency stats
   - Four ablation settings:
     - `original`
     - `exact_string_match`
     - `normalized_hash_only`
     - `behavioral_plus_diversity`

## Repository Structure

```text
src/                     # Core implementation
  normalizer/            # Program normalization
  similarity/            # Similarity, behavior probe, diversity ranking
  archive/               # Program archive and duplicate checks
  integration/           # FunSearch adapter and ablation configs
  metrics/               # Efficiency metrics and logging

tests/                   # Unit and integration tests
specs/001-efficient-funsearch/
  spec.md                # Feature spec
  plan.md                # Implementation plan and traceability
  tasks.md               # Task checklist

docs/milestone/          # Milestone submission materials
```

## Requirements

- Python **3.9+**
- Recommended: virtual environment

Core dependencies are defined in `pyproject.toml`:

- `numpy`
- `sentence-transformers`
- `torch`

> Note: unit tests are designed to run offline without forcing external model downloads.

## Setup

```bash
# 1) Create/activate virtual environment (example)
python -m venv .venv
# Windows (PowerShell): .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate

# 2) Install package + dev dependencies
pip install -e .
pip install -e .[dev]
```

## Quick Verification

Run lint and all tests:

```bash
ruff check .
pytest -q -rs
```

## Key Modules

- `src/similarity/behavioral_probe.py`
  - Deterministic behavioral fingerprint construction

- `src/archive/program_archive.py`
  - Archive storage and duplicate filtering path

- `src/integration/funsearch_adapter.py`
  - Pre-evaluation dedup integration + diversity-aware ranking

- `src/metrics/models.py`
  - `EfficiencyMetrics` and sample efficiency property

- `src/integration/ablation_configs.py`
  - Proposal-v1 ablation configuration registry

## Milestone Materials

Prepared docs are available in:

- `docs/milestone/milestone_report_draft.md` (CN/EN draft)
- `docs/milestone/preliminary_results.md`
- `docs/milestone/MILESTONE_SUBMISSION_CHECKLIST.md`

## Development Notes

- Ignore local tool metadata (`.opencode/`) and local helper script (`PUSH_TO_GITHUB.sh`) via `.gitignore`.
- Follow task traceability in `specs/001-efficient-funsearch/plan.md` and `tasks.md`.
