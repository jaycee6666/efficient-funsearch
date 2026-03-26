"""
Data models for the similarity module.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SimilarityResult:
    """
    Result of comparing two programs for similarity.

    Contains both embedding-based and AST-based similarity scores,
    as well as the final determination of whether they are duplicates.
    """

    program_a_id: str
    """ID of the first program."""

    program_b_id: str
    """ID of the second program."""

    embedding_similarity: float = 0.0
    """
    Cosine similarity of code embeddings (0-1).
    Higher values indicate more similar programs.
    """

    ast_similarity: float = 0.0
    """
    AST structural similarity (0-1).
    Higher values indicate more similar structure.
    """

    is_duplicate: bool = False
    """Whether the programs are considered duplicates."""

    detection_time: float = 0.0
    """Time taken for detection in seconds."""

    detection_method: str = "hybrid"
    """
    Method used for detection.
    One of: "embedding_only", "ast_only", "hybrid"
    """

    metadata: dict[str, Any] = field(default_factory=dict)
    """Additional metadata."""

    def __post_init__(self):
        """Validate similarity scores."""
        if not 0.0 <= self.embedding_similarity <= 1.0:
            raise ValueError(
                f"embedding_similarity must be in [0, 1], got {self.embedding_similarity}"
            )
        if not 0.0 <= self.ast_similarity <= 1.0:
            raise ValueError(f"ast_similarity must be in [0, 1], got {self.ast_similarity}")

    @property
    def combined_score(self) -> float:
        """
        Combined similarity score.

        Returns the maximum of embedding and AST similarity.
        """
        return max(self.embedding_similarity, self.ast_similarity)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "program_a_id": self.program_a_id,
            "program_b_id": self.program_b_id,
            "embedding_similarity": self.embedding_similarity,
            "ast_similarity": self.ast_similarity,
            "is_duplicate": self.is_duplicate,
            "detection_time": self.detection_time,
            "detection_method": self.detection_method,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SimilarityResult":
        """Create from dictionary."""
        return cls(
            program_a_id=data["program_a_id"],
            program_b_id=data["program_b_id"],
            embedding_similarity=data.get("embedding_similarity", 0.0),
            ast_similarity=data.get("ast_similarity", 0.0),
            is_duplicate=data.get("is_duplicate", False),
            detection_time=data.get("detection_time", 0.0),
            detection_method=data.get("detection_method", "hybrid"),
            metadata=data.get("metadata", {}),
        )


@dataclass
class DetectorConfig:
    """
    Configuration for the similarity detector.
    """

    embedding_threshold: float = 0.95
    """Minimum embedding similarity to consider programs as potential duplicates."""

    ast_threshold: float = 0.98
    """Minimum AST similarity to confirm duplicate status."""

    use_embedding: bool = True
    """Whether to use embedding-based pre-filtering."""

    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    """Name of the embedding model to use."""

    max_workers: int = 4
    """Maximum number of parallel workers for batch detection."""

    timeout_seconds: float = 1.0
    """Timeout for single detection in seconds."""

    fallback_to_ast: bool = True
    """Whether to fall back to AST-only mode if embedding fails."""

    behavior_probe_count_min: int = 5
    """Minimum number of probe inputs for behavioral fingerprinting."""

    behavior_probe_count_max: int = 15
    """Maximum number of probe inputs for behavioral fingerprinting."""

    behavior_similarity_threshold: float = 0.95
    """Threshold to classify two behavior fingerprints as duplicates."""

    diversity_weight: float = 0.2
    """Weight of diversity term in performance+diversity ranking."""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "embedding_threshold": self.embedding_threshold,
            "ast_threshold": self.ast_threshold,
            "use_embedding": self.use_embedding,
            "embedding_model": self.embedding_model,
            "max_workers": self.max_workers,
            "timeout_seconds": self.timeout_seconds,
            "fallback_to_ast": self.fallback_to_ast,
            "behavior_probe_count_min": self.behavior_probe_count_min,
            "behavior_probe_count_max": self.behavior_probe_count_max,
            "behavior_similarity_threshold": self.behavior_similarity_threshold,
            "diversity_weight": self.diversity_weight,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DetectorConfig":
        """Create from dictionary."""
        return cls(
            embedding_threshold=data.get("embedding_threshold", 0.95),
            ast_threshold=data.get("ast_threshold", 0.98),
            use_embedding=data.get("use_embedding", True),
            embedding_model=data.get("embedding_model", "sentence-transformers/all-MiniLM-L6-v2"),
            max_workers=data.get("max_workers", 4),
            timeout_seconds=data.get("timeout_seconds", 1.0),
            fallback_to_ast=data.get("fallback_to_ast", True),
            behavior_probe_count_min=data.get("behavior_probe_count_min", 5),
            behavior_probe_count_max=data.get("behavior_probe_count_max", 15),
            behavior_similarity_threshold=data.get("behavior_similarity_threshold", 0.95),
            diversity_weight=data.get("diversity_weight", 0.2),
        )
