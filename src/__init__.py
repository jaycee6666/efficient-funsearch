"""
Efficient FunSearch - Sample-efficient FunSearch with duplicate code detection.

This package provides tools to improve the sample efficiency of FunSearch by
detecting and filtering out functionally duplicate programs before evaluation.
"""

from src.normalizer import ProgramNormalizer, NormalizedProgram
from src.similarity import HybridSimilarityDetector, SimilarityResult
from src.archive import ProgramArchive, Program
from src.metrics import EfficiencyTracker, EfficiencyMetrics

__version__ = "0.1.0"
__all__ = [
    "ProgramNormalizer",
    "NormalizedProgram",
    "HybridSimilarityDetector",
    "SimilarityResult",
    "ProgramArchive",
    "Program",
    "EfficiencyTracker",
    "EfficiencyMetrics",
]
