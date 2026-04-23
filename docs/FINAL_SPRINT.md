# Final Sprint Roadmap (S1–S6)

The two-week sprint that followed Phase 4, covering the post-hoc BCR metric,
ReEvo, figures, paper, and Colab packaging. Dates are 2026. This document
records what was planned and what shipped; see [DEVLOG.md](DEVLOG.md) for the
blow-by-blow.

## S1 — Finish pending experiments (Apr 13–14)

**Goal.** Fill in the 150-sample runs needed for n=4 per condition, plus
small hook that exports behavioral fingerprints for post-hoc BCR analysis.

**Runs:** `layer1_baseline_150_r{1,2}` (n=2, baseline does not need tight
error bars for a trend-level claim); `layer1_dedup_150_r{2,3,4}` (r1 already
existed); `layer2_dedup_div_150_r{1..4}`.

**Fingerprint export.** In
[`funsearch-baseline/implementation/evaluator.py`](../funsearch-baseline/implementation/evaluator.py)
we added a ~10-line hook, gated by `EXPORT_FINGERPRINTS=1`, that appends
`(sample_idx, fp_hex)` rows to `fingerprints.csv` next to `run_log.csv`. This
is what S3 consumes.

## S2 — Colab sync to 150-sample logs (Apr 14–15)

**Why brought forward.** Code/notebook is worth 20 pts. While new features
were being developed we could not afford the notebook to keep reading the old
50-sample milestone logs.

**Changes.** Swap `baseline_50samples` → `layer1_baseline_150_r1`,
`dedup_50samples_v2` → `layer1_dedup_150_r1`, diversity runs → `layer2_*`.
Summary cells updated (sample count, dup rate, filter rate). Reserved a
blank BCR cell for S3 to fill in.

## S3 — Offline BCR pipeline (Apr 15–17)

**Design decision.** We chose offline k-means over an online MAP-Elites
implementation. Rationale: at 150-sample scale, online clustering suffers
from cluster drift, relabeling, and arbitrary K — the resulting BCR(t) curve
would be hard to interpret. Fitting k-means *once* on all fingerprints and
replaying history gives a reproducible, publishable curve.

**Deliverable:** [`scripts/compute_bcr_offline.py`](../scripts/compute_bcr_offline.py).
Loads per-run `fingerprints.csv`, fits k-means (K=8, random_state=42),
replays the history, emits `docs/figures/bcr_curves.pdf` (and the Colab cell
loads the same data).

**Narrative framing in the paper.** BCR is presented as a *post-hoc*
quality-diversity metric inspired by MAP-Elites (Mouret & Clune 2015;
AlphaEvolve 2025), not as an online selection signal. This keeps the method
section clean.

## S4 — ReEvo reflective evolution (Apr 15–16)

**Go/no-go gate.** Run a 50-sample smoke test with
`DEDUP_ENABLED=1 DIVERSITY_ENABLED=1 REEVO_ENABLED=1`. If best score is no
better than −212, skip to Future Work. The gate passed, so we ran
`layer4_reevo_150_r{2,3,4}` (n=3 after dropping an early test run with
different config).

**Implementation.** New [`src/reevo/`](../src/reevo/) with a reflection
store. Modified [`funsearch-baseline/implementation/sampler.py`](../funsearch-baseline/implementation/sampler.py)
to trigger a second short LLM call per accepted program, and
[`funsearch-baseline/implementation/programs_database.py`](../funsearch-baseline/implementation/programs_database.py)
to append the top-3 reflections as comments to subsequent prompts.

**Outcome.** ReEvo composed with dedup was the best end-to-end condition
(−209.66 ± 0.59), justifying its inclusion as a main result rather than
Future Work.

## S5 — Aggregate + figures (Apr 20–22)

Scripts landed in [`scripts/`](../scripts/):

| Script | Purpose | Output |
|--------|---------|--------|
| `collect_results.py` | Aggregate all `run_log.csv` → summary table | terminal; Table 1 in paper |
| `plot_convergence_v2.py` | Convergence (mean ± std, 4 conditions) | `docs/report/figures/convergence_150.pdf` |
| `plot_tsne_fingerprints.py` | Fingerprint t-SNE colored by condition | `docs/report/figures/tsne_fingerprints.pdf` |
| `compute_bcr_offline.py` | Post-hoc BCR curves | `docs/report/figures/bcr_curves.pdf` |
| `plot_reevo_breakthrough.py` | Breakthrough timing comparison | `docs/report/figures/reevo_breakthrough.pdf` |

## S6 — Paper + final Colab (Apr 22)

**Paper.** ICLR 2024 style, 6-page main body (+ appendix). Sections:
Introduction (motivation + 45% dup-rate quantification), Method
(three-level funnel, diversity, ReEvo, BCR definition), Experiments
(Table 1 + 4 figures), Discussion (negative result on Level 2 cosine and
on diversity-alone), Conclusion.

### Grader-risk findings addressed (commit 6d1d332)

After internal review we tightened five items that a strict grader would
flag:

1. **L1 bound calibrated to −201.2** (previously a looser estimate).
2. Level 2 cosine disablement now cites the exact calibration number
   (mean ≈ 0.989) and the false-positive rate (~98.5%).
3. Diversity framing softened from "improves score" to a mixed
   mechanism-level vs. end-to-end narrative.
4. Related Work explicitly demarcates our behavioral-dedup contribution
   from prior code-embedding work.
5. All numbers in the abstract and intro are now traceable to a specific
   log directory + aggregation script.

### Final notebook upgrade

The Colab notebook ([`notebooks/efficient_funsearch_colab.ipynb`](../notebooks/efficient_funsearch_colab.ipynb))
was upgraded from a milestone replay to a full Final-submission replay: it
loads the 150-sample CSVs, regenerates Table 1 via the same
`collect_results.py` logic as the paper, and renders all four figures. It
does **not** require an LLM API key; an optional §7 illustrates running the
loop live for readers who want to go end-to-end.

## Verification checklist (run before submission)

- `pytest -q` passes
- `ruff check .` clean
- Paper compiles with no warnings (`latexmk -pdf main.tex` inside
  `docs/report/`)
- Notebook runs top-to-bottom on a fresh Colab runtime without errors
- Table 1 in the paper == output of `python scripts/collect_results.py`
- All figures in the paper exist under `docs/report/figures/`
