"""
Data models for the normalizer module.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class NormalizedProgram:
    """
    Normalized representation of a Python program.

    This is the canonical form used for similarity comparison.
    All variable names are standardized, and docstrings/comments are removed.
    """

    canonical_code: str
    """Normalized code string with standardized variable names."""

    ast_hash: str
    """SHA256 hash of the AST structure."""

    embedding: list[float] = field(default_factory=list)
    """Code embedding vector (computed lazily)."""

    token_count: int = 0
    """Number of tokens in the canonical code."""

    original_source: str = ""
    """Original source code for debugging purposes."""

    metadata: dict[str, Any] = field(default_factory=dict)
    """Additional metadata."""

    def __post_init__(self):
        """Validate and set defaults."""
        if not self.canonical_code:
            raise ValueError("canonical_code cannot be empty")
        if not self.ast_hash:
            raise ValueError("ast_hash cannot be empty")

    @property
    def has_embedding(self) -> bool:
        """Check if embedding has been computed."""
        return len(self.embedding) > 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "canonical_code": self.canonical_code,
            "ast_hash": self.ast_hash,
            "embedding": self.embedding,
            "token_count": self.token_count,
            "original_source": self.original_source,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "NormalizedProgram":
        """Create from dictionary."""
        return cls(
            canonical_code=data["canonical_code"],
            ast_hash=data["ast_hash"],
            embedding=data.get("embedding", []),
            token_count=data.get("token_count", 0),
            original_source=data.get("original_source", ""),
            metadata=data.get("metadata", {}),
        )
