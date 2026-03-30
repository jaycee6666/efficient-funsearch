#!/usr/bin/env python3
"""Baseline analysis script for FunSearch bin packing experiment."""

import argparse
import datetime
import glob
import json
import os
import sys

import numpy as np
import pandas as pd

# Default log directory; can be overridden via --log-dir argument
_DEFAULT_LOG_DIR = "logs/baseline_50samples"


def load_json_samples(samples_dir: str) -> list[dict]:
    """Load all per-sample JSON files from the samples/ directory."""
    pattern = os.path.join(samples_dir, "samples_*.json")
    files = sorted(glob.glob(pattern))

    if not files:
        print(f"[WARNING] No JSON sample files found: {pattern}")
        return []

    samples = []
    for fpath in files:
        try:
            with open(fpath, encoding="utf-8") as f:
                data = json.load(f)
                # Support both single dict and list of dicts
                if isinstance(data, list):
                    samples.extend(data)
                elif isinstance(data, dict):
                    samples.append(data)
        except (json.JSONDecodeError, OSError) as e:
            print(f"[WARNING] Cannot read {fpath}: {e}")

    return samples


def compute_stats(samples: list[dict]) -> dict:
    """
    Compute core statistical metrics.

    Args:
    - samples: List of samples loaded from JSON, each containing score, sample_time, evaluate_time, etc.
    """
    total = len(samples)

    # --- 1. Filter valid samples (score is not null) ---
    successful = [s for s in samples if s.get("score") is not None]
    n_success = len(successful)
    # success_rate = number of successfully evaluated samples / total samples
    success_rate = round(n_success / total, 2) if total > 0 else 0.0

    scores = [s["score"] for s in successful]

    # --- 2. Score statistics ---
    if scores:
        arr = np.array(scores, dtype=float)
        best_score = float(np.max(arr))
        mean_score = float(np.mean(arr))
        std_score = float(np.std(arr))
        min_score = float(np.min(arr))
        max_score = float(np.max(arr))
        median_score = float(np.median(arr))
    else:
        best_score = mean_score = std_score = min_score = max_score = median_score = 0.0

    # --- 3. Natural deduplication rate ---
    # unique_score_count: number of distinct score values among successful samples
    # natural_dup_rate = 1 - (unique / successful), higher means more redundancy
    unique_scores = set(scores)
    unique_score_count = len(unique_scores)
    natural_dup_rate = (
        round(1.0 - unique_score_count / n_success, 2) if n_success > 0 else 0.0
    )

    # --- 4. Time statistics (filter out null values) ---
    sample_times = [
        s["sample_time"] for s in samples if s.get("sample_time") is not None
    ]
    eval_times = [
        s["evaluate_time"] for s in samples if s.get("evaluate_time") is not None
    ]
    avg_sample_time = float(np.mean(sample_times)) if sample_times else 0.0
    avg_eval_time = float(np.mean(eval_times)) if eval_times else 0.0

    # --- 5. Convergence curve ---
    # Sort by sample_order, track the running best score at each step
    ordered = sorted(
        [s for s in samples if s.get("score") is not None],
        key=lambda x: x.get("sample_order", 0),
    )
    convergence_curve = []
    current_best = float("-inf")
    for s in ordered:
        current_best = max(current_best, s["score"])
        convergence_curve.append(round(current_best, 6))

    return {
        "total_samples": total,
        "successful_samples": n_success,
        "success_rate": success_rate,
        "best_score": round(best_score, 6),
        "mean_score": round(mean_score, 6),
        "std_score": round(std_score, 6),
        "min_score": round(min_score, 6),
        "max_score": round(max_score, 6),
        "median_score": round(median_score, 6),
        "unique_score_count": unique_score_count,
        "natural_dup_rate": natural_dup_rate,
        "avg_eval_time_sec": round(avg_eval_time, 4),
        "avg_sample_time_sec": round(avg_sample_time, 4),
        "convergence_curve": convergence_curve,
    }


def main():
    parser = argparse.ArgumentParser(description="Analyze FunSearch baseline experiment logs.")
    parser.add_argument(
        "--log-dir",
        default=_DEFAULT_LOG_DIR,
        help=f"Log directory path (default: {_DEFAULT_LOG_DIR})",
    )
    args = parser.parse_args()

    LOG_DIR = args.log_dir
    SAMPLES_DIR = os.path.join(LOG_DIR, "samples")
    CSV_PATH = os.path.join(LOG_DIR, "run_log.csv")
    OUTPUT_PATH = os.path.join(LOG_DIR, "summary.json")

    if not os.path.isdir(LOG_DIR):
        print(f"[ERROR] Cannot find log directory: {LOG_DIR}")
        print("Usage: python scripts/analyze_baseline.py --log-dir <path>")
        sys.exit(1)

    # --- Load JSON samples ---
    samples = load_json_samples(SAMPLES_DIR)

    # --- If JSON samples are empty, try loading from CSV ---
    if not samples:
        if not os.path.isfile(CSV_PATH):
            print(f"[ERROR] Neither JSON samples nor CSV exist: {CSV_PATH}")
            sys.exit(1)
        print(f"[INFO] JSON samples are empty, loading from CSV instead: {CSV_PATH}")
        try:
            df = pd.read_csv(CSV_PATH)
        except Exception as e:
            print(f"[ERROR] Cannot read CSV: {e}")
            sys.exit(1)
        # Convert CSV rows to dict format consistent with JSON samples
        samples = df.to_dict(orient="records")
        for s in samples:
            # Convert NaN to None for consistent downstream handling
            for key in ("score", "sample_time", "evaluate_time"):
                if key in s and (s[key] != s[key]):  # NaN check
                    s[key] = None

    if not samples:
        print("[ERROR] No sample data available for analysis, exiting.")
        sys.exit(1)

    # --- Compute statistics ---
    stats = compute_stats(samples)

    # --- Build output JSON ---
    summary = {
        "run_config": {
            "max_samples": 50,
            "model": "gpt-5-nano",
            "dataset": "OR3",
            "date": str(datetime.date.today()),
        },
        "results": {
            "total_samples": stats["total_samples"],
            "successful_samples": stats["successful_samples"],
            "success_rate": stats["success_rate"],
            "best_score": stats["best_score"],
            "mean_score": stats["mean_score"],
            "std_score": stats["std_score"],
            "unique_score_count": stats["unique_score_count"],
            "natural_dup_rate": stats["natural_dup_rate"],
            "avg_eval_time_sec": stats["avg_eval_time_sec"],
            "avg_sample_time_sec": stats["avg_sample_time_sec"],
        },
        "convergence_curve": stats["convergence_curve"],
    }

    # --- Write JSON ---
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f"[DONE] Summary saved to: {OUTPUT_PATH}")

    # --- Print human-readable summary ---
    r = summary["results"]
    print("\n========== Baseline Experiment Summary ==========")
    print(f"  Date          : {summary['run_config']['date']}")
    print(f"  Model         : {summary['run_config']['model']}")
    print(f"  Dataset       : {summary['run_config']['dataset']}")
    print(f"  Total samples : {r['total_samples']}")
    print(f"  Successful    : {r['successful_samples']}  (success rate: {r['success_rate']:.0%})")
    print(f"  Best score    : {r['best_score']}")
    print(f"  Mean ± Std    : {r['mean_score']} ± {r['std_score']}")
    print(f"  Unique scores : {r['unique_score_count']}")
    # Higher natural_dup_rate means more redundancy, motivating FunSearch dedup optimization
    print(f"  Natural dup rate: {r['natural_dup_rate']:.0%}  (higher = more redundancy)")
    print(f"  Avg sample time : {r['avg_sample_time_sec']} s")
    print(f"  Avg eval time   : {r['avg_eval_time_sec']} s")
    print("=================================================\n")


if __name__ == "__main__":
    main()
