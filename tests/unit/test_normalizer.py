"""
Unit tests for the normalizer module.
"""

import ast
import hashlib
import pytest

from src.normalizer.models import NormalizedProgram


class TestNormalizedProgram:
    """Tests for NormalizedProgram dataclass."""

    def test_creation(self):
        """Test creating a NormalizedProgram."""
        program = NormalizedProgram(
            canonical_code="def foo(): pass",
            ast_hash="abc123",
        )
        assert program.canonical_code == "def foo(): pass"
        assert program.ast_hash == "abc123"
        assert program.embedding == []
        assert program.token_count == 0

    def test_empty_canonical_code_raises(self):
        """Test that empty canonical_code raises ValueError."""
        with pytest.raises(ValueError, match="canonical_code cannot be empty"):
            NormalizedProgram(canonical_code="", ast_hash="abc123")

    def test_empty_ast_hash_raises(self):
        """Test that empty ast_hash raises ValueError."""
        with pytest.raises(ValueError, match="ast_hash cannot be empty"):
            NormalizedProgram(canonical_code="def foo(): pass", ast_hash="")

    def test_has_embedding(self):
        """Test has_embedding property."""
        program = NormalizedProgram(
            canonical_code="def foo(): pass",
            ast_hash="abc123",
        )
        assert not program.has_embedding

        program.embedding = [0.1, 0.2, 0.3]
        assert program.has_embedding

    def test_to_dict_and_from_dict(self):
        """Test serialization and deserialization."""
        original = NormalizedProgram(
            canonical_code="def foo(): pass",
            ast_hash="abc123",
            embedding=[0.1, 0.2],
            token_count=10,
            original_source="original",
            metadata={"key": "value"},
        )
        data = original.to_dict()
        restored = NormalizedProgram.from_dict(data)

        assert restored.canonical_code == original.canonical_code
        assert restored.ast_hash == original.ast_hash
        assert restored.embedding == original.embedding
        assert restored.token_count == original.token_count
        assert restored.original_source == original.original_source
        assert restored.metadata == original.metadata


class TestProgramNormalizer:
    """Tests for ProgramNormalizer class."""

    def test_normalize_simple_program(self, sample_program_simple):
        """Test normalizing a simple program."""
        from src.normalizer.ast_normalizer import ProgramNormalizer

        normalizer = ProgramNormalizer()
        result = normalizer.normalize(sample_program_simple)

        assert isinstance(result, NormalizedProgram)
        assert result.canonical_code  # Should have content
        assert result.ast_hash  # Should have hash
        assert result.original_source == sample_program_simple

    def test_normalize_removes_docstring(self, sample_program_with_docstring):
        """Test that docstrings are removed during normalization."""
        from src.normalizer.ast_normalizer import ProgramNormalizer

        normalizer = ProgramNormalizer()
        result = normalizer.normalize(sample_program_with_docstring)

        # Docstring should be removed
        assert "Greedy heuristic" not in result.canonical_code
        assert "Args:" not in result.canonical_code

    def test_normalize_standardizes_variable_names(self):
        """Test that variable names are standardized."""
        from src.normalizer.ast_normalizer import ProgramNormalizer

        code = """
def heuristic(items, capacity):
    bins = []
    for item in items:
        best = find_best(item, bins)
    return len(bins)
"""
        normalizer = ProgramNormalizer()
        result = normalizer.normalize(code)

        # Original variable names should be replaced
        assert "items" not in result.canonical_code or "var_" in result.canonical_code
        assert "capacity" not in result.canonical_code or "var_" in result.canonical_code

    def test_normalize_syntax_error_raises(self):
        """Test that syntax errors raise SyntaxError."""
        from src.normalizer.ast_normalizer import ProgramNormalizer

        normalizer = ProgramNormalizer()
        with pytest.raises(SyntaxError):
            normalizer.normalize("def foo(:\n    return 1")

    def test_normalize_produces_consistent_hash(self, sample_program_simple):
        """Test that same code produces same hash."""
        from src.normalizer.ast_normalizer import ProgramNormalizer

        normalizer = ProgramNormalizer()
        result1 = normalizer.normalize(sample_program_simple)
        result2 = normalizer.normalize(sample_program_simple)

        assert result1.ast_hash == result2.ast_hash

    def test_normalize_different_code_different_hash(self):
        """Test that different code produces different hash."""
        from src.normalizer.ast_normalizer import ProgramNormalizer

        code1 = "def foo(): return 1"
        code2 = "def foo(): return 2"

        normalizer = ProgramNormalizer()
        result1 = normalizer.normalize(code1)
        result2 = normalizer.normalize(code2)

        assert result1.ast_hash != result2.ast_hash
