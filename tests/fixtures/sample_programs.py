"""
Sample programs for testing.

This module contains sample Python programs used as test fixtures
throughout the test suite.
"""

# Simple programs
SIMPLE_PROGRAM = """
def priority(item, bins):
    remaining = [b - item for b in bins]
    return min(range(len(remaining)), key=lambda i: remaining[i])
"""

SIMPLE_PROGRAM_WITH_DOCSTRING = '''
def heuristic(items, capacity):
    """Greedy heuristic for bin packing.

    Args:
        items: List of item sizes
        capacity: Bin capacity

    Returns:
        Number of bins used
    """
    bins = []
    for item in items:
        for i, b in enumerate(bins):
            if b + item <= capacity:
                bins[i] += item
                break
        else:
            bins.append(item)
    return len(bins)
'''

# Duplicate programs (functionally identical, different variable names)
DUPLICATE_PROGRAM_A = """
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

DUPLICATE_PROGRAM_B = """
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

# Different programs (different logic)
DIFFERENT_PROGRAM_A = '''
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

DIFFERENT_PROGRAM_B = '''
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

# Behavioral probe fixtures (v1)
BEHAVIOR_PROBES_SMALL = [1, 2, 3, 4, 5]

BEHAVIOR_PROBES_EDGE = [0, 1, -1, 10**3, -(10**3)]

BEHAVIOR_PROBES_MIXED = [
    ([], 10),
    ([1], 10),
    ([9, 1, 2], 10),
    ([5, 5, 5], 10),
    ([2, 3, 7, 8], 10),
]

# Invalid programs (for edge case testing)
INVALID_PROGRAM_SYNTAX = "def foo(:\n    return 1"

INVALID_PROGRAM_EMPTY = ""

INVALID_PROGRAM_NON_FUNCTION = "x = 1 + 2"


def get_sample_programs():
    """Get all sample programs."""
    return {
        "simple": SIMPLE_PROGRAM,
        "with_docstring": SIMPLE_PROGRAM_WITH_DOCSTRING,
        "duplicate_a": DUPLICATE_PROGRAM_A,
        "duplicate_b": DUPLICATE_PROGRAM_B,
        "different_a": DIFFERENT_PROGRAM_A,
        "different_b": DIFFERENT_PROGRAM_B,
    }


def get_duplicate_pair():
    """Get a pair of functionally identical programs."""
    return DUPLICATE_PROGRAM_A, DUPLICATE_PROGRAM_B


def get_different_pair():
    """Get a pair of functionally different programs."""
    return DIFFERENT_PROGRAM_A, DIFFERENT_PROGRAM_B


def get_behavior_probe_sets():
    """Get behavioral probe sets for v1 fingerprint tests."""
    return {
        "small": BEHAVIOR_PROBES_SMALL,
        "edge": BEHAVIOR_PROBES_EDGE,
        "mixed": BEHAVIOR_PROBES_MIXED,
    }
