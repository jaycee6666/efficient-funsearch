"""
Integration module for FunSearch.

This module provides adapters to integrate duplicate detection
with the FunSearch framework.
"""

# Standalone adapter (works without FunSearch library)
from .funsearch_adapter import (
    FunSearchAdapter,
    FunSearchConfig,
    FunSearchResult,
)

# FunSearch library integration (requires RayZhhh/funsearch)
_funsearch_integration = None

try:
    from . import funsearch_integration as _funsearch_integration

    FUNSEARCH_LIBRARY_AVAILABLE = True
except ImportError:
    FUNSEARCH_LIBRARY_AVAILABLE = False

__all__ = [
    # Standalone adapter
    "FunSearchAdapter",
    "FunSearchConfig",
    "FunSearchResult",
]

# Add library integration exports if available
if FUNSEARCH_LIBRARY_AVAILABLE:
    assert _funsearch_integration is not None
    FunSearchIntegration = _funsearch_integration.FunSearchIntegration
    get_integration = _funsearch_integration.get_integration
    patch_funsearch = _funsearch_integration.patch_funsearch
    run_efficient_funsearch = _funsearch_integration.run_efficient_funsearch
    create_patched_database_class = _funsearch_integration.create_patched_database_class
    create_patched_evaluator_class = _funsearch_integration.create_patched_evaluator_class

    __all__.extend(
        [
            "FunSearchIntegration",
            "get_integration",
            "patch_funsearch",
            "run_efficient_funsearch",
            "create_patched_database_class",
            "create_patched_evaluator_class",
        ]
    )
