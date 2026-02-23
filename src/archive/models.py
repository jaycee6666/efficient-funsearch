from __future__ import annotations

"""
Data models for the archive module.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
import uuid


@dataclass
class Program:
    """
    A stored program record in the archive.

    This represents a program that has been evaluated and stored
    for future duplicate detection.
    """

    id: str
    """Unique identifier (UUID)."""

    source_code: str
    """Original Python source code."""

    normalized_code: str
    """Normalized canonical code."""

    ast_hash: str
    """SHA256 hash of the AST structure."""

    score: float | None = None
    """Evaluation score (None if not yet evaluated)."""

    created_at: datetime = field(default_factory=datetime.now)
    """Timestamp when the program was created."""

    generation: int = 0
    """Which generation this program belongs to."""

    parent_ids: list[str] = field(default_factory=list)
    """IDs of parent programs (for evolutionary tracking)."""

    metadata: dict[str, Any] = field(default_factory=dict)
    """Additional metadata."""

    def __post_init__(self):
        """Validate and set defaults."""
        if not self.id:
            self.id = str(uuid.uuid4())
        if not self.source_code:
            raise ValueError("source_code cannot be empty")

    @property
    def is_evaluated(self) -> bool:
        """Check if program has been evaluated."""
        return self.score is not None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "source_code": self.source_code,
            "normalized_code": self.normalized_code,
            "ast_hash": self.ast_hash,
            "score": self.score,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "generation": self.generation,
            "parent_ids": self.parent_ids,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Program":
        """Create from dictionary."""
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        elif created_at is None:
            created_at = datetime.now()

        return cls(
            id=data["id"],
            source_code=data["source_code"],
            normalized_code=data["normalized_code"],
            ast_hash=data["ast_hash"],
            score=data.get("score"),
            created_at=created_at,
            generation=data.get("generation", 0),
            parent_ids=data.get("parent_ids", []),
            metadata=data.get("metadata", {}),
        )
