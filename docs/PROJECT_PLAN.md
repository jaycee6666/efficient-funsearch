# Project Plan — Efficient FunSearch

A condensed English snapshot of the overall design and phase breakdown.
The compiled paper (`docs/report/main.pdf`) is the primary artifact; this
document records the methodology and roadmap behind it.

## Problem

[FunSearch](https://www.nature.com/articles/s41586-023-06924-6) (DeepMind,
*Nature* 2024) uses an LLM-driven evolutionary loop to discover heuristics.
The loop repeatedly evaluates every LLM-generated candidate on the target
task, but in practice many candidates are **functionally equivalent** while
being **syntactically distinct** — they waste both API budget and wall-clock
time on redundant evaluation. Our 50- and 150-sample baseline runs on the
online bin-packing benchmark observed a ~45% natural duplicate rate (programs
that produce exactly the same bin-packing decisions on the evaluation set).

Our goal: reduce wasted evaluation without hurting final heuristic quality.
We add two orthogonal mechanisms, framed as **"defend and explore"**:

- **Defend (behavioral deduplication):** detect functionally equivalent
  candidates *before* full evaluation and skip them.
- **Explore (diversity-guided selection):** bias the prompt-sampling
  distribution toward clusters whose behavior is under-represented.

A third mechanism, **ReEvo** (reflective evolution), was added in the final
sprint to test whether reflections injected into prompts compose with the
other two.

## Method

### Three-Level Behavioral Deduplication Funnel

For each LLM-generated candidate, we run an increasingly expensive cascade of
checks *before* invoking the slow sandbox evaluation:

| Level | Check | Cost | Hit action |
|-------|-------|------|------------|
| 0 | AST normalization (variable rename, strip docstrings) + SHA256 of canonical source | µs | exact syntactic match → skip |
| 1 | Behavioral fingerprint: run candidate on 10 probing instances, record the decision sequence (bin index chosen at each step), SHA256 the tuple | ms | exact functional match → skip |
| 2 | Cosine similarity over fingerprint vectors, threshold τ | ms | near-duplicate → **disabled in the final config** (see note below) |

**Level 2 is disabled in the submitted configuration.** Our calibration study
found that high-dimensional discrete decision vectors collapse to mean cosine
≈ 0.989, producing unacceptable false-positive rates. We report this as a
negative finding in the paper and retain only the first two levels, which
together already catch ~30–40% of samples as duplicates.

### Probing Instances (10)

A carefully chosen set covering tight-fit, all-identical, descending,
ascending, near-capacity, tiny-items, mixed, and adversarial cases. See the
paper §2.2 and Appendix B for the full table; each probe runs in microseconds.

### Diversity-Guided Selection

On the programs database's island-level sampler we add a row-centered cosine
distance term:

```
Score(cluster) = Perf(cluster) + β · Div(cluster)
β_t = β₀ · max(0, 1 − t / T_decay),  β₀ = 0.3, T_decay = 350
```

`Div(cluster)` is the mean pairwise cosine distance from the cluster's latest
fingerprint to all other clusters' fingerprints within the same island. β
decays linearly so that early iterations explore, later iterations exploit.

### ReEvo (Reflective Evolution, Sprint S4)

After each accepted program, a short LLM-written reflection is stored
(top-20 by score). The three best reflections are appended as comments to
subsequent prompts, giving the generator a lightweight memory of what has
worked. Independent toggle `REEVO_ENABLED=1`.

## Phases and Sprints

| Phase | Dates (2026) | Deliverable | Status |
|-------|--------------|-------------|--------|
| 1 | Mar 27–31 | Baseline FunSearch wired up; trim-bug fixed; Milestone report | ✅ |
| 2 | Apr 1–7   | Behavioral dedup funnel (Levels 0–2), probing instances, calibration | ✅ |
| 3 | Apr 12    | Diversity-guided selection on islands with decaying β | ✅ |
| 4 | Apr 12–16 | Ablation: 150-sample runs × n=4 per condition | ✅ |
| S1–S3 | Apr 13–17 | Fingerprint export for BCR, Colab on 150-sample logs, offline BCR pipeline | ✅ |
| S4 | Apr 18–19 | ReEvo, 150-sample runs | ✅ |
| S5 | Apr 20–22 | Convergence, BCR, t-SNE figures; aggregate results | ✅ |
| S6 | Apr 22    | ICLR-format paper + final Colab | ✅ |

Phase 1–4 cover the original project plan; S1–S6 form a final sprint that
adds BCR (behavioral coverage rate) as a post-hoc quality-diversity metric,
ReEvo as an optional mechanism, and the paper/notebook packaging.

## Final Results (150 samples, n=4 per condition except baseline n=2)

| Condition | Best score | 1st-hit sample | Dup rate |
|-----------|------------|----------------|----------|
| baseline | −210.52 ± 1.31 | 146 ± 2 | N/A |
| dedup | **−210.04 ± 1.00** | **90 ± 36** | 0.401 ± 0.046 |
| dedup + diversity | −210.20 ± 0.68 | 108 ± 21 | 0.342 ± 0.067 |
| dedup + ReEvo | **−209.66 ± 0.59** | 101 ± 16 | **0.314 ± 0.034** |

Headline takeaways:

1. **Behavioral dedup is the main result.** +0.48 score uplift over baseline
   and first-hit 56 samples earlier.
2. **ReEvo is the strongest end-to-end condition** when composed with dedup.
3. **Diversity-guided selection is mixed.** The mechanism works (dup rate
   drops 0.401 → 0.342), but final score and first-hit do not beat dedup
   alone. The paper reports this honestly as a negative-to-mixed result.

## Key Design Choices

- **Direct source-level integration.** We edit the course-provided
  `funsearch-baseline` harness in place rather than monkey-patching. Each of
  the three mechanisms is a single environment-variable switch
  (`DEDUP_ENABLED`, `DIVERSITY_ENABLED`, `REEVO_ENABLED`), enabling arbitrary
  subsets for ablation without code changes.
- **Behavioral fingerprint over code embedding.** We intentionally do not
  bring in a code-embedding model (e.g., CodeBERT); behavioral fingerprints
  on problem-specific probes are faster and more tightly aligned with the
  functional-equivalence question we care about.
- **Offline BCR.** We fit k-means *once* on all collected fingerprints and
  replay the history to get BCR(t), avoiding online cluster drift and
  relabeling issues that would make the curve uninterpretable.
- **Conservative false-positive control.** Level 1 uses exact tuple hashing
  (zero false positives by construction); Level 2 would sit on top of that
  but was disabled after calibration. Periodic spot-checks re-run "flagged
  duplicates" through full evaluation to sanity-check Level 1 in dev.

## Key Innovations

1. **Behavioral fingerprinting for LLM program search.** To our knowledge,
   the first deployment of problem-specific probe-based functional
   equivalence checking inside a FunSearch-style loop.
2. **Defend-and-Explore framing.** Dedup (defense) and diversity (explore)
   are complementary; we report both independently and composed.
3. **Systematic ablation ladder.** Four conditions (baseline / dedup /
   dedup+diversity / dedup+ReEvo) cleanly quantify each mechanism's marginal
   contribution.
4. **End-to-end time accounting.** We report net wall-clock savings that
   include dedup overhead, not just "candidates skipped."

## References (for the full bibliography see `docs/report/final.bib`)

Core: Romera-Paredes et al., *Nature* 2024 (FunSearch); Lehman & Stanley,
*Evol. Comput.* 2011 (Novelty Search); Mouret & Clune, 2015 (MAP-Elites);
Ye et al., NeurIPS 2024 (ReEvo); van Stein et al. 2025 (behavior-space
analysis of LLM meta-heuristic discovery); Sim et al. 2025 (LLM-evolved
heuristics for bin packing benchmark).
