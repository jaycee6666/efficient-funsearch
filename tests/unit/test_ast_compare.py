"""
Unit tests for AST comparison.
"""

import pytest


class TestASTCompare:
    """Tests for AST structural comparison."""

    def test_identical_code_ast_similarity(self):
        """Test that identical code has AST similarity 1.0."""
        from src.similarity.ast_compare import compute_ast_similarity

        code = "def foo(): return 1"
        similarity = compute_ast_similarity(code, code)

        assert similarity == 1.0

    def test_different_code_low_similarity(self):
        """Test that structurally different code has low similarity."""
        from src.similarity.ast_compare import compute_ast_similarity

        code1 = "def foo(): return 1"
        code2 = "class Bar:\n    x = 1"
        similarity = compute_ast_similarity(code1, code2)

        assert similarity < 0.5

    def test_renamed_variables_high_similarity(self):
        """Test that renamed variables still have high AST similarity."""
        from src.similarity.ast_compare import compute_ast_similarity

        code1 = "def foo(x, y):\n    return x + y"
        code2 = "def foo(a, b):\n    return a + b"
        similarity = compute_ast_similarity(code1, code2)

        # After normalization, these should be similar
        assert similarity >= 0.9

    def test_compute_ast_hash(self):
        """Test AST hash computation."""
        from src.similarity.ast_compare import compute_ast_hash

        code = "def foo(): return 1"
        hash1 = compute_ast_hash(code)
        hash2 = compute_ast_hash(code)

        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 hex digest length

    def test_different_code_different_hash(self):
        """Test that different code produces different hash."""
        from src.similarity.ast_compare import compute_ast_hash

        hash1 = compute_ast_hash("def foo(): return 1")
        hash2 = compute_ast_hash("def foo(): return 2")

        assert hash1 != hash2

    def test_syntax_error_handling(self):
        """Test handling of syntax errors."""
        from src.similarity.ast_compare import compute_ast_similarity

        code1 = "def foo(): return 1"
        invalid = "def foo(:\n    return 1"

        with pytest.raises(SyntaxError):
            compute_ast_similarity(code1, invalid)
