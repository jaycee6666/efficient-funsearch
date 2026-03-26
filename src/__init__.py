"""
Efficient FunSearch - Sample-efficient FunSearch with duplicate code detection.

This package provides tools to improve the sample efficiency of FunSearch by
detecting and filtering out functionally duplicate programs before evaluation.
"""

from src.archive import Program, ProgramArchive
from src.config import ArchiveConfig
from src.integration import FunSearchAdapter, FunSearchConfig, FunSearchResult
from src.metrics import EfficiencyMetrics, EfficiencyTracker
from src.normalizer import NormalizedProgram, ProgramNormalizer
from src.similarity import DetectorConfig, HybridSimilarityDetector, SimilarityResult

__version__ = "0.1.0"
__all__ = [
    "ProgramNormalizer",
    "NormalizedProgram",
    "HybridSimilarityDetector",
    "SimilarityResult",
    "DetectorConfig",
    "ProgramArchive",
    "Program",
    "EfficiencyTracker",
    "EfficiencyMetrics",
    "ArchiveConfig",
    "FunSearchAdapter",
    "FunSearchConfig",
    "FunSearchResult",
]
