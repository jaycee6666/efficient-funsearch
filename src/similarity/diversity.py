"""Diversity-guided candidate ranking utilities."""

from __future__ import annotations


def rank_candidates(
    candidates: list[str],
    perf_scores: dict[str, float],
    diversity_scores: dict[str, float],
    beta: float = 0.2,
) -> list[str]:
    """Rank candidates by performance + diversity weighted score."""
    return sorted(
        candidates,
        key=lambda c: perf_scores[c] + beta * diversity_scores[c],
        reverse=True,
    )
