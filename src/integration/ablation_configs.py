"""Ablation configuration registry for proposal v1."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AblationConfig:
    """Single ablation configuration descriptor."""

    name: str
    options: dict[str, Any] = field(default_factory=dict)


def get_v1_ablation_configs() -> list[AblationConfig]:
    """Return the four required proposal-v1 baseline/ablation variants."""
    return [
        AblationConfig(name="original"),
        AblationConfig(name="exact_string_match"),
        AblationConfig(name="normalized_hash_only"),
        AblationConfig(name="behavioral_plus_diversity"),
    ]
