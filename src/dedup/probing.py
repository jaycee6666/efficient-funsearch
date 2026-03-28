"""Probing 实例定义与行为指纹计算。

8 个精心设计的微型 bin-packing 实例，用于快速生成行为指纹。
总物品数 = 62，指纹向量维度固定为 62。
"""

from __future__ import annotations

import signal
from typing import Callable

import numpy as np


# ============================================================
# 8 个 Probing 实例（回应助教 #1: Probing instance 生成方式）
# 设计原则：
#   - 实例极小，总执行时间 <1ms
#   - 覆盖边界情况和正常情况
#   - 能区分本质不同的装箱策略
# ============================================================

PROBING_INSTANCES = [
    {
        "name": "tight_fit",
        "capacity": 100,
        "items": [50, 50, 100, 25, 75],      # 5 个物品，完美匹配识别
    },
    {
        "name": "all_identical",
        "capacity": 100,
        "items": [34] * 8,                    # 8 个物品，对称处理
    },
    {
        "name": "descending",
        "capacity": 150,
        "items": [140, 120, 100, 80, 60, 40, 20],  # 7 个物品，FFD 感知
    },
    {
        "name": "ascending",
        "capacity": 150,
        "items": [10, 20, 30, 40, 50, 60, 70],     # 7 个物品，顺序敏感
    },
    {
        "name": "near_capacity",
        "capacity": 100,
        "items": [99, 98, 97, 96, 95],        # 5 个物品，强制单物品/箱
    },
    {
        "name": "tiny_items",
        "capacity": 100,
        "items": [5] * 15,                    # 15 个物品，贪心装箱
    },
    {
        "name": "mixed",
        "capacity": 150,
        "items": [30, 90, 60, 120, 45, 15, 75],    # 7 个物品，真实分布
    },
    {
        "name": "adversarial",
        "capacity": 100,
        "items": [60, 40, 35, 65, 20, 80, 45, 55], # 8 个物品，区分 BF/FF
    },
]

# 所有探针总物品数 = 5+8+7+7+5+15+7+8 = 62
TOTAL_FINGERPRINT_DIM = sum(len(p["items"]) for p in PROBING_INSTANCES)
assert TOTAL_FINGERPRINT_DIM == 62, f"指纹维度应为 62，实际 {TOTAL_FINGERPRINT_DIM}"


def _run_single_probe(
    priority_fn: Callable[[float, np.ndarray], np.ndarray],
    capacity: int,
    items: list[int],
) -> tuple[int, ...]:
    """对单个探针运行在线装箱，返回决策序列（每步选择的箱子索引）。

    这是 bin-packing 评估逻辑的轻量内联版本，不依赖 Sandbox。
    """
    bins = np.array([capacity], dtype=np.float64)
    decisions = []
    for item in items:
        # 找到有足够空间的箱子
        valid = np.where(bins - item >= 0)[0]
        if len(valid) == 0:
            # 开一个新箱子
            bins = np.append(bins, float(capacity))
            valid = np.array([len(bins) - 1])
        # 用 priority 函数评估每个可用箱子
        priorities = priority_fn(float(item), bins[valid])
        best = valid[np.argmax(priorities)]
        bins[best] -= item
        decisions.append(int(best))
    return tuple(decisions)


class _TimeoutError(Exception):
    """探针执行超时异常。"""
    pass


def _timeout_handler(signum, frame):
    raise _TimeoutError("探针执行超时")


def compute_fingerprint(
    program_str: str,
    function_to_evolve: str,
    probes: list[dict] | None = None,
    timeout: int = 5,
) -> tuple[int, ...] | None:
    """计算程序的行为指纹（回应助教 #3: 指纹精确定义）。

    对程序 p 和探针集 P = {p₁, ..., p₈}:
    1. 对每个探针 pᵢ，执行在线装箱，记录每步选择的箱子索引
    2. 单探针决策序列: seq_i = (bin_chosen_1, ..., bin_chosen_n)
    3. 完整指纹: F(p) = seq_1 ⊕ seq_2 ⊕ ... ⊕ seq_8（拼接为 62 维整数元组）

    Args:
        program_str: 完整可执行的程序字符串（包含 priority 函数定义）
        function_to_evolve: 要提取的函数名（通常是 'priority'）
        probes: 探针列表，None 则使用默认 PROBING_INSTANCES
        timeout: 超时秒数

    Returns:
        62 维整数元组，或 None（执行失败时）
    """
    if probes is None:
        probes = PROBING_INSTANCES

    try:
        # 用 exec() 执行程序，提取 priority 函数
        # 不用 multiprocessing Sandbox，因为 fork ~50ms 太慢
        namespace = {"np": np, "numpy": np}
        exec(program_str, namespace)

        priority_fn = namespace.get(function_to_evolve)
        if priority_fn is None:
            return None

        # 设置超时保护（仅 Unix，Windows 下跳过超时保护）
        use_alarm = hasattr(signal, 'SIGALRM')
        if use_alarm:
            old_handler = signal.signal(signal.SIGALRM, _timeout_handler)
            signal.alarm(timeout)

        try:
            # 对每个探针运行 binpack，拼接决策序列
            all_decisions: list[int] = []
            for probe in probes:
                seq = _run_single_probe(
                    priority_fn, probe["capacity"], probe["items"]
                )
                all_decisions.extend(seq)
            return tuple(all_decisions)
        finally:
            if use_alarm:
                signal.alarm(0)  # 取消定时器
                signal.signal(signal.SIGALRM, old_handler)

    except Exception:
        # 任何异常（语法错误、超时、运行时错误）都返回 None
        # 调用方会跳过 Level 1/2，直接进入正常 Sandbox 评估
        return None
