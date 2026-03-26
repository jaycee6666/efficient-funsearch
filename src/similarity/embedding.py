"""
Code embedding for similarity detection.

This module provides tools to compute embeddings for Python code
using sentence-transformers for semantic similarity comparison.
"""


import numpy as np

# Lazy-loaded embedding model
_model = None
_model_name = "sentence-transformers/all-MiniLM-L6-v2"


def _get_model():
    """Lazy load the embedding model."""
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer

            _model = SentenceTransformer(_model_name)
        except ImportError:
            raise ImportError(
                "sentence-transformers is required for embedding. "
                "Install with: pip install sentence-transformers"
            )
    return _model


def get_embedding_dimension() -> int:
    """
    Get the dimension of the embedding vectors.

    Returns:
        Embedding dimension (384 for all-MiniLM-L6-v2)
    """
    return 384


def compute_embedding(code: str) -> np.ndarray:
    """
    Compute embedding for a code snippet.

    Args:
        code: Python source code string

    Returns:
        L2-normalized embedding vector
    """
    model = _get_model()

    # Compute embedding
    embedding = model.encode(code, convert_to_numpy=True)

    # Ensure it's a numpy array and normalized
    embedding = np.array(embedding, dtype=np.float32)

    # L2 normalize
    norm = np.linalg.norm(embedding)
    if norm > 0:
        embedding = embedding / norm

    return embedding


def compute_embedding_batch(codes: list[str]) -> np.ndarray:
    """
    Compute embeddings for multiple code snippets.

    Args:
        codes: List of Python source code strings

    Returns:
        Array of L2-normalized embedding vectors
    """
    model = _get_model()

    # Compute embeddings
    embeddings = model.encode(codes, convert_to_numpy=True)

    # L2 normalize
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    norms = np.where(norms > 0, norms, 1)  # Avoid division by zero
    embeddings = embeddings / norms

    return embeddings.astype(np.float32)


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """
    Compute cosine similarity between two vectors.

    Args:
        a: First vector
        b: Second vector

    Returns:
        Cosine similarity in [-1, 1]
    """
    # Vectors should already be normalized
    dot_product = np.dot(a, b)
    return float(np.clip(dot_product, -1.0, 1.0))


def cosine_similarity_matrix(embeddings: np.ndarray) -> np.ndarray:
    """
    Compute pairwise cosine similarity matrix.

    Args:
        embeddings: Matrix of embeddings (N x D)

    Returns:
        Symmetric similarity matrix (N x N)
    """
    # Embeddings should already be normalized
    return np.dot(embeddings, embeddings.T)
