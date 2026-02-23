"""
Similarity detection module.

This module provides tools to detect code similarity using a hybrid
approach: embedding-based pre-filtering + AST verification.
"""

from src.similarity.models import SimilarityResult, DetectorConfig
from src.similarity.hybrid import HybridSimilarityDetector

__all__ = ["SimilarityResult", "DetectorConfig", "HybridSimilarityDetector"]
