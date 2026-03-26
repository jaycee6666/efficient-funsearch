"""
Configuration for efficient_funsearch.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ArchiveConfig:
    """
    Configuration for the program archive.
    """

    max_archive_size: int = 10000
    """Maximum number of programs to store."""

    embedding_threshold: float = 0.95
    """Threshold for embedding-based duplicate detection."""

    ast_threshold: float = 0.98
    """Threshold for AST-based duplicate confirmation."""

    use_embedding_index: bool = True
    """Whether to build an embedding index for similarity search."""

    cache_embeddings: bool = True
    """Whether to cache computed embeddings."""

    persistence_path: str | None = None
    """Path for persistent storage (None for in-memory only)."""

    behavior_probe_count_min: int = 5
    """Minimum number of probe inputs used for behavioral signatures."""

    behavior_probe_count_max: int = 15
    """Maximum number of probe inputs used for behavioral signatures."""

    behavior_similarity_threshold: float = 0.95
    """Threshold for behavioral duplicate detection."""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "max_archive_size": self.max_archive_size,
            "embedding_threshold": self.embedding_threshold,
            "ast_threshold": self.ast_threshold,
            "use_embedding_index": self.use_embedding_index,
            "cache_embeddings": self.cache_embeddings,
            "persistence_path": self.persistence_path,
            "behavior_probe_count_min": self.behavior_probe_count_min,
            "behavior_probe_count_max": self.behavior_probe_count_max,
            "behavior_similarity_threshold": self.behavior_similarity_threshold,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ArchiveConfig:
        """Create from dictionary."""
        return cls(
            max_archive_size=data.get("max_archive_size", 10000),
            embedding_threshold=data.get("embedding_threshold", 0.95),
            ast_threshold=data.get("ast_threshold", 0.98),
            use_embedding_index=data.get("use_embedding_index", True),
            cache_embeddings=data.get("cache_embeddings", True),
            persistence_path=data.get("persistence_path"),
            behavior_probe_count_min=data.get("behavior_probe_count_min", 5),
            behavior_probe_count_max=data.get("behavior_probe_count_max", 15),
            behavior_similarity_threshold=data.get("behavior_similarity_threshold", 0.95),
        )
