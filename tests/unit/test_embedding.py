"""
Unit tests for code embedding.
"""

import hashlib

import numpy as np
import pytest


@pytest.fixture
def mock_embedding_model(monkeypatch):
    """Mock embedding backend to make tests deterministic and offline."""
    import src.similarity.embedding as embedding_module

    class FakeModel:
        def encode(self, data, convert_to_numpy=True):  # noqa: FBT002
            def _vec(text: str):
                seed = int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:8], 16)
                rng = np.random.RandomState(seed)
                return rng.rand(384).astype(np.float32)

            if isinstance(data, str):
                return _vec(data)
            return np.vstack([_vec(x) for x in data]).astype(np.float32)

    monkeypatch.setattr(embedding_module, "_model", FakeModel())


class TestCodeEmbedding:
    """Tests for code embedding functionality."""

    def test_compute_embedding_returns_vector(self, mock_embedding_model):
        """Test that compute_embedding returns a vector."""
        from src.similarity.embedding import compute_embedding

        code = "def foo(): return 1"
        embedding = compute_embedding(code)

        assert isinstance(embedding, np.ndarray)
        assert len(embedding) > 0

    def test_embedding_dimension(self, mock_embedding_model):
        """Test that embedding has expected dimension."""
        from src.similarity.embedding import compute_embedding, get_embedding_dimension

        code = "def foo(): return 1"
        embedding = compute_embedding(code)
        dim = get_embedding_dimension()

        assert len(embedding) == dim

    def test_same_code_same_embedding(self, mock_embedding_model):
        """Test that same code produces same embedding."""
        from src.similarity.embedding import compute_embedding

        code = "def foo(): return 1"
        embedding1 = compute_embedding(code)
        embedding2 = compute_embedding(code)

        np.testing.assert_array_almost_equal(embedding1, embedding2)

    def test_cosine_similarity(self, mock_embedding_model):
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

    def test_embedding_normalized(self, mock_embedding_model):
        """Test that embeddings are L2 normalized."""
        from src.similarity.embedding import compute_embedding

        code = "def foo(): return 1"
        embedding = compute_embedding(code)

        # L2 norm should be close to 1
        norm = np.linalg.norm(embedding)
        np.testing.assert_almost_equal(norm, 1.0, decimal=5)
