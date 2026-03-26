"""Integration checks for v1 documentation alignment."""

from pathlib import Path


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_documentation_mentions_behavioral_and_diversity_mainline():
    root = Path(__file__).resolve().parents[2]
    detector_doc = _read(root / "specs/001-efficient-funsearch/contracts/detector.md")
    data_model_doc = _read(root / "specs/001-efficient-funsearch/data-model.md")
    quickstart_doc = _read(root / "specs/001-efficient-funsearch/quickstart.md")

    merged = "\n".join([detector_doc, data_model_doc, quickstart_doc]).lower()
    assert "behavioral" in merged
    assert "diversity" in merged
    assert "embedding+ast" not in merged
