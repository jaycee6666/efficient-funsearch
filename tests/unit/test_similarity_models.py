"""Unit tests for similarity/config data models."""

from src.config import ArchiveConfig
from src.similarity.models import DetectorConfig


def test_detector_config_supports_behavioral_and_diversity_fields():
    cfg = DetectorConfig()

    assert cfg.behavior_probe_count_min == 5
    assert cfg.behavior_probe_count_max == 15
    assert cfg.behavior_similarity_threshold == 0.95
    assert 0.0 <= cfg.diversity_weight <= 1.0


def test_archive_config_aligned_with_behavior_threshold_defaults():
    cfg = ArchiveConfig()

    assert cfg.behavior_similarity_threshold == 0.95
    assert cfg.behavior_probe_count_min == 5
    assert cfg.behavior_probe_count_max == 15
