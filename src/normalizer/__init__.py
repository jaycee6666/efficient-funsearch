"""
Normalizer module for code standardization.

This module provides tools to normalize Python code into a canonical form
for similarity comparison.
"""

from src.normalizer.ast_normalizer import ProgramNormalizer
from src.normalizer.models import NormalizedProgram

__all__ = ["NormalizedProgram", "ProgramNormalizer"]
