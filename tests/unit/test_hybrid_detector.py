"""
Unit tests for hybrid similarity detector.
"""

import pytest


# Check if sentence-transformers is available
def _has_sentence_transformers():
    try:
        import sentence_transformers  # noqa: F401

        return True
    except ImportError:
        return False


requires_embedding = pytest.mark.skipif(
    not _has_sentence_transformers(),
    reason="sentence-transformers not installed. Run in Google Colab.",
)


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
        from src.similarity.hybrid import HybridSimilarityDetector
        from src.normalizer.models import NormalizedProgram

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

    @requires_embedding
    def test_is_similar_different_programs(self):
        """Test that different programs are not detected as similar."""
        from src.similarity.hybrid import HybridSimilarityDetector
        from src.normalizer.models import NormalizedProgram

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

    @requires_embedding
    def test_find_similar(self):
        """Test finding similar programs in a list."""
        from src.similarity.hybrid import HybridSimilarityDetector
        from src.normalizer.models import NormalizedProgram

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
        from src.similarity.hybrid import HybridSimilarityDetector
        from src.normalizer.models import NormalizedProgram

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
