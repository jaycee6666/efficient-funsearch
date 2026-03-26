"""
Similarity detection module.

This module provides tools to detect code similarity using a hybrid
approach: embedding-based pre-filtering + AST verification.
"""

from .behavioral_probe import build_behavior_fingerprint
from .hybrid import HybridSimilarityDetector
from .models import DetectorConfig, SimilarityResult

__all__ = [
    "SimilarityResult",
    "DetectorConfig",
    "HybridSimilarityDetector",
    "build_behavior_fingerprint",
]
