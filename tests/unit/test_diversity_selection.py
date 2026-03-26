"""Unit tests for diversity-guided ranking."""

from importlib import import_module


def test_rank_candidates_combines_performance_and_diversity():
    rank_candidates = import_module("src.similarity.diversity").rank_candidates

    ranked = rank_candidates(
        candidates=["a", "b"],
        perf_scores={"a": 0.8, "b": 0.79},
        diversity_scores={"a": 0.1, "b": 0.6},
        beta=0.2,
    )

    assert ranked[0] == "b"
