#!/usr/bin/env python3
"""Baseline analysis script for FunSearch bin packing experiment."""

import argparse
import json
import os
import glob
import datetime
import sys

import numpy as np
import pandas as pd


# 日志目录默认值；可通过 --log-dir 参数覆盖
_DEFAULT_LOG_DIR = "logs/baseline_50samples"


def load_json_samples(samples_dir: str) -> list[dict]:
    """从 samples/ 目录加载所有 per-sample JSON 文件。"""
    pattern = os.path.join(samples_dir, "samples_*.json")
    files = sorted(glob.glob(pattern))

    if not files:
        print(f"[警告] 未找到 JSON 样本文件：{pattern}")
        return []

    samples = []
    for fpath in files:
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)
                # 支持单个 dict 或 list of dicts
                if isinstance(data, list):
                    samples.extend(data)
                elif isinstance(data, dict):
                    samples.append(data)
        except (json.JSONDecodeError, OSError) as e:
            print(f"[警告] 无法读取 {fpath}：{e}")

    return samples


def compute_stats(samples: list[dict]) -> dict:
    """
    计算核心统计指标。

    参数说明：
    - samples: 从 JSON 加载的样本列表，每个样本含 score、sample_time、evaluate_time 等字段
    """
    total = len(samples)

    # --- 1. 过滤有效（score 非 null）样本 ---
    successful = [s for s in samples if s.get("score") is not None]
    n_success = len(successful)
    # 成功率 = 成功评估的样本数 / 总样本数
    success_rate = round(n_success / total, 2) if total > 0 else 0.0

    scores = [s["score"] for s in successful]

    # --- 2. Score 统计 ---
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

    # --- 3. 自然去重率（natural deduplication rate）---
    # unique_score_count：成功样本中不同 score 值的数量
    # natural_dup_rate = 1 - (unique / successful)，越高说明重复越多
    unique_scores = set(scores)
    unique_score_count = len(unique_scores)
    natural_dup_rate = (
        round(1.0 - unique_score_count / n_success, 2) if n_success > 0 else 0.0
    )

    # --- 4. 时间统计（过滤 null 值）---
    sample_times = [
        s["sample_time"] for s in samples if s.get("sample_time") is not None
    ]
    eval_times = [
        s["evaluate_time"] for s in samples if s.get("evaluate_time") is not None
    ]
    avg_sample_time = float(np.mean(sample_times)) if sample_times else 0.0
    avg_eval_time = float(np.mean(eval_times)) if eval_times else 0.0

    # --- 5. 收敛曲线（convergence curve）---
    # 按 sample_order 排序，记录每一步的历史最优 score
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
        help=f"日志目录路径（默认：{_DEFAULT_LOG_DIR}）",
    )
    args = parser.parse_args()

    LOG_DIR = args.log_dir
    SAMPLES_DIR = os.path.join(LOG_DIR, "samples")
    CSV_PATH = os.path.join(LOG_DIR, "run_log.csv")
    OUTPUT_PATH = os.path.join(LOG_DIR, "summary.json")

    if not os.path.isdir(LOG_DIR):
        print(f"[错误] 找不到日志目录：{LOG_DIR}")
        print(f"用法：python scripts/analyze_baseline.py --log-dir <路径>")
        sys.exit(1)

    # --- 加载 JSON 样本 ---
    samples = load_json_samples(SAMPLES_DIR)

    # --- 如果 JSON 样本为空，尝试从 CSV 加载 ---
    if not samples:
        if not os.path.isfile(CSV_PATH):
            print(f"[错误] JSON 样本和 CSV 均不存在：{CSV_PATH}")
            sys.exit(1)
        print(f"[信息] JSON 样本为空，改从 CSV 加载：{CSV_PATH}")
        try:
            df = pd.read_csv(CSV_PATH)
        except Exception as e:
            print(f"[错误] 无法读取 CSV：{e}")
            sys.exit(1)
        # 将 CSV 行转为与 JSON 样本一致的 dict 格式
        samples = df.to_dict(orient="records")
        for s in samples:
            # pandas 读取时 NaN 转为 None，方便后续统一处理
            for key in ("score", "sample_time", "evaluate_time"):
                if key in s and (s[key] != s[key]):  # NaN check
                    s[key] = None

    if not samples:
        print("[错误] 没有任何可分析的样本数据，退出。")
        sys.exit(1)

    # --- 计算统计 ---
    stats = compute_stats(samples)

    # --- 构建输出 JSON ---
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

    # --- 写入 JSON ---
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f"[完成] 摘要已保存至：{OUTPUT_PATH}")

    # --- 打印人类可读摘要 ---
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
    # natural_dup_rate 越高说明重复越严重，是 FunSearch 去重优化的动机
    print(f"  Natural dup rate: {r['natural_dup_rate']:.0%}  (higher = more redundancy)")
    print(f"  Avg sample time : {r['avg_sample_time_sec']} s")
    print(f"  Avg eval time   : {r['avg_eval_time_sec']} s")
    print("=================================================\n")


if __name__ == "__main__":
    main()
