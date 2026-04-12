"""Unit tests for Phase 3 diversity-guided cluster selection."""
import sys
import os

import numpy as np
import pytest

# Allow importing from funsearch-baseline
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../funsearch-baseline'))

from implementation.programs_database import _normalize_scores, _compute_diversity_scores


class TestNormalizeScores:
    def test_normal_range(self):
        scores = np.array([-300.0, -212.0, -250.0])
        result = _normalize_scores(scores)
        assert result.min() == pytest.approx(0.0)
        assert result.max() == pytest.approx(1.0)

    def test_all_equal_returns_zeros(self):
        scores = np.array([-212.0, -212.0, -212.0])
        result = _normalize_scores(scores)
        np.testing.assert_array_equal(result, np.zeros(3))

    def test_single_element(self):
        scores = np.array([-212.0])
        result = _normalize_scores(scores)
        np.testing.assert_array_equal(result, np.zeros(1))


class TestComputeDiversityScores:
    def test_single_cluster_returns_zero(self):
        sigs = [(-212.0, -300.0)]
        result = _compute_diversity_scores(sigs)
        np.testing.assert_array_equal(result, np.zeros(1))

    def test_two_identical_clusters_have_zero_diversity(self):
        sigs = [(-212.0, -300.0), (-212.0, -300.0)]
        result = _compute_diversity_scores(sigs)
        assert result[0] == pytest.approx(0.0, abs=1e-6)
        assert result[1] == pytest.approx(0.0, abs=1e-6)

    def test_orthogonal_clusters_have_max_diversity(self):
        # Two clusters whose signatures are orthogonal vectors
        sigs = [(1.0, 0.0), (0.0, 1.0)]
        result = _compute_diversity_scores(sigs)
        # cosine similarity = 0 → distance = 1
        assert result[0] == pytest.approx(1.0, abs=1e-6)
        assert result[1] == pytest.approx(1.0, abs=1e-6)

    def test_diverse_cluster_gets_higher_score(self):
        # sigs[2] is very different from sigs[0] and sigs[1] which are similar
        sigs = [
            (1.0, 0.01),   # similar to next
            (1.0, 0.02),   # similar to prev
            (0.01, 1.0),   # very different from both
        ]
        result = _compute_diversity_scores(sigs)
        # The outlier cluster should have higher diversity score
        assert result[2] > result[0]
        assert result[2] > result[1]

    def test_returns_array_of_correct_length(self):
        sigs = [(-212.0,), (-300.0,), (-250.0,), (-180.0,)]
        result = _compute_diversity_scores(sigs)
        assert len(result) == 4
