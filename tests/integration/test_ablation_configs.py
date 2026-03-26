"""Integration tests for v1 ablation config registry."""

from importlib import import_module


def test_v1_ablation_configs_have_four_required_variants():
    get_v1_ablation_configs = import_module(
        "src.integration.ablation_configs"
    ).get_v1_ablation_configs

    names = [c.name for c in get_v1_ablation_configs()]
    assert names == [
        "original",
        "exact_string_match",
        "normalized_hash_only",
        "behavioral_plus_diversity",
    ]
