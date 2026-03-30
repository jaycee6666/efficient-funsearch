# test Development Guidelines

Auto-generated from current repository state. Last updated: 2026-03-30

## Active Technologies

- Python 3.9+ (project runtime; tested on 3.9/3.10+)
- Core libs: `numpy`, `sentence-transformers`, `torch`
- Dev tooling: `pytest`, `ruff`, `black`, `mypy`
- Domain focus: Efficient FunSearch with behavioral deduplication + diversity-guided selection

## Project Structure

```text
src/
  normalizer/      # Program normalization
  similarity/      # AST/embedding/behavioral similarity and diversity
  archive/         # Program archive and duplicate checks
  integration/     # FunSearch adapter and ablation configs
  metrics/         # Efficiency tracking models/logger

tests/             # Unit and integration tests
notebooks/         # Demo and Colab reproduction notebooks
docs/milestone/    # Milestone submission package
specs/001-efficient-funsearch/  # Spec/plan/tasks and design artifacts
```

## Commands

```bash
# install
pip install -e .
pip install -e .[dev]

# quality gates
ruff check .
pytest -q -rs
```

## Code Style

- Python target: py39
- Ruff line length: 100
- Follow existing project conventions (types, dataclasses, focused modules, clear naming)

## Recent Changes

- Updated milestone materials under `docs/milestone/` (EN/ZH drafts, reproduction, links)
- Removed redundant `specs/001-efficient-funsearch/spec_zh.md`
- Refreshed notebooks:
  - `notebooks/efficient_funsearch_demo.ipynb`
  - `notebooks/efficient_funsearch_colab.ipynb`
  to align with current adapter workflow and reproduction outputs

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
