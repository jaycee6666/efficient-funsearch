#!/usr/bin/env python3
"""
Aggregate run_log.csv across all conditions and runs.

Outputs a summary table with mean±std for:
  - best_score
  - sample at which best was first achieved
  - dup_rate (fraction of duplicates)
  - valid_rate (fraction of samples with a real score)

Usage (from efficient-funsearch/):
  python scripts/collect_results.py
"""

import csv
import math
import os
import statistics

# ---------------------------------------------------------------------------
# Configuration: map condition label → list of log dirs (relative to LOG_BASE)
# ---------------------------------------------------------------------------
LOG_BASE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "funsearch-baseline", "logs"
)

CONDITIONS = {
    "baseline":  ["layer1_baseline_150_r1", "layer1_baseline_150_r2"],
    "dedup":     ["layer1_dedup_150_r1", "layer1_dedup_150_r2",
                  "layer1_dedup_150_r3", "layer1_dedup_150_r4"],
    "dedup+div": ["layer2_dedup_div_150_r1", "layer2_dedup_div_150_r2",
                  "layer2_dedup_div_150_r3", "layer2_dedup_div_150_r4"],
    "reevo":     ["layer4_reevo_test_r1", "layer4_reevo_150_r2",
                  "layer4_reevo_150_r3", "layer4_reevo_150_r4"],
}

# Scores below this threshold are treated as failed programs (e.g. -500)
SCORE_FAIL_THRESHOLD = -400


def _load_run(log_dir: str) -> dict:
    """Load one run_log.csv and return per-run metrics."""
    csv_path = os.path.join(LOG_BASE, log_dir, "run_log.csv")
    rows = []
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    best_score = None
    best_sample = None
    n_dup = 0
    n_total = 0

    for row in rows:
        raw_order = row.get("sample_order", "None")
        if raw_order in ("None", "", "nan"):
            continue  # skip the initialization row
        n_total += 1

        if row.get("is_duplicate", "").lower() in ("true", "1"):
            n_dup += 1

        raw_score = row.get("score", "")
        try:
            s = float(raw_score)
        except (ValueError, TypeError):
            continue
        if math.isnan(s) or s <= SCORE_FAIL_THRESHOLD:
            continue

        if best_score is None or s > best_score:
            best_score = s
            best_sample = int(float(raw_order))

    dup_rate = n_dup / n_total if n_total > 0 else float("nan")
    return {
        "best_score": best_score,
        "best_sample": best_sample,
        "dup_rate": dup_rate,
        "n_total": n_total,
    }


def _fmt(values: list, fmt: str = ".2f") -> str:
    """Format mean±std, or just the value if n=1."""
    clean = [v for v in values if v is not None and not math.isnan(v)]
    if not clean:
        return "N/A"
    mean = statistics.mean(clean)
    if len(clean) < 2:
        return format(mean, fmt)
    std = statistics.stdev(clean)
    return f"{mean:{fmt}} ± {std:{fmt}}"


def main():
    rows_out = []
    for cond, dirs in CONDITIONS.items():
        runs = [_load_run(d) for d in dirs]

        best_scores = [r["best_score"] for r in runs]
        best_samples = [r["best_sample"] for r in runs]
        dup_rates = [r["dup_rate"] for r in runs]

        rows_out.append({
            "condition": cond,
            "n": len(runs),
            "best_score": _fmt(best_scores, ".2f"),
            "best_score_range": (
                f"{min(s for s in best_scores if s):.2f} ~ "
                f"{max(s for s in best_scores if s):.2f}"
            ),
            "best_sample": _fmt(best_samples, ".0f"),
            "dup_rate": _fmt(dup_rates, ".3f"),
        })

    # Print table
    header = f"{'Condition':<12} {'n':>3}  {'best_score (mean±std)':>22}  "
    header += f"{'range':>22}  {'1st best (mean±std)':>20}  {'dup_rate (mean±std)':>20}"
    print(header)
    print("-" * len(header))
    for r in rows_out:
        print(
            f"{r['condition']:<12} {r['n']:>3}  {r['best_score']:>22}  "
            f"{r['best_score_range']:>22}  {r['best_sample']:>20}  {r['dup_rate']:>20}"
        )


if __name__ == "__main__":
    main()
