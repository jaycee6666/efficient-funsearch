# Efficient FunSearch

Sample-efficient FunSearch for online bin packing, combining **behavioral deduplication**,
**diversity-guided selection**, and **reflective evolution (ReEvo)**.

This is the CS5491 Final submission repository. The compiled paper is at
[`docs/report/main.pdf`](docs/report/main.pdf); the reproducible end-to-end notebook is at
[`notebooks/efficient_funsearch_colab.ipynb`](notebooks/efficient_funsearch_colab.ipynb).

## Overview

The project upgrades a baseline FunSearch-style loop with three orthogonal mechanisms,
exposed as independent environment-variable switches so any subset can be ablated:

1. **Behavioral deduplication** (`DEDUP_ENABLED=1`) — three-level funnel run before full
   evaluation:
   - **Level 0**: AST normalisation + SHA256 on the rewritten source
   - **Level 1**: 375-dim behavioral fingerprint from 10 probing instances, SHA256 of the
     decision-sequence tuple (exact match, zero false positives by construction)
   - **Level 2**: cosine similarity on the fingerprint vector — **disabled** in the final
     configuration because high-dimensional discrete decision vectors collapse to mean
     cosine ≈ 0.989 and produce unacceptable false-positive rates (see paper §2.3 and
     calibration result in `docs/plan/06-step8-experiment-analysis.md`).
2. **Diversity-guided selection** (`DIVERSITY_ENABLED=1`) — island-level prompt sampling
   weights a performance term and a row-centered cosine *behavioral* diversity term with a
   linearly decaying `β` schedule (`β₀=0.3`, decay over 350 samples).
3. **Reflective evolution (ReEvo)** (`REEVO_ENABLED=1`) — after each accepted program, a
   short LLM-written reflection is stored (top 20 by score) and the three best reflections
   are appended as comments to subsequent prompts.

All three mechanisms write per-sample telemetry to `run_log.csv`; `scripts/collect_results.py`
aggregates runs into the summary table reported in the paper.

## Final Results (150 samples, n=4 per condition except baseline n=2)

| condition          | best_score        | 1st-hit sample | dup_rate          |
|--------------------|-------------------|----------------|-------------------|
| baseline           | −210.52 ± 1.31    | 146 ± 2        | N/A               |
| dedup              | **−210.04 ± 1.00**| **90 ± 36**    | 0.401 ± 0.046     |
| dedup + diversity  | −210.20 ± 0.68    | 108 ± 21       | 0.342 ± 0.067     |
| dedup + ReEvo      | **−209.66 ± 0.59**| 101 ± 16       | **0.314 ± 0.034** |

Headline takeaways (see paper for full discussion):
- **Behavioral dedup is the main result.** It yields +0.48 score uplift and 56 samples
  earlier first-hit vs. baseline.
- **ReEvo is the strongest end-to-end condition.**
- **Diversity-guided selection is a mechanism-level success but end-to-end mixed**:
  `dup_rate` drops 0.401 → 0.342, but final score and first-hit do not improve beyond
  dedup alone. The paper frames this honestly as a negative-to-mixed finding.

## Repository Layout

```text
docs/report/                      # Final paper (LaTeX + compiled PDF)
  main.tex / main.pdf             # CS5491 final report (ICLR 2024 style, 6-page body)
  final.bib                       # Verified BibTeX for cited papers
  figures/                        # Final paper figures (PDF)

docs/milestone/                   # Milestone submission (frozen 2026-03-31, not updated)
  milestone_report_draft_en.md
  milestone_report_draft_zh.md
  reproduction.txt                # Milestone-era reproduction steps
  README_submit.md

notebooks/
  efficient_funsearch_colab.ipynb            # Final-submission reproducible notebook
  efficient_funsearch_colab_milestone.ipynb  # Frozen Milestone snapshot (kept as reference)

funsearch-baseline/               # Course-provided FunSearch harness (modified in-place)
  funsearch_bin_packing_llm_api.py  # Main entry; reads DEDUP/DIVERSITY/REEVO env vars
  implementation/                    # evaluator, programs_database, profile, sampler, ...
  logs/                              # Per-run CSV logs consumed by scripts/ and notebook

src/
  dedup/                          # Three-level dedup funnel
    dedup_config.py, probing.py, dedup_filter.py
  reevo/                          # Reflection store for ReEvo
  normalizer/, similarity/, archive/, integration/, metrics/

scripts/
  collect_results.py              # Aggregate run logs → paper summary table
  compute_bcr_offline.py          # Offline Behavioural Coverage Rate analysis
  plot_tsne_fingerprints.py       # t-SNE visualisation of behavioural fingerprints
  calibration.py                  # Level-2 threshold calibration (cosine vs |Δscore|)
  analyze_baseline.py             # Single-run analyser

tests/                            # Unit and integration tests
```

## Research Trail

For readers interested in the design history and phase breakdown:

- [`docs/PROJECT_PLAN.md`](docs/PROJECT_PLAN.md) — overall methodology, the
  three-level dedup funnel, diversity selection, and final results
- [`docs/DEVLOG.md`](docs/DEVLOG.md) — chronological development log with
  key decisions, pitfalls, and bug fixes
- [`docs/FINAL_SPRINT.md`](docs/FINAL_SPRINT.md) — roadmap of the S1–S6
  final sprint (BCR, ReEvo, figures, paper)

## Requirements

- Python **3.9+** (development uses 3.10 via conda env `funsearch`)
- `numpy`, `matplotlib`, `scikit-learn`; optional: `tensorboardX`, `sentence-transformers`,
  `torch` for the optional richer similarity path (not used by the final configuration).

## Reproduction

### Option A — Colab notebook (recommended; no API key needed)

The notebook replays the pre-recorded CSV logs under `funsearch-baseline/logs/` to
regenerate every table and figure in the paper. Open
[`notebooks/efficient_funsearch_colab.ipynb`](notebooks/efficient_funsearch_colab.ipynb)
in Colab, run all cells; sections §6 (ReEvo), §7 (t-SNE), §8 (summary table) match the
paper exactly.

### Option B — Re-run the LLM loop locally

```bash
conda activate funsearch   # Python 3.10
export API_KEY=...
# optional: export API_TIMEOUT=60 API_MAX_RETRIES=5

cd efficient-funsearch/funsearch-baseline
# Four conditions; pick one set of flags:
# baseline:
LOG_DIR=logs/rerun_baseline python funsearch_bin_packing_llm_api.py
# dedup:
DEDUP_ENABLED=1 LOG_DIR=logs/rerun_dedup python funsearch_bin_packing_llm_api.py
# dedup + diversity:
DEDUP_ENABLED=1 DIVERSITY_ENABLED=1 LOG_DIR=logs/rerun_ddiv python funsearch_bin_packing_llm_api.py
# dedup + ReEvo:
DEDUP_ENABLED=1 REEVO_ENABLED=1 LOG_DIR=logs/rerun_reevo python funsearch_bin_packing_llm_api.py

# Aggregate:
cd .. && python scripts/collect_results.py
```

### Rebuilding the paper

```bash
cd docs/report
latexmk -pdf main.tex
```

## Milestone Materials

`docs/milestone/` is the Milestone-era submission (**frozen on 2026-03-31**, not updated
for the Final). The authoritative reproduction entry point for the Final is
`notebooks/efficient_funsearch_colab.ipynb` and this README.

## Quick Verification

```bash
ruff check .
pytest -q -rs
```

## Development Notes

- API key is read from environment variables; never hardcoded.
- LaTeX build artefacts (`.aux`, `.bbl`, `.log`, …) are gitignored; only `main.tex`,
  `final.bib`, styles, `figures/*.pdf`, and `main.pdf` are tracked under `docs/report/`.
- Follow task traceability in `specs/001-efficient-funsearch/plan.md` and `tasks.md`.
