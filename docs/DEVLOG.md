# Development Log — Efficient FunSearch

Condensed chronological log of technical decisions, pitfalls, and
verification gates. All dates are 2026. For the design rationale see
[PROJECT_PLAN.md](PROJECT_PLAN.md); for the final-sprint plan see
[FINAL_SPRINT.md](FINAL_SPRINT.md).

---

## Phase 1 — Baseline FunSearch (Mar 27–31)

### Mar 27 — Baseline wired up

- Cloned the course-provided FunSearch harness and got the evaluator + LLM
  loop running end-to-end on online bin packing (OR3 dataset).
- Initial 10-sample probe showed **100% of samples scored exactly −212.75**
  and 91.7% were LLM-valid. Something was badly wrong.
- **Root cause: the `_trim_preface_of_body()` bug.** The harness
  aggressively stripped the LLM response, matching `def ` and discarding
  everything up to and including that line. For `gpt-5-nano`, whose outputs
  routinely include a markdown fence + a `def priority(...):` declaration,
  the function *body* was being thrown away → `priority()` returned
  `None` → the evaluator fell back to first-fit, producing the same score
  every time.
- **Fix.** Strip ```` ``` ```` fences first, then keep the indented body
  after `def priority(...)`. Handle multiple LLM output layouts.

### Environment pitfalls encountered

| Symptom | Cause | Fix |
|---------|-------|-----|
| `tensorboard` import errors on macOS | torch not installed and not needed | switched to `tensorboardX` (API-compatible) |
| All scores reported as `None` | `numba` not installed; harness tried JIT | set `Sandbox(numba_accelerate=False)` |
| LLM responses empty | `gpt-5-nano` is a reasoning model; `max_tokens=512` was consumed by internal reasoning | raised to 4096 |
| Sample count off-by-one | `_global_samples_nums` starts at 1 | set `global_max_sample_num = N+1` |
| Analysis scripts couldn't find logs | logs are written relative to the harness cwd | accept `--log-dir` flag |

---

## Phase 2 — Behavioral deduplication funnel (Mar 28–31)

### Mar 28 — Three-level funnel implementation

- New module [`src/dedup/`](../src/dedup/): `dedup_config.py`,
  `probing.py`, `dedup_filter.py`. Probes executed in-process; no
  sandboxing overhead for the fast path.
- Insertion point: [`funsearch-baseline/implementation/evaluator.py`](../funsearch-baseline/implementation/evaluator.py)
  `analyse()`, after `_sample_to_program()` and before the sandbox call.
- Added `DEDUP_ENABLED` env toggle for ablation.

### Mar 29 — Code review + bug fixes

- Caught two issues in code review:
  1. Level 1 hash was keyed on the raw decision tuple but failed when a
     probe raised an exception; wrapped with defensive `None` handling
     and a separate "probe-failed" counter.
  2. The probe runner silently swallowed exceptions; surfaced them to the
     dedup stats so we can tell "duplicate" from "broken program".

### Mar 30 — Step 8 calibration and Milestone

- Calibrated Level 2 cosine threshold with a scatter plot of pairwise
  fingerprint cosine vs. score delta on 100 programs. Observed mean cosine
  ≈ 0.989 across near-unrelated programs → the discrete decision vector is
  too collapsed to discriminate. **Level 2 disabled; documented as negative
  result** in the paper.
- Milestone delivered (PR #5 merged into teammate's repo): baseline
  score −212.0, dedup filter rate 30.8%, net time saved 175.3 s.

### Mar 31 — Colab notebook for Milestone

- First full Colab notebook, reading from `baseline_50samples/` and
  `dedup_50samples_v2/` — snapshot preserved as
  [`notebooks/efficient_funsearch_colab_milestone.ipynb`](../notebooks/efficient_funsearch_colab_milestone.ipynb).

---

## Phase 3 — Diversity-guided selection (Apr 12)

### Apr 12 — Implementation + PR #6 review

- Modified `programs_database.py`'s cluster sampling to mix in
  `β · Div(cluster)` where `Div` is the mean pairwise cosine distance from
  the cluster's latest fingerprint to every other cluster in the same
  island. β = 0.3 initial with linear decay over 350 samples.
- **Review pitfall.** First commit (88a9af4) used raw Euclidean distance
  on discrete decision vectors — geometrically wrong for our fingerprints
  (captures magnitude, not pattern). Reverted and replaced with
  row-centered cosine distance (commit bba5a64), which normalizes away
  the overall decision-count skew and correctly captures *relative*
  behavioral differences.
- Restored the multi-dimensional signature after a regression where a
  dimensionality bug collapsed diversity scores to constants.

---

## Phase 4 — Ablation at 150 samples (Apr 13–16)

### Apr 13 — Layer 1 & Layer 2 runs

- **Layer 1** (`layer1_dedup_150_r1..r4`, `layer1_baseline_150_r1`):
  dedup alone confirmed to beat baseline on both score and first-hit.
- **Layer 2** (`layer2_dedup_div_150_r1..r4`): diversity successfully
  reduces dup rate 0.401 → 0.342 but does not improve final score or
  first-hit beyond dedup alone. Logged honestly as mixed.

### Apr 14 — n=4 stabilization

- Completed the n=4 ablation ladder. Aggregated via the first draft of
  `scripts/collect_results.py`.

---

## Sprint S1–S6 — Paper, BCR, ReEvo (Apr 13–22)

### Apr 14 — S1: baseline 150-sample + fingerprint export

- Finalized 150-sample baselines. Added `EXPORT_FINGERPRINTS=1` hook in
  `evaluator.py` (≤10 lines) writing `fingerprints.csv` next to
  `run_log.csv`.

### Apr 14 — S2: Colab sync to 150-sample logs

- Swapped all notebook CSV paths from Milestone logs to
  `layer1_baseline_150_r1` / `layer1_dedup_150_r1` /
  `layer2_dedup_div_150_r1`. Reserved a blank cell for BCR.

### Apr 15 — S3: BCR pipeline

- New [`scripts/compute_bcr_offline.py`](../scripts/compute_bcr_offline.py):
  fits k-means (K=8, random_state=42) on all collected fingerprints *once*,
  then replays the history to produce BCR(t) curves — avoids the online
  drift + relabel trap.
- Paper frames BCR as a post-hoc quality-diversity metric inspired by
  MAP-Elites (Mouret & Clune 2015).

### Apr 15–16 — S4: ReEvo

- 50-sample smoke test passed the go/no-go gate (best score < −212
  achieved).
- Full runs `layer4_reevo_150_r{2,3,4}`. ReEvo + dedup yielded the best
  end-to-end condition (−209.66 ± 0.59).
- New [`src/reevo/`](../src/reevo/); `sampler.py` triggers one short
  reflection LLM call per accepted program; `programs_database.py`
  appends top-3 reflections as comments to the next prompts.

### Apr 20–22 — S5: figures

- `plot_convergence_v2.py`, `plot_tsne_fingerprints.py`,
  `plot_reevo_breakthrough.py` — all four paper figures rendered from the
  checked-in CSVs.

### Apr 21 — Pre-delivery audit + three bug fixes + Final notebook

1. **Trim-bug regression guard.** Added a unit test covering fenced LLM
   outputs to prevent Phase-1's bug from silently returning.
2. **API retry cap.** [`funsearch-baseline/*llm_api.py`](../funsearch-baseline/funsearch_bin_packing_llm_api.py)
   had an implicit infinite retry; added request timeout + retry cap
   (commit 4df99b5).
3. **CSV row for fingerprint-failed samples.** Previously those were
   silently dropped from `run_log.csv`; now they appear with a
   `fingerprint=NaN` marker so the notebook can surface them.
4. Notebook upgraded to Final form with 19 code cells + 13 markdown cells,
   top-to-bottom runnable from the repo clone.

### Apr 22 — S6: paper delivery and repo close-out

- ICLR 2024 style paper at [`docs/report/main.tex`](../docs/report/main.tex),
  compiled to `main.pdf`. Five grader-risk findings fixed (commit 6d1d332):
  L1 bound calibrated to −201.2; Level 2 disablement justified with the
  mean-cosine number; diversity claim softened; Related Work demarcates our
  contribution from code-embedding approaches; every number in
  intro/abstract traceable to a log + aggregation script.

### Apr 22 (evening) — Notebook audit fixes (7 cells)

- Re-ran audit against the Final notebook: patched stale numbers (45%,
  100%, 30.8%, "further extends"), fixed a NaN display, and re-ran all
  cells. Commit dd71f40.

### Apr 26 — Pre-submission notebook review (P0 + P1 fixes)

Final pre-submission audit of `notebooks/efficient_funsearch_colab.ipynb`
against `background/Project_report_submit.md` requirements.

**P0 (correctness / Colab-runtime safety)**

1. Section 9 `LOG_DIR` nested-path bug — three cells set
   `LOG_DIR="funsearch-baseline/logs/..."` then `cd funsearch-baseline &&
   python ...`, which would write logs to
   `funsearch-baseline/funsearch-baseline/logs/...`. Fixed: `LOG_DIR` now
   relative to the script's cwd (`logs/...`), with an explanatory comment.
2. Setup cell missing `scikit-learn` — Section 7 imports
   `sklearn.manifold.TSNE` but the pip install line did not request it,
   so a fresh Colab runtime would fail. Added to the install line.
3. Softened "behaviorally equivalent" / "zero false positives" claims in
   §3 markdown (cells 11 & 15) to "equivalent on the probing suite
   (conservative proxy)" — probe-equivalence is a proxy for behavioral
   equivalence, not a proof.

**P1 (method completeness / report parity)**

4. Inserted a Phase 3 diversity-selection mechanism cell (markdown +
   demo) between the ablation conclusions and the BCR cell. Shows the
   `Combined = Perf + β·Div` formula, the linear `β` decay
   (β_init=0.3, decay_period=350), and a 3-cluster toy where β=0.3
   shifts ~95 % of the selection mass to the most novel cluster.
5. Added a 4-condition mean ± std convergence figure (the report's main
   figure) in §8 just before the summary table, so the figure and Table 1
   come from identical raw inputs (same `_best_so_far` reduction, same
   condition→seed mapping).

Both new code cells executed cleanly against the checked-in logs; new
4-condition figure visually matches `docs/figures/convergence_150.pdf`.
Total notebook size: 32 → 36 cells.

---

## Verification gates (passed for Final)

- `pytest -q` passes in the repo root.
- `ruff check .` clean (per-file ignores cover the baseline harness).
- Paper compiles warning-free with `latexmk -pdf main.tex`.
- Notebook runs top-to-bottom on a fresh Colab runtime reading only from
  `funsearch-baseline/logs/` and produces tables/figures matching the paper.
- Table 1 in the paper == `python scripts/collect_results.py` output.
