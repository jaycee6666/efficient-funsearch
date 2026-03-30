"""Probing instance definitions and behavioral fingerprint computation.

10 carefully designed bin-packing instances for fast behavioral fingerprint generation.
Each instance has 35-40 items, total items = 375, fingerprint vector dimension is fixed at 375.
"""

from __future__ import annotations

import signal
from typing import Callable

import numpy as np


# ============================================================
# 10 Probing instances (addressing TA feedback #1: Probing instance generation method)
# Design principles (redesigned after Step 8 experiments):
#   - Each instance has 35-40 items (up from 5-15), ensuring 8-15+ open bins
#   - capacity=150 as default (matching OR3 dataset), with 100 and 200 for variation
#   - Item sizes 20-140 (matching OR3 distribution range), avoiding degenerate scenarios
#   - Deterministic values (no randomness), ensuring reproducibility
#   - Removed degenerate instances (near_capacity / all_identical)
# ============================================================

PROBING_INSTANCES = [
    {
        # First 40 items from OR3 u500_00 (hardcoded), closest to the real evaluation scenario
        "name": "or3_sample",
        "capacity": 150,
        "items": [42, 69, 67, 57, 93, 90, 38, 36, 45, 42,
                  33, 79, 27, 57, 44, 84, 86, 92, 46, 38,
                  85, 33, 82, 73, 49, 70, 59, 23, 57, 72,
                  74, 69, 33, 42, 28, 46, 30, 64, 29, 74],  # 40 items
    },
    {
        # Consecutive medium sizes, pairwise packing possible, many half-full bins, fine-grained differentiation
        "name": "medium_uniform",
        "capacity": 150,
        "items": list(range(30, 70)),  # [30, 31, ..., 69], 40 items
    },
    {
        # Large items, at most 2 per bin, tight packing decisions
        "name": "large_items",
        "capacity": 150,
        "items": list(range(75, 110)),  # [75, 76, ..., 109], 35 items
    },
    {
        # Small items with many choices, non-monotonic pattern to avoid strategy convergence
        "name": "small_varied",
        "capacity": 150,
        "items": [20 + (i * 7) % 19 for i in range(40)],  # 40 items, range 20-38
    },
    {
        # 18 large + 18 small, maximum divergence when small items fill gaps
        "name": "bimodal",
        "capacity": 150,
        "items": [100 + i % 5 for i in range(18)]
              + [25 + i % 8 for i in range(18)],  # 36 items
    },
    {
        # Descending wide range, tests differences in FFD-like strategies
        "name": "descending_spread",
        "capacity": 150,
        "items": [140 - i * 3 for i in range(35)],  # [140, 137, ..., 38], 35 items
    },
    {
        # Ascending sequence, small items build bin states first -> large items cause bin selection divergence
        "name": "ascending_spread",
        "capacity": 150,
        "items": [25 + i * 3 for i in range(35)],  # [25, 28, ..., 127], 35 items
    },
    {
        # Sawtooth cycle, periodic size alternation
        "name": "sawtooth",
        "capacity": 150,
        "items": [(i % 6) * 20 + 30 for i in range(36)],  # [30,50,70,90,110,130]x6, 36 items
    },
    {
        # capacity=100, items ~50%, each item has 5+ feasible bins, very many choices
        "name": "tight_pairs",
        "capacity": 100,
        "items": [48 + (i * 3) % 11 for i in range(40)],  # 40 items, range 48-58
    },
    {
        # capacity=200, multiple items per bin, deep bin states
        "name": "wide_capacity",
        "capacity": 200,
        "items": [30 + (i * 13) % 71 for i in range(38)],  # 38 items, range 30-100
    },
]

# Total items across all probes = 40+40+35+40+36+35+35+36+40+38 = 375
TOTAL_FINGERPRINT_DIM = sum(len(p["items"]) for p in PROBING_INSTANCES)
assert TOTAL_FINGERPRINT_DIM == 375, f"Fingerprint dimension should be 375, got {TOTAL_FINGERPRINT_DIM}"


def _run_single_probe(
    priority_fn: Callable[[float, np.ndarray], np.ndarray],
    capacity: int,
    items: list[int],
) -> tuple[int, ...]:
    """Run online bin packing on a single probe instance, returning the decision sequence (bin index chosen at each step).

    This is a lightweight inline version of the bin-packing evaluation logic, independent of Sandbox.
    """
    bins = np.array([capacity], dtype=np.float64)
    decisions = []
    for item in items:
        # Find bins with enough remaining space
        valid = np.where(bins - item >= 0)[0]
        if len(valid) == 0:
            # Open a new bin
            bins = np.append(bins, float(capacity))
            valid = np.array([len(bins) - 1])
        # Use priority function to evaluate each available bin
        priorities = priority_fn(float(item), bins[valid])
        best = valid[np.argmax(priorities)]
        bins[best] -= item
        decisions.append(int(best))
    return tuple(decisions)


class _TimeoutError(Exception):
    """Probe execution timeout exception."""
    pass


def _timeout_handler(signum, frame):
    raise _TimeoutError("Probe execution timed out")


def compute_fingerprint(
    program_str: str,
    function_to_evolve: str,
    probes: list[dict] | None = None,
    timeout: int = 5,
) -> tuple[int, ...] | None:
    """Compute the behavioral fingerprint of a program (addressing TA feedback #3: precise fingerprint definition).

    For program p and probe set P = {p1, ..., p10}:
    1. For each probe pi, run online bin packing and record the bin index chosen at each step
    2. Single probe decision sequence: seq_i = (bin_chosen_1, ..., bin_chosen_n)
    3. Full fingerprint: F(p) = seq_1 || seq_2 || ... || seq_10 (concatenated into a 375-dim integer tuple)

    Args:
        program_str: Complete executable program string (containing priority function definition)
        function_to_evolve: Name of the function to extract (typically 'priority')
        probes: List of probes; None uses the default PROBING_INSTANCES
        timeout: Timeout in seconds

    Returns:
        375-dim integer tuple, or None (on execution failure)
    """
    if probes is None:
        probes = PROBING_INSTANCES

    try:
        # Execute the program with exec() and extract the priority function
        # Not using multiprocessing Sandbox because fork ~50ms is too slow
        namespace = {"np": np, "numpy": np}
        exec(program_str, namespace)

        priority_fn = namespace.get(function_to_evolve)
        if priority_fn is None:
            return None

        # Set up timeout protection (Unix only; skipped on Windows)
        use_alarm = hasattr(signal, 'SIGALRM')
        if use_alarm:
            old_handler = signal.signal(signal.SIGALRM, _timeout_handler)
            signal.alarm(timeout)

        try:
            # Run bin packing on each probe and concatenate decision sequences
            all_decisions: list[int] = []
            for probe in probes:
                seq = _run_single_probe(
                    priority_fn, probe["capacity"], probe["items"]
                )
                all_decisions.extend(seq)
            return tuple(all_decisions)
        finally:
            if use_alarm:
                signal.alarm(0)  # Cancel the timer
                signal.signal(signal.SIGALRM, old_handler)

    except Exception:
        # Any exception (syntax error, timeout, runtime error) returns None
        # The caller will skip Level 1/2 and proceed directly to normal Sandbox evaluation
        return None
