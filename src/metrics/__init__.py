"""
Metrics module for tracking efficiency improvements.

This module provides tools to track and analyze the efficiency
gains from duplicate detection.
"""

from src.metrics.efficiency_logger import EfficiencyTracker
from src.metrics.models import EfficiencyMetrics

__all__ = ["EfficiencyMetrics", "EfficiencyTracker"]
