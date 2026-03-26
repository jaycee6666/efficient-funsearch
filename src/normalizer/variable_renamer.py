"""
Variable renamer for AST normalization.

This module provides an AST transformer that renames variables
to a canonical form (var_0, var_1, etc.).
"""

import ast

# Python builtins that should not be renamed
BUILTINS: set[str] = {
    "abs",
    "all",
    "any",
    "bin",
    "bool",
    "bytes",
    "callable",
    "chr",
    "classmethod",
    "compile",
    "complex",
    "delattr",
    "dict",
    "dir",
    "divmod",
    "enumerate",
    "eval",
    "exec",
    "filter",
    "float",
    "format",
    "frozenset",
    "getattr",
    "globals",
    "hasattr",
    "hash",
    "help",
    "hex",
    "id",
    "input",
    "int",
    "isinstance",
    "issubclass",
    "iter",
    "len",
    "list",
    "locals",
    "map",
    "max",
    "memoryview",
    "min",
    "next",
    "object",
    "oct",
    "open",
    "ord",
    "pow",
    "print",
    "property",
    "range",
    "repr",
    "reversed",
    "round",
    "set",
    "setattr",
    "slice",
    "sorted",
    "staticmethod",
    "str",
    "sum",
    "super",
    "tuple",
    "type",
    "vars",
    "zip",
    "__import__",
    # Common constants
    "True",
    "False",
    "None",
    "Ellipsis",
    "NotImplemented",
    # Exceptions
    "Exception",
    "BaseException",
    "ValueError",
    "TypeError",
    "KeyError",
    "IndexError",
    "AttributeError",
    "RuntimeError",
    "StopIteration",
}


class VariableRenamer(ast.NodeTransformer):
    """
    AST transformer that renames variables to canonical names.

    Variables are renamed in order of first appearance to var_0, var_1, etc.
    Built-in names are preserved.
    """

    def __init__(self):
        """Initialize the renamer with an empty name mapping."""
        self.name_map: dict[str, str] = {}
        self.counter: int = 0

    def _get_canonical_name(self, name: str) -> str:
        """
        Get or create canonical name for a variable.

        Args:
            name: Original variable name

        Returns:
            Canonical name (var_N)
        """
        if name in BUILTINS:
            return name

        if name not in self.name_map:
            self.name_map[name] = f"var_{self.counter}"
            self.counter += 1

        return self.name_map[name]

    def visit_Name(self, node: ast.Name) -> ast.Name:
        """Rename a Name node."""
        if node.id not in BUILTINS:
            node.id = self._get_canonical_name(node.id)
        return self.generic_visit(node)

    def visit_arg(self, node: ast.arg) -> ast.arg:
        """Rename a function argument."""
        if node.arg not in BUILTINS:
            node.arg = self._get_canonical_name(node.arg)
        return self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        """Visit function definition, preserving function name."""
        # Don't rename the function name itself, only its body
        # Rename arguments
        for arg in node.args.args:
            if arg.arg not in BUILTINS:
                arg.arg = self._get_canonical_name(arg.arg)
        if node.args.vararg:
            node.args.vararg.arg = self._get_canonical_name(node.args.vararg.arg)
        if node.args.kwarg:
            node.args.kwarg.arg = self._get_canonical_name(node.args.kwarg.arg)

        # Visit body
        node.body = [self.visit(stmt) for stmt in node.body]

        return node

    def visit_ClassDef(self, node: ast.ClassDef) -> ast.ClassDef:
        """Visit class definition, preserving class name."""
        # Don't rename the class name itself
        node.body = [self.visit(stmt) for stmt in node.body]
        return node

    def visit_comprehension(self, node: ast.comprehension) -> ast.comprehension:
        """Visit comprehension, renaming target."""
        node.target = self.visit(node.target)
        node.iter = self.visit(node.iter)
        node.ifs = [self.visit(if_clause) for if_clause in node.ifs]
        return node

    def visit_Lambda(self, node: ast.Lambda) -> ast.Lambda:
        """Visit lambda, renaming arguments."""
        for arg in node.args.args:
            if arg.arg not in BUILTINS:
                arg.arg = self._get_canonical_name(arg.arg)
        node.body = self.visit(node.body)
        return node
