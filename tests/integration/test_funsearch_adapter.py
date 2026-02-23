"""
Integration tests for FunSearch adapter.
"""

import pytest


class TestFunSearchAdapter:
    """Tests for FunSearchAdapter integration."""

    def test_adapter_creation(self):
        """Test creating an adapter with default config."""
        from src.integration.funsearch_adapter import FunSearchAdapter

        adapter = FunSearchAdapter()
        assert adapter is not None
        assert adapter.config.use_duplicate_detection is True

    def test_adapter_with_custom_config(self):
        """Test creating an adapter with custom config."""
        from src.integration.funsearch_adapter import FunSearchAdapter, FunSearchConfig

        config = FunSearchConfig(
            problem_name="test_problem",
            max_generations=10,
            use_duplicate_detection=True,
        )
        adapter = FunSearchAdapter(config)

        assert adapter.config.problem_name == "test_problem"
        assert adapter.config.max_generations == 10

    def test_is_duplicate_detection(self):
        """Test duplicate detection in adapter."""
        from src.integration.funsearch_adapter import FunSearchAdapter

        adapter = FunSearchAdapter()

        code = "def solve(x): return x * 2"

        # First time should not be duplicate
        is_dup = adapter.is_duplicate(code)
        assert is_dup is False

        # Record it
        adapter.record_result(code, score=1.0)

        # Same code should now be duplicate
        is_dup = adapter.is_duplicate(code)
        assert is_dup is True

    def test_record_result(self):
        """Test recording program results."""
        from src.integration.funsearch_adapter import FunSearchAdapter

        adapter = FunSearchAdapter()

        code = "def solve(x): return x + 1"

        # Record unique program
        result = adapter.record_result(code, score=0.5)
        assert result is True

        # Try to record duplicate
        result = adapter.record_result(code, score=0.6)
        assert result is False

    def test_duplicate_with_renamed_variables(self):
        """Test that renamed variables are detected as duplicates."""
        from src.integration.funsearch_adapter import FunSearchAdapter

        adapter = FunSearchAdapter()

        code_a = """
def solve(items, capacity):
    result = 0
    for item in items:
        if item <= capacity:
            result += item
    return result
"""

        code_b = """
def solve(xs, cap):
    total = 0
    for x in xs:
        if x <= cap:
            total += x
    return total
"""

        # Record first program
        adapter.record_result(code_a, score=0.8)

        # Second program (semantically same, different names) should be duplicate
        is_dup = adapter.is_duplicate(code_b)
        assert is_dup is True

    def test_different_programs_not_duplicates(self):
        """Test that different programs are not duplicates."""
        from src.integration.funsearch_adapter import FunSearchAdapter

        adapter = FunSearchAdapter()

        code_a = "def solve(x): return x * 2"
        code_b = "def solve(x): return x ** 3"

        # Record first program
        adapter.record_result(code_a, score=0.5)

        # Different program should not be duplicate
        is_dup = adapter.is_duplicate(code_b)
        assert is_dup is False

    def test_get_stats(self):
        """Test getting adapter statistics."""
        from src.integration.funsearch_adapter import FunSearchAdapter

        adapter = FunSearchAdapter()

        # Record some programs
        adapter.record_result("def a(): return 1", score=0.5)
        adapter.record_result("def b(): return 2", score=0.6)
        adapter.record_result("def a(): return 1", score=0.7)  # Duplicate

        stats = adapter.get_stats()

        assert stats["total_programs"] == 2
        assert stats["duplicates_skipped"] == 1
        assert stats["best_score"] == 0.6

    def test_reset(self):
        """Test resetting adapter state."""
        from src.integration.funsearch_adapter import FunSearchAdapter

        adapter = FunSearchAdapter()

        # Record some programs
        adapter.record_result("def a(): return 1", score=0.5)

        # Reset
        adapter.reset()

        stats = adapter.get_stats()
        assert stats["total_programs"] == 0
        assert stats["best_score"] == float("-inf")

    def test_disable_duplicate_detection(self):
        """Test that duplicate detection can be disabled."""
        from src.integration.funsearch_adapter import FunSearchAdapter, FunSearchConfig

        config = FunSearchConfig(use_duplicate_detection=False)
        adapter = FunSearchAdapter(config)

        code = "def solve(x): return x * 2"

        # Record twice
        adapter.record_result(code, score=0.5)
        is_dup = adapter.is_duplicate(code)

        # Should not be duplicate when detection is disabled
        assert is_dup is False

    def test_run_with_evaluation_function(self):
        """Test running adapter with evaluation function."""
        from src.integration.funsearch_adapter import FunSearchAdapter, FunSearchConfig

        def eval_fn(code: str) -> float:
            # Simple evaluation: longer code = higher score
            return float(len(code))

        config = FunSearchConfig(
            max_generations=1,
            verbose=False,
        )
        adapter = FunSearchAdapter(config)

        # Run with initial programs
        initial_programs = [
            "def a(): return 1",
            "def b(): return 2",
            "def a(): return 1",  # Duplicate
        ]

        result = adapter.run(
            initial_programs=initial_programs,
            evaluation_function=eval_fn,
        )

        assert result.generations_run == 1
        assert result.unique_programs_evaluated == 2
        assert result.duplicates_skipped == 0  # run() skips duplicates before tracking
        assert result.best_score > 0

    def test_syntax_error_handling(self):
        """Test that syntax errors are handled gracefully."""
        from src.integration.funsearch_adapter import FunSearchAdapter

        adapter = FunSearchAdapter()

        # Invalid code
        invalid_code = "def broken(: return 1"

        # Should not crash, just return False for duplicate check
        is_dup = adapter.is_duplicate(invalid_code)
        assert is_dup is False

        # Should not be recorded
        result = adapter.record_result(invalid_code, score=1.0)
        assert result is False


class TestFunSearchResult:
    """Tests for FunSearchResult dataclass."""

    def test_result_creation(self):
        """Test creating a result object."""
        from src.integration.funsearch_adapter import FunSearchResult

        result = FunSearchResult(
            best_program="def solve(): return 42",
            best_score=42.0,
            total_programs_generated=100,
            unique_programs_evaluated=70,
            duplicates_skipped=30,
        )

        assert result.best_score == 42.0
        assert result.total_programs_generated == 100
        assert result.unique_programs_evaluated == 70
        assert result.duplicates_skipped == 30
