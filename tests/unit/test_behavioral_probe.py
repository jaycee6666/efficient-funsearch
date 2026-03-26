"""Unit tests for behavioral probe fingerprinting."""

from src.similarity.behavioral_probe import build_behavior_fingerprint


def test_build_behavior_fingerprint_returns_stable_signature():
    code = "def solve(x): return x + 1"
    probes = [1, 2, 3, 4, 5]

    sig1 = build_behavior_fingerprint(code, probes)
    sig2 = build_behavior_fingerprint(code, probes)

    assert sig1 == sig2
