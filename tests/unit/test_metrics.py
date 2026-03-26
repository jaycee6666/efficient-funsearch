"""Unit tests for v1 efficiency metrics behavior."""

from src.metrics.models import EfficiencyMetrics


def test_sample_efficiency_eta_computed_from_unique_over_total():
    m = EfficiencyMetrics(total_programs_generated=10, programs_evaluated=4)
    assert m.sample_efficiency == 0.4
