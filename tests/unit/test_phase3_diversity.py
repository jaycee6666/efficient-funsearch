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
        # (1,0) centered -> (0.5,-0.5) normalized -> (1/sqrt2, -1/sqrt2)
        # (0,1) centered -> (-0.5,0.5) normalized -> (-1/sqrt2, 1/sqrt2)
        # After centering these are anti-correlated: cosine_sim = -1, distance = 2.0
        sigs = [(1.0, 0.0), (0.0, 1.0)]
        result = _compute_diversity_scores(sigs)
        assert result[0] == pytest.approx(2.0, abs=1e-6)
        assert result[1] == pytest.approx(2.0, abs=1e-6)

    def test_proportional_clusters_have_zero_diversity(self):
        # (-100,-200) and (-200,-400) have the same relative pattern (scaled versions)
        # Centering: (-100,-200) -> mean=-150 -> (50,-50) normalized -> (1/sqrt2,-1/sqrt2)
        #            (-200,-400) -> mean=-300 -> (100,-100) normalized -> (1/sqrt2,-1/sqrt2)
        # cosine_sim = 1.0, distance = 0.0
        sigs = [(-100.0, -200.0), (-200.0, -400.0)]
        result = _compute_diversity_scores(sigs)
        assert result[0] == pytest.approx(0.0, abs=1e-6)
        assert result[1] == pytest.approx(0.0, abs=1e-6)

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

    def test_zero_variance_clusters_have_zero_diversity(self):
        # Both clusters score identically on all tests: no discriminating pattern.
        # After row-centering the vectors become (0,...,0); cosine similarity is
        # undefined. These clusters should be assigned diversity=0, not 1.0.
        sigs = [(-1.0, -1.0), (-2.0, -2.0)]
        result = _compute_diversity_scores(sigs)
        assert result[0] == pytest.approx(0.0, abs=1e-6)
        assert result[1] == pytest.approx(0.0, abs=1e-6)

    def test_returns_array_of_correct_length(self):
        sigs = [(-212.0,), (-300.0,), (-250.0,), (-180.0,)]
        result = _compute_diversity_scores(sigs)
        assert len(result) == 4
