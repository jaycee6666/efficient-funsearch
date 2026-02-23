"""
Unit tests for code embedding.

Note: These tests require sentence-transformers. Run in Google Colab or
install with: pip install sentence-transformers
"""

import pytest

# Skip all tests in this module if sentence-transformers is not installed
pytest.importorskip(
    "sentence_transformers", reason="sentence-transformers not installed. Run in Google Colab."
)

import numpy as np


class TestCodeEmbedding:
    """Tests for code embedding functionality."""

    def test_compute_embedding_returns_vector(self):
        """Test that compute_embedding returns a vector."""
        from src.similarity.embedding import compute_embedding

        code = "def foo(): return 1"
        embedding = compute_embedding(code)

        assert isinstance(embedding, np.ndarray)
        assert len(embedding) > 0

    def test_embedding_dimension(self):
        """Test that embedding has expected dimension."""
        from src.similarity.embedding import compute_embedding, get_embedding_dimension

        code = "def foo(): return 1"
        embedding = compute_embedding(code)
        dim = get_embedding_dimension()

        assert len(embedding) == dim

    def test_same_code_same_embedding(self):
        """Test that same code produces same embedding."""
        from src.similarity.embedding import compute_embedding

        code = "def foo(): return 1"
        embedding1 = compute_embedding(code)
        embedding2 = compute_embedding(code)

        np.testing.assert_array_almost_equal(embedding1, embedding2)

    def test_cosine_similarity(self):
        """Test cosine similarity computation."""
        from src.similarity.embedding import compute_embedding, cosine_similarity

        code1 = "def foo(): return 1"
        code2 = "def foo(): return 2"
        code3 = "def bar(x): return x * 2"

        emb1 = compute_embedding(code1)
        emb2 = compute_embedding(code2)
        emb3 = compute_embedding(code3)

        # Similar code should have high similarity
        sim_12 = cosine_similarity(emb1, emb2)
        assert 0.5 < sim_12 <= 1.0

        # Different code should have lower similarity
        sim_13 = cosine_similarity(emb1, emb3)
        assert sim_13 < sim_12

    def test_embedding_normalized(self):
        """Test that embeddings are L2 normalized."""
        from src.similarity.embedding import compute_embedding

        code = "def foo(): return 1"
        embedding = compute_embedding(code)

        # L2 norm should be close to 1
        norm = np.linalg.norm(embedding)
        np.testing.assert_almost_equal(norm, 1.0, decimal=5)
