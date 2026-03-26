"""
AST normalizer for Python code.

This module provides tools to normalize Python code into a canonical form
by removing docstrings, comments, and standardizing variable names.
"""

from __future__ import annotations

import ast
import hashlib

from src.normalizer.models import NormalizedProgram
from src.normalizer.variable_renamer import VariableRenamer


class ProgramNormalizer:
    """
    Normalizer for Python programs.

    Converts Python source code into a canonical form for similarity comparison.
    """

    def __init__(self, preserve_function_names: bool = True):
        """
        Initialize the normalizer.

        Args:
            preserve_function_names: Whether to keep original function names
        """
        self.preserve_function_names = preserve_function_names

    def normalize(self, source_code: str) -> NormalizedProgram:
        """
        Normalize a Python program.

        Args:
            source_code: Python source code string

        Returns:
            NormalizedProgram with canonical code and AST hash

        Raises:
            SyntaxError: If source_code contains invalid Python syntax
        """
        # Parse the source code
        tree = ast.parse(source_code)

        # Remove docstrings
        tree = self._remove_docstrings(tree)

        # Rename variables
        renamer = VariableRenamer()
        tree = renamer.visit(tree)

        # Fix any issues from the transformation
        ast.fix_missing_locations(tree)

        # Convert back to source
        canonical_code = ast.unparse(tree)

        # Compute AST hash
        ast_hash = self._compute_ast_hash(tree)

        # Count tokens (approximate)
        token_count = len(canonical_code.split())

        return NormalizedProgram(
            canonical_code=canonical_code,
            ast_hash=ast_hash,
            token_count=token_count,
            original_source=source_code,
        )

    def normalize_batch(self, source_codes: list[str]) -> list[NormalizedProgram | None]:
        """
        Normalize multiple programs.

        Args:
            source_codes: List of Python source code strings

        Returns:
            List of NormalizedProgram objects (None for syntax errors)
        """
        results = []
        for code in source_codes:
            try:
                results.append(self.normalize(code))
            except SyntaxError:
                results.append(None)
        return results

    def _remove_docstrings(self, tree: ast.AST) -> ast.AST:
        """
        Remove docstrings from the AST.

        Args:
            tree: AST to process

        Returns:
            Modified AST without docstrings
        """
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)):
                # Check if first statement is a docstring
                if node.body and isinstance(node.body[0], ast.Expr):
                    if isinstance(node.body[0].value, ast.Constant):
                        if isinstance(node.body[0].value.value, str):
                            # Remove the docstring
                            node.body = node.body[1:]
        return tree

    def _compute_ast_hash(self, tree: ast.AST) -> str:
        """
        Compute a hash of the AST structure.

        Args:
            tree: AST to hash

        Returns:
            SHA256 hash string
        """
        # Convert AST to string representation
        ast_str = ast.dump(tree)

        # Compute hash
        hash_obj = hashlib.sha256(ast_str.encode("utf-8"))
        return hash_obj.hexdigest()
