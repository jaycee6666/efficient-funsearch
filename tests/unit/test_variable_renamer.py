"""
Unit tests for variable renaming.
"""

import pytest


class TestVariableRenamer:
    """Tests for the VariableRenamer AST transformer."""

    def test_rename_single_variable(self):
        """Test renaming a single variable."""
        from src.normalizer.variable_renamer import VariableRenamer
        import ast

        code = "x = 1"
        tree = ast.parse(code)
        renamer = VariableRenamer()
        new_tree = renamer.visit(tree)

        # Variable should be renamed
        source = ast.unparse(new_tree)
        assert "var_0" in source
        assert "x" not in source

    def test_rename_multiple_variables(self):
        """Test renaming multiple variables in order."""
        from src.normalizer.variable_renamer import VariableRenamer
        import ast

        code = "result = a + b"
        tree = ast.parse(code)
        renamer = VariableRenamer()
        new_tree = renamer.visit(tree)

        source = ast.unparse(new_tree)
        # Variables should be renamed consistently
        assert "var_0" in source
        assert "var_1" in source
        assert "var_2" in source

    def test_rename_function_parameters(self):
        """Test renaming function parameters."""
        from src.normalizer.variable_renamer import VariableRenamer
        import ast

        code = "def foo(items, capacity):\n    return items"
        tree = ast.parse(code)
        renamer = VariableRenamer()
        new_tree = renamer.visit(tree)

        source = ast.unparse(new_tree)
        # Parameters should be renamed
        assert "var_0" in source
        assert "var_1" in source

    def test_consistent_renaming(self):
        """Test that same variable name gets same canonical name."""
        from src.normalizer.variable_renamer import VariableRenamer
        import ast

        code = "x = 1\ny = x + x"
        tree = ast.parse(code)
        renamer = VariableRenamer()
        new_tree = renamer.visit(tree)

        source = ast.unparse(new_tree)
        # All occurrences of 'x' should have same name (var_0)
        assert source.count("var_0") == 3  # x = 1, and two uses of x

    def test_preserve_builtin_names(self):
        """Test that builtin names are not renamed."""
        from src.normalizer.variable_renamer import VariableRenamer
        import ast

        code = "result = len(items)"
        tree = ast.parse(code)
        renamer = VariableRenamer()
        new_tree = renamer.visit(tree)

        source = ast.unparse(new_tree)
        # len is a builtin, should be preserved
        assert "len" in source

    def test_rename_nested_scopes(self):
        """Test renaming in nested function definitions."""
        from src.normalizer.variable_renamer import VariableRenamer
        import ast

        code = """
def outer(x):
    def inner(y):
        return x + y
    return inner(x)
"""
        tree = ast.parse(code)
        renamer = VariableRenamer()
        new_tree = renamer.visit(tree)

        source = ast.unparse(new_tree)
        # Both parameters should be renamed
        assert "var_0" in source  # outer's x
        assert "var_1" in source  # inner's y
