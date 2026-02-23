"""
Hash store for efficient duplicate detection.

This module provides a simple hash-based storage for quick duplicate checks.
"""

import hashlib
from typing import Dict, Set, Optional


class HashStore:
    """
    Simple hash-based store for O(1) duplicate detection.
    """

    def __init__(self):
        """Initialize an empty hash store."""
        self._hashes: Set[str] = set()
        self._hash_to_id: Dict[str, str] = {}

    def add(self, hash_value: str, program_id: str) -> None:
        """
        Add a hash to the store.

        Args:
            hash_value: Hash string to store
            program_id: Associated program ID
        """
        self._hashes.add(hash_value)
        self._hash_to_id[hash_value] = program_id

    def contains(self, hash_value: str) -> bool:
        """
        Check if a hash exists in the store.

        Args:
            hash_value: Hash string to check

        Returns:
            True if hash exists
        """
        return hash_value in self._hashes

    def get_id(self, hash_value: str) -> Optional[str]:
        """
        Get the program ID associated with a hash.

        Args:
            hash_value: Hash string to look up

        Returns:
            Program ID if found, None otherwise
        """
        return self._hash_to_id.get(hash_value)

    def remove(self, hash_value: str) -> bool:
        """
        Remove a hash from the store.

        Args:
            hash_value: Hash string to remove

        Returns:
            True if hash was removed
        """
        if hash_value in self._hashes:
            self._hashes.remove(hash_value)
            del self._hash_to_id[hash_value]
            return True
        return False

    def clear(self) -> None:
        """Clear all stored hashes."""
        self._hashes.clear()
        self._hash_to_id.clear()

    def __len__(self) -> int:
        """Return number of stored hashes."""
        return len(self._hashes)

    def __contains__(self, hash_value: str) -> bool:
        """Support 'in' operator."""
        return hash_value in self._hashes
