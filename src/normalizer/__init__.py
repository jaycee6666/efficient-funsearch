"""
Normalizer module for code standardization.

This module provides tools to normalize Python code into a canonical form
for similarity comparison.
"""

from src.normalizer.models import NormalizedProgram
from src.normalizer.ast_normalizer import ProgramNormalizer

__all__ = ["NormalizedProgram", "ProgramNormalizer"]
