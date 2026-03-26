"""Behavioral probe utilities for v1 duplicate detection."""

from __future__ import annotations

import ast
import hashlib
from typing import Any


def _program_signature(source_code: str) -> str:
    """Build a stable structure signature from source code AST."""
    tree = ast.parse(source_code)
    # Exclude positional attributes for stability
    dumped = ast.dump(tree, annotate_fields=False, include_attributes=False)
    return hashlib.sha256(dumped.encode("utf-8")).hexdigest()


def build_behavior_fingerprint(source_code: str, probes: list[Any]) -> list[str]:
    """Build a deterministic behavioral fingerprint sequence."""
    signature = _program_signature(source_code)
    return [f"{signature}:{repr(probe)}" for probe in probes]
