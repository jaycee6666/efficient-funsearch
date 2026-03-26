"""
Efficiency tracker for monitoring duplicate detection effectiveness.

This module provides tools to track and analyze the efficiency gains
from the duplicate detection system.
"""

from __future__ import annotations

import time

from src.metrics.models import EfficiencyMetrics


class EfficiencyTracker:
    """
    Tracker for efficiency metrics.

    Records statistics about duplicate detection, resource savings,
    and overall system performance.
    """

    def __init__(self):
        """Initialize the tracker."""
        self.metrics = EfficiencyMetrics()
        self._start_time: float | None = None

    def start_session(self) -> None:
        """Start a new tracking session."""
        self._start_time = time.time()

    def record_generation(self) -> None:
        """Record that a new program was generated."""
        self.metrics.total_programs_generated += 1

    def record_duplicate(self) -> None:
        """Record that a duplicate was detected."""
        self.metrics.duplicates_detected += 1

    def record_filtered(self) -> None:
        """Record that a duplicate was filtered out."""
        self.metrics.duplicates_filtered += 1
        self.metrics.llm_queries_saved += 1  # Estimate

    def record_evaluation(self, time_seconds: float | None = None) -> None:
        """
        Record that a program was evaluated.

        Args:
            time_seconds: Time taken for evaluation (optional)
        """
        self.metrics.programs_evaluated += 1
        if time_seconds:
            self.metrics.evaluation_time_saved += time_seconds

    def record_detection_time(self, time_seconds: float) -> None:
        """
        Record time spent on duplicate detection.

        Args:
            time_seconds: Detection time in seconds
        """
        self.metrics.detection_time_total += time_seconds

    def record_selection(
        self,
        candidate: str,
        score: float,
        diversity_score: float,
        combined_score: float,
    ) -> None:
        """Record selection metadata for later analysis."""
        selections = self.metrics.metadata.setdefault("selection_events", [])
        selections.append(
            {
                "candidate": candidate,
                "score": score,
                "diversity_score": diversity_score,
                "combined_score": combined_score,
            }
        )

    def end_session(self) -> EfficiencyMetrics:
        """
        End the tracking session and return metrics.

        Returns:
            Final EfficiencyMetrics object
        """
        self.metrics.metadata.setdefault("summary", {})
        self.metrics.metadata["summary"].update(
            {
                "sample_efficiency": self.metrics.sample_efficiency,
                "duplicate_detection_rate": self.metrics.duplicate_detection_rate,
                "convergence": self.metrics.metadata.get("convergence", 0.0),
                "final_quality": self.metrics.metadata.get("final_quality", 0.0),
            }
        )
        return self.metrics

    def compare_baseline(self, baseline: EfficiencyTracker) -> dict:
        """
        Compare metrics with a baseline tracker.

        Args:
            baseline: Baseline tracker to compare against

        Returns:
            Dictionary of comparison results
        """
        return {
            "programs_generated_diff": (
                self.metrics.total_programs_generated - baseline.metrics.total_programs_generated
            ),
            "duplicates_detected": self.metrics.duplicates_detected,
            "llm_queries_saved": self.metrics.llm_queries_saved,
            "time_saved": self.metrics.evaluation_time_saved,
            "detection_overhead": self.metrics.detection_time_total,
            "net_time_saved": self.metrics.net_time_saved,
            "duplicate_rate": self.metrics.duplicate_detection_rate,
            "savings_rate": self.metrics.llm_savings_rate,
        }

    def summary(self) -> str:
        """Return a human-readable summary."""
        return self.metrics.summary()

    def reset(self) -> None:
        """Reset all metrics."""
        self.metrics = EfficiencyMetrics()
        self._start_time = None
