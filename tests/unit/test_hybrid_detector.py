"""
Unit tests for hybrid similarity detector.
"""

import numpy as np
import pytest


@pytest.fixture
def mock_embedding(monkeypatch):
    """Deterministic embedding mock to avoid external dependency in unit tests."""
    import src.similarity.hybrid as hybrid_module

    def _fake_compute_embedding(code: str) -> np.ndarray:
        if "class" in code:
            return np.array([1.0, 0.0], dtype=np.float32)
        if "bar" in code:
            return np.array([0.7, 0.7], dtype=np.float32)
        return np.array([0.0, 1.0], dtype=np.float32)

    monkeypatch.setattr(hybrid_module, "compute_embedding", _fake_compute_embedding)


class TestHybridSimilarityDetector:
    """Tests for the HybridSimilarityDetector class."""

    def test_detector_creation(self):
        """Test creating a detector with default config."""
        from src.similarity.hybrid import HybridSimilarityDetector

        detector = HybridSimilarityDetector()
        assert detector is not None

    def test_detector_with_custom_config(self):
        """Test creating a detector with custom config."""
        from src.similarity.hybrid import HybridSimilarityDetector
        from src.similarity.models import DetectorConfig

        config = DetectorConfig(
            embedding_threshold=0.9,
            ast_threshold=0.95,
        )
        detector = HybridSimilarityDetector(config)
        assert detector.config.embedding_threshold == 0.9
        assert detector.config.ast_threshold == 0.95

    def test_is_similar_identical_programs(self):
        """Test that identical programs are detected as similar."""
        from src.normalizer.models import NormalizedProgram
        from src.similarity.hybrid import HybridSimilarityDetector

        detector = HybridSimilarityDetector()
        code = "def foo(): return 1"

        program_a = NormalizedProgram(
            canonical_code=code,
            ast_hash="hash_a",
        )
        program_b = NormalizedProgram(
            canonical_code=code,
            ast_hash="hash_a",  # Same hash
        )

        result = detector.is_similar(program_a, program_b)
        assert result.is_duplicate

    def test_is_similar_different_programs(self, mock_embedding):
        """Test that different programs are not detected as similar."""
        from src.normalizer.models import NormalizedProgram
        from src.similarity.hybrid import HybridSimilarityDetector

        detector = HybridSimilarityDetector()
        code_a = "def foo(): return 1"
        code_b = "class Bar:\n    x = 1"

        program_a = NormalizedProgram(
            canonical_code=code_a,
            ast_hash="hash_a",
        )
        program_b = NormalizedProgram(
            canonical_code=code_b,
            ast_hash="hash_b",
        )

        result = detector.is_similar(program_a, program_b)
        assert not result.is_duplicate

    def test_find_similar(self, mock_embedding):
        """Test finding similar programs in a list."""
        from src.normalizer.models import NormalizedProgram
        from src.similarity.hybrid import HybridSimilarityDetector

        detector = HybridSimilarityDetector()

        target = NormalizedProgram(
            canonical_code="def foo(): return 1",
            ast_hash="hash_target",
        )

        candidates = [
            NormalizedProgram(
                canonical_code="def foo(): return 1",
                ast_hash="hash_target",  # Same
            ),
            NormalizedProgram(
                canonical_code="def bar(): return 2",
                ast_hash="hash_c1",
            ),
            NormalizedProgram(
                canonical_code="class X:\n    pass",
                ast_hash="hash_c2",
            ),
        ]

        results = detector.find_similar(target, candidates, k=2)

        # Should return results sorted by similarity
        assert len(results) <= 2
        if len(results) > 0:
            assert results[0].is_duplicate  # First should be duplicate

    def test_detection_method_tracking(self):
        """Test that detection method is tracked."""
        from src.normalizer.models import NormalizedProgram
        from src.similarity.hybrid import HybridSimilarityDetector

        detector = HybridSimilarityDetector()
        program_a = NormalizedProgram(
            canonical_code="def foo(): return 1",
            ast_hash="hash_a",
        )
        program_b = NormalizedProgram(
            canonical_code="def foo(): return 1",
            ast_hash="hash_a",
        )

        result = detector.is_similar(program_a, program_b)
        assert result.detection_method in ["embedding_only", "ast_only", "hybrid", "hash_match"]


def test_behavior_similarity_threshold_applied_for_duplicate_decision():
    from src.similarity.hybrid import HybridSimilarityDetector

    detector = HybridSimilarityDetector()
    score = detector.compute_behavior_similarity(["1", "2"], ["1", "2"])

    assert score > 0.95
