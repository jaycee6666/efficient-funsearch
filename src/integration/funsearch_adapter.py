"""
FunSearch adapter for integrating duplicate detection.

This module provides an adapter that wraps FunSearch's evolution process
to detect and filter duplicate programs before evaluation.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from src.archive import ProgramArchive
from src.metrics import EfficiencyMetrics, EfficiencyTracker
from src.normalizer import ProgramNormalizer
from src.similarity import HybridSimilarityDetector
from src.similarity.behavioral_probe import build_behavior_fingerprint


@dataclass
class FunSearchConfig:
    """
    Configuration for FunSearch adapter.
    """

    # Problem settings
    problem_name: str = "default"
    """Name of the optimization problem."""

    max_generations: int = 100
    """Maximum number of generations to run."""

    population_size: int = 10
    """Number of programs per generation."""

    # Duplicate detection settings
    use_duplicate_detection: bool = True
    """Whether to enable duplicate detection."""

    embedding_threshold: float = 0.95
    """Threshold for embedding-based duplicate detection."""

    ast_threshold: float = 0.98
    """Threshold for AST-based duplicate confirmation."""

    # Evaluation settings
    evaluation_function: Callable[[str], float] | None = None
    """Function to evaluate program quality."""

    # LLM settings (for integration with actual FunSearch)
    llm_function: Callable[[str, list[str]], str] | None = None
    """LLM function to generate new programs."""

    # Logging
    verbose: bool = True
    """Whether to print progress messages."""


@dataclass
class FunSearchResult:
    """
    Result from running FunSearch with duplicate detection.
    """

    best_program: str | None = None
    """Best program found."""

    best_score: float = float("-inf")
    """Best score achieved."""

    total_programs_generated: int = 0
    """Total number of programs generated."""

    unique_programs_evaluated: int = 0
    """Number of unique programs that were evaluated."""

    duplicates_skipped: int = 0
    """Number of duplicate programs that were skipped."""

    generations_run: int = 0
    """Number of generations completed."""

    efficiency_metrics: EfficiencyMetrics | None = None
    """Detailed efficiency metrics."""

    evaluation_time: float = 0.0
    """Total time spent on evaluation."""

    detection_time: float = 0.0
    """Total time spent on duplicate detection."""

    archive: ProgramArchive | None = None
    """The program archive (for inspection)."""


class FunSearchAdapter:
    """
    Adapter to integrate duplicate detection with FunSearch.

    This adapter wraps the FunSearch evolution process, adding duplicate
    detection to improve sample efficiency by avoiding redundant evaluations.

    Usage:
        # With actual FunSearch
        adapter = FunSearchAdapter(config)
        result = adapter.run()

        # Or use as a filter in your own evolution loop
        adapter = FunSearchAdapter(config)
        for program_code in generated_programs:
            if not adapter.is_duplicate(program_code):
                score = evaluate(program_code)
                adapter.record_result(program_code, score)
    """

    def __init__(self, config: FunSearchConfig | None = None):
        """
        Initialize the adapter.

        Args:
            config: Configuration for the adapter
        """
        self.config = config or FunSearchConfig()

        # Initialize components
        self.normalizer = ProgramNormalizer()
        self.detector = HybridSimilarityDetector()
        self.archive = ProgramArchive()
        self.tracker = EfficiencyTracker()

        # State
        self._best_program: str | None = None
        self._best_score: float = float("-inf")
        self._total_detection_time: float = 0.0

    def _behavior_probes(self) -> list[int]:
        """Default probe set used for behavioral dedup checks."""
        return list(range(5, 16))

    def is_duplicate(self, source_code: str) -> bool:
        """
        Check if a program is a duplicate of one already evaluated.

        Args:
            source_code: Python source code to check

        Returns:
            True if the program is a duplicate, False otherwise
        """
        if not self.config.use_duplicate_detection:
            return False

        start_time = time.time()

        # Normalize the program
        try:
            normalized = self.normalizer.normalize(source_code)
        except SyntaxError:
            # Invalid code is not a duplicate
            return False

        # Check against archive
        is_dup = self.archive.is_duplicate(normalized)

        detection_elapsed = time.time() - start_time
        self._total_detection_time += detection_elapsed
        self.tracker.record_detection_time(detection_elapsed)

        return is_dup

    def record_result(
        self,
        source_code: str,
        score: float,
        generation: int = 0,
    ) -> bool:
        """
        Record a program and its evaluation result.

        Args:
            source_code: Python source code
            score: Evaluation score
            generation: Which generation this program belongs to

        Returns:
            True if the program was added (not a duplicate), False if skipped
        """
        self.tracker.record_generation()

        # Normalize
        try:
            normalized = self.normalizer.normalize(source_code)
        except SyntaxError:
            return False

        # Check for duplicate
        if self.config.use_duplicate_detection:
            probes = self._behavior_probes()
            candidate_fp = build_behavior_fingerprint(normalized.canonical_code, probes)

            is_duplicate = False
            for stored_program in self.archive:
                stored_fp = build_behavior_fingerprint(stored_program.normalized_code, probes)
                similarity = self.detector.compute_behavior_similarity(candidate_fp, stored_fp)
                if similarity >= self.detector.config.behavior_similarity_threshold:
                    is_duplicate = True
                    break

            if is_duplicate or self.archive.is_duplicate(normalized):
                self.tracker.record_duplicate()
                self.tracker.record_filtered()
                return False

        # Add to archive
        self.archive.add(source_code, normalized, score, generation)
        self.tracker.record_evaluation()

        # Update best
        if score > self._best_score:
            self._best_score = score
            self._best_program = source_code

        return True

    def generate_and_filter(
        self,
        prompt: str,
        examples: list[str],
    ) -> str | None:
        """
        Generate a new program and filter if duplicate.

        Args:
            prompt: Prompt for the LLM
            examples: Example programs to guide generation

        Returns:
            Generated program if unique, None if duplicate
        """
        if self.config.llm_function is None:
            raise ValueError("LLM function not configured")

        # Generate new program
        new_program = self.config.llm_function(prompt, examples)

        # Filter duplicate
        if self.is_duplicate(new_program):
            return None

        return new_program

    def rank_candidates_for_selection(
        self,
        candidates: list[str],
        perf_scores: dict[str, float],
        diversity_scores: dict[str, float],
        beta: float = 0.2,
    ) -> list[str]:
        """Rank candidates using performance + diversity scoring."""
        ranked = sorted(
            candidates,
            key=lambda c: perf_scores[c] + beta * diversity_scores[c],
            reverse=True,
        )

        for candidate in ranked:
            perf = perf_scores[candidate]
            diversity = diversity_scores[candidate]
            combined = perf + beta * diversity
            self.tracker.record_selection(candidate, perf, diversity, combined)

        return ranked

    def run(
        self,
        initial_programs: list[str] | None = None,
        evaluation_function: Callable[[str], float] | None = None,
    ) -> FunSearchResult:
        """
        Run the FunSearch evolution process with duplicate detection.

        This is a simplified evolution loop. For full FunSearch integration,
        use the adapter methods (is_duplicate, record_result) within
        FunSearch's own evolution loop.

        Args:
            initial_programs: Initial population (optional)
            evaluation_function: Function to evaluate programs

        Returns:
            FunSearchResult with the best program and metrics
        """
        eval_fn = evaluation_function or self.config.evaluation_function

        if eval_fn is None:
            raise ValueError(
                "Evaluation function required. Set config.evaluation_function "
                "or pass evaluation_function parameter."
            )

        start_time = time.time()

        # Initialize with provided programs or empty
        population = initial_programs or []

        # Evolution loop
        for gen in range(self.config.max_generations):
            # Evaluate current population
            for program in population:
                if not self.is_duplicate(program):
                    try:
                        score = eval_fn(program)
                    except Exception:
                        score = float("-inf")

                    self.record_result(program, score, generation=gen)

            # TODO: Integrate with actual FunSearch LLM-based generation
            # For now, this is a placeholder for the evolution logic

            if self.config.verbose and gen % 10 == 0:
                stats = self.get_stats()
                print(
                    f"Generation {gen}: "
                    f"{stats['total_programs']} programs, "
                    f"{stats['duplicates_skipped']} duplicates skipped"
                )

        # Build result
        metrics = self.tracker.metrics

        result = FunSearchResult(
            best_program=self._best_program,
            best_score=self._best_score,
            total_programs_generated=metrics.total_programs_generated,
            unique_programs_evaluated=metrics.programs_evaluated,
            duplicates_skipped=metrics.duplicates_detected,
            generations_run=self.config.max_generations,
            efficiency_metrics=metrics,
            evaluation_time=time.time() - start_time - self._total_detection_time,
            detection_time=self._total_detection_time,
            archive=self.archive,
        )

        return result

    def get_stats(self) -> dict[str, Any]:
        """
        Get current statistics.

        Returns:
            Dictionary with current statistics
        """
        archive_stats = self.archive.stats()
        metrics = self.tracker.metrics

        return {
            "best_score": self._best_score,
            "total_programs": archive_stats.total_programs,
            "duplicates_skipped": metrics.duplicates_detected,
            "unique_programs": metrics.programs_evaluated,
            "duplicate_rate": metrics.duplicate_detection_rate,
            "estimated_llm_savings": metrics.llm_queries_saved,
        }

    def reset(self) -> None:
        """Reset the adapter state for a new run."""
        self.archive = ProgramArchive()
        self.tracker = EfficiencyTracker()
        self._best_program = None
        self._best_score = float("-inf")
        self._total_detection_time = 0.0
