"""
FunSearch library integration for efficient_funsearch.

This module provides utilities to integrate duplicate detection with the
actual FunSearch library (RayZhhh/funsearch).

Usage:
    from efficient_funsearch.integration import patch_funsearch

    # Patch FunSearch to use duplicate detection
    patch_funsearch()

    # Now run FunSearch normally
    from implementation import funsearch
    funsearch.main(specification, inputs, config, ...)
"""

from __future__ import annotations

import hashlib
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from implementation import code_manipulation, programs_database

from src.normalizer import ProgramNormalizer, NormalizedProgram
from src.metrics import EfficiencyTracker


class FunSearchIntegration:
    """
    Integration layer between efficient_funsearch and the FunSearch library.

    This class provides methods to hook into FunSearch's evolution loop
    and add duplicate detection.

    Architecture:
        FunSearch Evolution Loop:
        Sampler → LLM → Evaluator → ProgramsDatabase.register_program()
                                          ↑
                              Inject duplicate detection here
    """

    def __init__(
        self,
        use_normalization: bool = True,
        track_metrics: bool = True,
    ):
        """
        Initialize the integration.

        Args:
            use_normalization: Whether to normalize programs before comparison
            track_metrics: Whether to track efficiency metrics
        """
        self.use_normalization = use_normalization
        self.track_metrics = track_metrics

        self.normalizer = ProgramNormalizer() if use_normalization else None
        self.tracker = EfficiencyTracker() if track_metrics else None

        # Hash set for quick duplicate detection
        self._seen_hashes: set[str] = set()

        # Statistics
        self.total_checked = 0
        self.duplicates_found = 0

    def get_program_hash(self, program: Any) -> str:
        """
        Get a hash for a FunSearch program.

        Args:
            program: A code_manipulation.Function or string

        Returns:
            Hash string
        """
        if hasattr(program, "body"):
            # code_manipulation.Function object
            code = f"def {program.name}({program.args}):\n{program.body}"
        else:
            code = str(program)

        if self.normalizer:
            try:
                normalized = self.normalizer.normalize(code)
                return normalized.ast_hash
            except SyntaxError:
                # Fall back to direct hash
                pass

        return hashlib.sha256(code.encode()).hexdigest()

    def is_duplicate(self, program: Any) -> bool:
        """
        Check if a program is a duplicate.

        Args:
            program: A code_manipulation.Function or string

        Returns:
            True if duplicate, False otherwise
        """
        self.total_checked += 1

        program_hash = self.get_program_hash(program)

        if program_hash in self._seen_hashes:
            self.duplicates_found += 1
            if self.tracker:
                self.tracker.record_generation()
                self.tracker.record_duplicate()
            return True

        self._seen_hashes.add(program_hash)
        if self.tracker:
            self.tracker.record_generation()
            self.tracker.record_evaluation()

        return False

    def check_and_register(self, program: Any) -> bool:
        """
        Check if duplicate and register if not.

        Args:
            program: A code_manipulation.Function or string

        Returns:
            True if new (not duplicate), False if duplicate
        """
        return not self.is_duplicate(program)

    def get_stats(self) -> dict[str, Any]:
        """Get integration statistics."""
        stats = {
            "total_checked": self.total_checked,
            "duplicates_found": self.duplicates_found,
            "unique_programs": self.total_checked - self.duplicates_found,
            "duplicate_rate": (
                self.duplicates_found / self.total_checked if self.total_checked > 0 else 0.0
            ),
        }

        if self.tracker:
            metrics = self.tracker.metrics
            stats["llm_queries_saved"] = metrics.llm_queries_saved
            stats["efficiency_summary"] = self.tracker.summary()

        return stats

    def reset(self) -> None:
        """Reset the integration state."""
        self._seen_hashes.clear()
        self.total_checked = 0
        self.duplicates_found = 0
        if self.tracker:
            self.tracker.reset()


# Global integration instance
_integration: Optional[FunSearchIntegration] = None


def get_integration() -> FunSearchIntegration:
    """Get the global integration instance."""
    global _integration
    if _integration is None:
        _integration = FunSearchIntegration()
    return _integration


def create_patched_database_class():
    """
    Create a patched ProgramsDatabase class with duplicate detection.

    Returns:
        A new class that extends ProgramsDatabase with duplicate detection
    """
    try:
        from implementation import programs_database, config as fs_config
    except ImportError:
        raise ImportError(
            "FunSearch library not installed. "
            "Install with: pip install git+https://github.com/RayZhhh/funsearch.git"
        )

    integration = get_integration()

    class EfficientProgramsDatabase(programs_database.ProgramsDatabase):
        """
        ProgramsDatabase with duplicate detection.

        This class extends FunSearch's ProgramsDatabase to filter out
        duplicate programs before registration.
        """

        def register_program(
            self, program: Any, island_id: Optional[int], scores_per_test: Any, **kwargs
        ) -> None:
            """
            Register a program, skipping duplicates.

            Args:
                program: The program to register
                island_id: Island to register in
                scores_per_test: Evaluation scores
                **kwargs: Additional arguments
            """
            # Check for duplicate
            if integration.is_duplicate(program):
                # Skip registration for duplicates
                return

            # Call original registration
            super().register_program(program, island_id, scores_per_test, **kwargs)

    return EfficientProgramsDatabase


def create_patched_evaluator_class():
    """
    Create a patched Evaluator class with duplicate detection.

    Returns:
        A new class that extends Evaluator with duplicate detection
    """
    try:
        from implementation import evaluator
    except ImportError:
        raise ImportError(
            "FunSearch library not installed. "
            "Install with: pip install git+https://github.com/RayZhhh/funsearch.git"
        )

    integration = get_integration()

    class EfficientEvaluator(evaluator.Evaluator):
        """
        Evaluator with duplicate detection.

        This class extends FunSearch's Evaluator to skip evaluation
        for duplicate programs.
        """

        def analyse(
            self, sample: str, island_id: Optional[int], version_generated: Optional[int], **kwargs
        ) -> None:
            """
            Analyse a sample, skipping duplicates.

            Args:
                sample: The code sample
                island_id: Island ID
                version_generated: Version number
                **kwargs: Additional arguments
            """
            # Early duplicate check before expensive evaluation
            if integration.is_duplicate(sample):
                return

            # Call original analysis
            super().analyse(sample, island_id, version_generated, **kwargs)

    return EfficientEvaluator


def patch_funsearch(
    patch_database: bool = True,
    patch_evaluator: bool = False,
    use_normalization: bool = True,
) -> FunSearchIntegration:
    """
    Patch FunSearch to use duplicate detection.

    This function monkey-patches FunSearch's classes to add duplicate
    detection. Call this before running funsearch.main().

    Args:
        patch_database: Patch ProgramsDatabase (recommended)
        patch_evaluator: Patch Evaluator (alternative, saves evaluation time)
        use_normalization: Use code normalization for better detection

    Returns:
        The integration instance for statistics tracking

    Example:
        >>> from efficient_funsearch.integration import patch_funsearch
        >>> integration = patch_funsearch()
        >>>
        >>> # Now run FunSearch
        >>> from implementation import funsearch, config
        >>> funsearch.main(specification, inputs, config.Config(), ...)
        >>>
        >>> # Check statistics
        >>> stats = integration.get_stats()
        >>> print(f"Duplicates found: {stats['duplicates_found']}")
    """
    global _integration
    _integration = FunSearchIntegration(use_normalization=use_normalization)

    try:
        from implementation import programs_database, evaluator

        if patch_database:
            EfficientDB = create_patched_database_class()
            # Monkey-patch the class
            programs_database.ProgramsDatabase = EfficientDB

        if patch_evaluator:
            EfficientEval = create_patched_evaluator_class()
            evaluator.Evaluator = EfficientEval

        return _integration

    except ImportError as e:
        raise ImportError(
            "FunSearch library not installed. "
            "Install with: pip install git+https://github.com/RayZhhh/funsearch.git"
        ) from e


def run_efficient_funsearch(
    specification: str,
    inputs: list[Any],
    samples_per_prompt: int = 4,
    num_evaluators: int = 1,
    num_samplers: int = 1,
    max_sample_nums: Optional[int] = None,
    **kwargs,
) -> dict[str, Any]:
    """
    Run FunSearch with duplicate detection enabled.

    This is a convenience function that patches FunSearch and runs
    an experiment.

    Args:
        specification: Problem specification code
        inputs: Test inputs for evaluation
        samples_per_prompt: Samples per LLM prompt
        num_evaluators: Number of evaluator processes
        num_samplers: Number of sampler processes
        max_sample_nums: Maximum samples (None for unlimited)
        **kwargs: Additional arguments for funsearch.main()

    Returns:
        Dictionary with results and statistics

    Example:
        >>> specification = '''
        ... def solve(items):
        ...     # Your solution here
        ...     pass
        ... '''
        >>> inputs = [[1, 2, 3], [4, 5, 6]]
        >>> result = run_efficient_funsearch(specification, inputs, max_sample_nums=100)
        >>> print(f"Best score: {result['best_score']}")
        >>> print(f"Duplicates skipped: {result['duplicates_found']}")
    """
    try:
        from implementation import funsearch, config
    except ImportError:
        raise ImportError(
            "FunSearch library not installed. "
            "Install with: pip install git+https://github.com/RayZhhh/funsearch.git"
        )

    # Patch FunSearch
    integration = patch_funsearch()

    # Create config
    fs_config = config.Config(
        samples_per_prompt=samples_per_prompt,
        num_evaluators=num_evaluators,
        num_samplers=num_samplers,
    )

    # Run FunSearch
    funsearch.main(
        specification=specification,
        inputs=inputs,
        config=fs_config,
        max_sample_nums=max_sample_nums,
        **kwargs,
    )

    # Return statistics
    stats = integration.get_stats()
    return stats
