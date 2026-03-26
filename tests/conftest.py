"""
Pytest configuration and fixtures for efficient_funsearch tests.
"""

import sys
from pathlib import Path

import pytest

# Add project root and src to path for imports
project_root = Path(__file__).parent.parent
src_path = project_root / "src"

for path in (project_root, src_path):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)


@pytest.fixture
def sample_program_simple():
    """Simple program for basic tests."""
    return '''
def priority(item, bins):
    """Calculate priority for bin selection."""
    remaining = [b - item for b in bins]
    return min(range(len(remaining)), key=lambda i: remaining[i])
'''


@pytest.fixture
def sample_program_with_docstring():
    """Program with docstring to test docstring removal."""
    return '''
def heuristic(items, capacity):
    """
    Greedy heuristic for bin packing.

    Args:
        items: List of item sizes
        capacity: Bin capacity

    Returns:
        Number of bins used
    """
    bins = []
    for item in items:
        # Find best bin
        for i, b in enumerate(bins):
            if b + item <= capacity:
                bins[i] += item
                break
        else:
            bins.append(item)
    return len(bins)
'''


@pytest.fixture
def sample_programs_duplicate_pair():
    """Two programs that are functionally identical but syntactically different."""
    program_a = """
def heuristic(items, capacity):
    bins = []
    for item in items:
        best_idx = -1
        best_space = capacity
        for i, used in enumerate(bins):
            space = capacity - used
            if space >= item and space < best_space:
                best_idx = i
                best_space = space
        if best_idx >= 0:
            bins[best_idx] += item
        else:
            bins.append(item)
    return len(bins)
"""
    # Same logic, different variable names
    program_b = """
def heuristic(elements, max_capacity):
    containers = []
    for element in elements:
        best_container = -1
        min_remaining = max_capacity
        for j, filled in enumerate(containers):
            remaining = max_capacity - filled
            if remaining >= element and remaining < min_remaining:
                best_container = j
                min_remaining = remaining
        if best_container >= 0:
            containers[best_container] += element
        else:
            containers.append(element)
    return len(containers)
"""
    return program_a, program_b


@pytest.fixture
def sample_programs_different():
    """Two programs with different logic."""
    program_a = '''
def heuristic(items, capacity):
    """First-fit algorithm."""
    bins = []
    for item in items:
        for i, used in enumerate(bins):
            if used + item <= capacity:
                bins[i] += item
                break
        else:
            bins.append(item)
    return len(bins)
'''
    program_b = '''
def heuristic(items, capacity):
    """Best-fit decreasing algorithm."""
    sorted_items = sorted(items, reverse=True)
    bins = []
    for item in sorted_items:
        best_idx = -1
        best_space = capacity + 1
        for i, used in enumerate(bins):
            space = capacity - used - item
            if space >= 0 and space < best_space:
                best_idx = i
                best_space = space
        if best_idx >= 0:
            bins[best_idx] += item
        else:
            bins.append(item)
    return len(bins)
'''
    return program_a, program_b
