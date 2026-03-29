"""Probing 实例定义与行为指纹计算。

10 个精心设计的 bin-packing 实例，用于快速生成行为指纹。
每个实例 35-40 个物品，总物品数 = 375，指纹向量维度固定为 375。
"""

from __future__ import annotations

import signal
from typing import Callable

import numpy as np


# ============================================================
# 10 个 Probing 实例（回应助教 #1: Probing instance 生成方式）
# 设计原则（Step 8 实验后重新设计）：
#   - 每个实例 35-40 个物品（原 5-15 个），确保 8-15+ 个打开的箱子
#   - capacity=150 为主（匹配 OR3 数据集），另有 100 和 200 做变化
#   - 物品大小 20-140（匹配 OR3 分布范围），避免退化场景
#   - 确定性值（无随机数），保证可复现
#   - 移除退化实例（near_capacity / all_identical）
# ============================================================

PROBING_INSTANCES = [
    {
        # OR3 u500_00 的前 40 个物品（硬编码），最贴近真实评估场景
        "name": "or3_sample",
        "capacity": 150,
        "items": [42, 69, 67, 57, 93, 90, 38, 36, 45, 42,
                  33, 79, 27, 57, 44, 84, 86, 92, 46, 38,
                  85, 33, 82, 73, 49, 70, 59, 23, 57, 72,
                  74, 69, 33, 42, 28, 46, 30, 64, 29, 74],  # 40 个物品
    },
    {
        # 连续中等大小，可配对装箱，箱子半满状态多，精细区分
        "name": "medium_uniform",
        "capacity": 150,
        "items": list(range(30, 70)),  # [30, 31, ..., 69]，40 个物品
    },
    {
        # 大物品，每箱最多 2 个，紧密装填决策
        "name": "large_items",
        "capacity": 150,
        "items": list(range(75, 110)),  # [75, 76, ..., 109]，35 个物品
    },
    {
        # 小物品多选择，非单调模式避免策略趋同
        "name": "small_varied",
        "capacity": 150,
        "items": [20 + (i * 7) % 19 for i in range(40)],  # 40 个物品，范围 20-38
    },
    {
        # 18 大 + 18 小，小物品填缝隙时分歧最大
        "name": "bimodal",
        "capacity": 150,
        "items": [100 + i % 5 for i in range(18)]
              + [25 + i % 8 for i in range(18)],  # 36 个物品
    },
    {
        # 递减宽幅，测试 FFD 类策略差异
        "name": "descending_spread",
        "capacity": 150,
        "items": [140 - i * 3 for i in range(35)],  # [140, 137, ..., 38]，35 个物品
    },
    {
        # 递增序列，小物品先建箱态→大物品择箱分歧
        "name": "ascending_spread",
        "capacity": 150,
        "items": [25 + i * 3 for i in range(35)],  # [25, 28, ..., 127]，35 个物品
    },
    {
        # 锯齿循环，周期性大小交替
        "name": "sawtooth",
        "capacity": 150,
        "items": [(i % 6) * 20 + 30 for i in range(36)],  # [30,50,70,90,110,130]×6，36 个物品
    },
    {
        # capacity=100，物品 ~50%，每个物品 5+ 可行箱，极多选择
        "name": "tight_pairs",
        "capacity": 100,
        "items": [48 + (i * 3) % 11 for i in range(40)],  # 40 个物品，范围 48-58
    },
    {
        # capacity=200，多物品/箱，深层箱态
        "name": "wide_capacity",
        "capacity": 200,
        "items": [30 + (i * 13) % 71 for i in range(38)],  # 38 个物品，范围 30-100
    },
]

# 所有探针总物品数 = 40+40+35+40+36+35+35+36+40+38 = 375
TOTAL_FINGERPRINT_DIM = sum(len(p["items"]) for p in PROBING_INSTANCES)
assert TOTAL_FINGERPRINT_DIM == 375, f"指纹维度应为 375，实际 {TOTAL_FINGERPRINT_DIM}"


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

    对程序 p 和探针集 P = {p₁, ..., p₁₀}:
    1. 对每个探针 pᵢ，执行在线装箱，记录每步选择的箱子索引
    2. 单探针决策序列: seq_i = (bin_chosen_1, ..., bin_chosen_n)
    3. 完整指纹: F(p) = seq_1 ⊕ seq_2 ⊕ ... ⊕ seq_10（拼接为 375 维整数元组）

    Args:
        program_str: 完整可执行的程序字符串（包含 priority 函数定义）
        function_to_evolve: 要提取的函数名（通常是 'priority'）
        probes: 探针列表，None 则使用默认 PROBING_INSTANCES
        timeout: 超时秒数

    Returns:
        375 维整数元组，或 None（执行失败时）
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
