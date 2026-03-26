# CS5491 Project Milestone Report Draft (English)

> Aligned with the course milestone requirements:
> 1) Problem description & motivation
> 2) Design of method/approach
> 3) Preliminary results

---

## 1. Project Information

- **Course**: CS5491
- **Project**: Sample-Efficient FunSearch via Behavioral Deduplication and Diversity-Guided Selection
- **Team members**: CHEN Sijie (59872908) & BIAN Wenbo (59872472)
- **Date**: 2026-03-27

---

## 2. Problem Description and Motivation

LLM-driven program search (e.g., FunSearch) often generates many behaviorally redundant candidates. Although these candidates may look syntactically different, they can make equivalent decisions on the target task. Evaluating such duplicates wastes API calls and compute, reducing sample efficiency.

Our project focuses on online bin packing and aims to improve search efficiency without sacrificing final solution quality. We use two mechanisms:

1. Behavioral deduplication before full evaluation;
2. Diversity-guided selection to avoid early strategy collapse.

---

## 3. Design of Method / Approach

### 3.1 Pipeline Overview

Current v1 pipeline:

1. Candidate generation
2. Behavioral probing (5–15 probes)
3. Behavioral duplicate filtering (threshold > 0.95)
4. Full evaluation for non-duplicates
5. Archive update
6. Diversity-guided candidate selection

### 3.2 Behavioral Deduplication

We build deterministic behavioral fingerprints and compare them with archive fingerprints. Candidates above the similarity threshold are filtered before expensive evaluation.

Implemented modules:

- `src/similarity/behavioral_probe.py`
- `src/similarity/hybrid.py`
- `src/archive/program_archive.py`
- `src/integration/funsearch_adapter.py`

### 3.3 Diversity-Guided Selection

Candidate ranking uses a combined score:

`combined(c) = perf(c) + beta * diversity(c)`

Implemented modules:

- `src/similarity/diversity.py`
- `src/integration/funsearch_adapter.py`
- `src/metrics/efficiency_logger.py`

### 3.4 Metrics and Ablation

Metrics include sample efficiency, duplicate detection rate, convergence, and final quality. We define 4 ablation settings: `original`, `exact_string_match`, `normalized_hash_only`, `behavioral_plus_diversity`.

### 3.5 Benchmark Details

- **Primary benchmark**: OR-Library bin packing instances
- **Source**: http://people.brunel.ac.uk/~mastjjb/jeb/info.html
- **Data format**: text files (instance lines)
- **Current milestone scope**: small-to-medium OR-Library-style instances for quick preliminary runs

---

## 4. Preliminary Results

### 4.1 Current Engineering Evidence

- `ruff check .` passed
- `pytest -q -rs` passed: **65 passed, 0 skipped**
- US1/US2/US3 paths are covered by unit/integration tests

### 4.2 Preliminary Results Table

Benchmark setup used for this table: OR-Library `binpack1.txt`, first 3 instances (`u120_00`, `u120_01`, `u120_02`), single-generation preliminary run.
`Final Quality Proxy` is average `(best_known_bins / bins_used)` across these instances (higher is better).

| Setting | N_total | N_unique | Sample Efficiency η | Duplicate Rate | Convergence Proxy | Final Quality Proxy | Status |
|---|---:|---:|---:|---:|---:|---:|---|
| original | 4 | 4 | 1.0000 | 0.0000 | OR-Library prelim (1 generation) | 0.9861 | OR-Library preliminary measured |
| exact_string_match | 4 | 4 | 1.0000 | 0.0000 | OR-Library prelim (1 generation) | 0.9861 | OR-Library preliminary measured |
| normalized_hash_only | 4 | 4 | 1.0000 | 0.0000 | OR-Library prelim (1 generation) | 0.9861 | OR-Library preliminary measured |
| behavioral_plus_diversity | 4 | 4 | 1.0000 | 0.0000 | OR-Library prelim (1 generation) | 0.9861 | OR-Library preliminary measured |

### 4.3 Metric Mapping

For each setting/run:

1. **N_total** = `total_programs_generated`
2. **N_unique** = `programs_evaluated`
3. **Sample Efficiency η** = `N_unique / N_total` (or `sample_efficiency`)
4. **Duplicate Rate** = `duplicates_detected / total_programs_generated` (or `duplicate_detection_rate`)
5. **Convergence Proxy** = consistently defined convergence proxy
6. **Final Quality Proxy** = final quality metric (e.g., best score)

---

## 5. Reproducibility

```bash
ruff check .
pytest -q -rs
```

Expected:

- lint pass
- tests pass (currently 65 passed, 0 skipped)
