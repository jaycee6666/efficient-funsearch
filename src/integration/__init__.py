"""
Integration module for FunSearch.

This module provides adapters to integrate duplicate detection
with the FunSearch framework.
"""

# Standalone adapter (works without FunSearch library)
from src.integration.funsearch_adapter import (
    FunSearchAdapter,
    FunSearchConfig,
    FunSearchResult,
)

# FunSearch library integration (requires RayZhhh/funsearch)
try:
    from src.integration.funsearch_integration import (
        FunSearchIntegration,
        get_integration,
        patch_funsearch,
        run_efficient_funsearch,
        create_patched_database_class,
        create_patched_evaluator_class,
    )

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
