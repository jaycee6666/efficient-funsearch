"""
AST comparison for structural similarity detection.

This module provides tools to compare Python programs based on their
Abstract Syntax Tree (AST) structure.
"""

import ast
import hashlib
from typing import Any


def compute_ast_hash(code: str) -> str:
    """
    Compute a hash of the AST structure.

    Args:
        code: Python source code string

    Returns:
        SHA256 hex digest of the AST structure

    Raises:
        SyntaxError: If code contains invalid Python syntax
    """
    tree = ast.parse(code)
    ast_str = ast.dump(tree)
    return hashlib.sha256(ast_str.encode("utf-8")).hexdigest()


def compute_ast_similarity(code_a: str, code_b: str) -> float:
    """
    Compute structural similarity between two programs based on AST.

    Args:
        code_a: First Python source code
        code_b: Second Python source code

    Returns:
        Similarity score in [0, 1]

    Raises:
        SyntaxError: If either code contains invalid Python syntax
    """
    tree_a = ast.parse(code_a)
    tree_b = ast.parse(code_b)

    # Compare AST structures
    structure_a = _extract_structure(tree_a)
    structure_b = _extract_structure(tree_b)

    # Compute Jaccard similarity on structural features
    intersection = len(structure_a & structure_b)
    union = len(structure_a | structure_b)

    if union == 0:
        return 1.0 if intersection == 0 else 0.0

    return intersection / union


def _extract_structure(tree: ast.AST) -> set[str]:
    """
    Extract structural features from an AST.

    Args:
        tree: AST to analyze

    Returns:
        Set of structural feature strings
    """
    features = set()

    for node in ast.walk(tree):
        # Node type
        node_type = type(node).__name__

        # Add basic structural features
        if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
            features.add(f"func_def")
            features.add(f"args_{len(node.args.args)}")
            if node.args.vararg:
                features.add("vararg")
            if node.args.kwarg:
                features.add("kwarg")
            if node.decorator_list:
                features.add(f"decorators_{len(node.decorator_list)}")

        elif isinstance(node, ast.ClassDef):
            features.add("class_def")
            features.add(f"bases_{len(node.bases)}")

        elif isinstance(node, ast.If):
            features.add("if_stmt")

        elif isinstance(node, ast.For) or isinstance(node, ast.AsyncFor):
            features.add("for_loop")

        elif isinstance(node, ast.While):
            features.add("while_loop")

        elif isinstance(node, ast.Try):
            features.add("try_except")

        elif isinstance(node, ast.With) or isinstance(node, ast.AsyncWith):
            features.add("with_stmt")

        elif isinstance(node, ast.Return):
            features.add("return")

        elif isinstance(node, ast.Yield) or isinstance(node, ast.YieldFrom):
            features.add("yield")

        elif isinstance(node, ast.Await):
            features.add("await")

        elif isinstance(node, ast.BinOp):
            features.add(f"binop_{type(node.op).__name__}")

        elif isinstance(node, ast.Compare):
            features.add("compare")

        elif isinstance(node, ast.BoolOp):
            features.add(f"boolop_{type(node.op).__name__}")

        elif isinstance(node, ast.Call):
            features.add("call")

        elif isinstance(node, ast.Subscript):
            features.add("subscript")

        elif isinstance(node, ast.Attribute):
            features.add("attribute")

        elif isinstance(node, ast.ListComp) or isinstance(node, ast.SetComp):
            features.add("comprehension")

        elif isinstance(node, ast.DictComp):
            features.add("dict_comprehension")

        elif isinstance(node, ast.Lambda):
            features.add("lambda")

    return features


def compute_tree_edit_distance(tree_a: ast.AST, tree_b: ast.AST) -> int:
    """
    Compute approximate tree edit distance between two ASTs.

    This is a simplified implementation using node counts.
    For a full implementation, consider using zss library.

    Args:
        tree_a: First AST
        tree_b: Second AST

    Returns:
        Approximate edit distance
    """
    # Count nodes by type
    nodes_a = _count_nodes_by_type(tree_a)
    nodes_b = _count_nodes_by_type(tree_b)

    # Compute difference
    all_types = set(nodes_a.keys()) | set(nodes_b.keys())

    distance = 0
    for node_type in all_types:
        count_a = nodes_a.get(node_type, 0)
        count_b = nodes_b.get(node_type, 0)
        distance += abs(count_a - count_b)

    return distance


def _count_nodes_by_type(tree: ast.AST) -> dict[str, int]:
    """
    Count nodes by type in an AST.

    Args:
        tree: AST to analyze

    Returns:
        Dictionary mapping node type names to counts
    """
    counts: dict[str, int] = {}

    for node in ast.walk(tree):
        node_type = type(node).__name__
        counts[node_type] = counts.get(node_type, 0) + 1

    return counts
