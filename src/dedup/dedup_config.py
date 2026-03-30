"""Dedup module configuration — controls the switches and parameters of the three-level filter funnel."""

from __future__ import annotations

import dataclasses


@dataclasses.dataclass(frozen=True)
class DedupConfig:
    """Configuration parameters for the three-level dedup funnel.

    Attributes:
        enabled: Master switch; if False, dedup is completely skipped
        level0_enabled: Level 0 — code normalization + AST Hash
        level1_enabled: Level 1 — behavioral fingerprint exact match
        level2_enabled: Level 2 — cosine similarity approximate match
        cosine_threshold: Level 2 duplicate threshold (higher = more conservative; 0.98 means nearly identical to count as duplicate)
        probe_timeout_seconds: Timeout in seconds for a single probe execution
        validation_interval: Every N samples, force-pass a "hit" sample for validation (used for false positive rate tracking)
    """
    enabled: bool = True
    level0_enabled: bool = True
    level1_enabled: bool = True
    level2_enabled: bool = False       # Cosine similarity lacks discriminative power with 375-dim fingerprints; disabled for now
    cosine_threshold: float = 0.98
    probe_timeout_seconds: int = 5
    validation_interval: int = 50
