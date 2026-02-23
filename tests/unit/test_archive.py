"""
Unit tests for program archive.
"""

import pytest


class TestProgramArchive:
    """Tests for ProgramArchive class."""

    def test_archive_creation(self):
        """Test creating an empty archive."""
        from src.archive.program_archive import ProgramArchive

        archive = ProgramArchive()
        assert len(archive) == 0

    def test_add_program(self):
        """Test adding a program to archive."""
        from src.archive.program_archive import ProgramArchive
        from src.normalizer.models import NormalizedProgram

        archive = ProgramArchive()
        normalized = NormalizedProgram(
            canonical_code="def foo(): return 1",
            ast_hash="hash123",
        )

        program_id = archive.add(
            source_code="def foo(): return 1",
            normalized=normalized,
            score=0.5,
        )

        assert program_id is not None
        assert len(archive) == 1

    def test_is_duplicate_true(self):
        """Test detecting a duplicate program."""
        from src.archive.program_archive import ProgramArchive
        from src.normalizer.models import NormalizedProgram

        archive = ProgramArchive()

        # Add a program
        normalized = NormalizedProgram(
            canonical_code="def foo(): return 1",
            ast_hash="hash123",
        )
        archive.add("def foo(): return 1", normalized, score=0.5)

        # Check duplicate with same hash
        new_normalized = NormalizedProgram(
            canonical_code="def foo(): return 1",
            ast_hash="hash123",  # Same hash
        )
        assert archive.is_duplicate(new_normalized)

    def test_is_duplicate_false(self):
        """Test that non-duplicate is not detected."""
        from src.archive.program_archive import ProgramArchive
        from src.normalizer.models import NormalizedProgram

        archive = ProgramArchive()

        normalized = NormalizedProgram(
            canonical_code="def foo(): return 1",
            ast_hash="hash123",
        )
        archive.add("def foo(): return 1", normalized, score=0.5)

        new_normalized = NormalizedProgram(
            canonical_code="def bar(): return 2",
            ast_hash="hash456",  # Different hash
        )
        assert not archive.is_duplicate(new_normalized)

    def test_get_program(self):
        """Test retrieving a program by ID."""
        from src.archive.program_archive import ProgramArchive
        from src.normalizer.models import NormalizedProgram

        archive = ProgramArchive()
        normalized = NormalizedProgram(
            canonical_code="def foo(): return 1",
            ast_hash="hash123",
        )
        program_id = archive.add("def foo(): return 1", normalized, score=0.5)

        program = archive.get(program_id)
        assert program is not None
        assert program.source_code == "def foo(): return 1"
        assert program.score == 0.5

    def test_get_best(self):
        """Test getting best programs."""
        from src.archive.program_archive import ProgramArchive
        from src.normalizer.models import NormalizedProgram

        archive = ProgramArchive()

        for i in range(5):
            normalized = NormalizedProgram(
                canonical_code=f"def func{i}(): return {i}",
                ast_hash=f"hash{i}",
            )
            archive.add(f"def func{i}(): return {i}", normalized, score=float(i) / 10)

        best = archive.get_best(k=2)
        assert len(best) == 2
        assert best[0].score >= best[1].score

    def test_stats(self):
        """Test archive statistics."""
        from src.archive.program_archive import ProgramArchive
        from src.normalizer.models import NormalizedProgram

        archive = ProgramArchive()

        for i in range(3):
            normalized = NormalizedProgram(
                canonical_code=f"def func{i}(): return {i}",
                ast_hash=f"hash{i}",
            )
            archive.add(f"def func{i}(): return {i}", normalized, score=float(i))

        stats = archive.stats()
        assert stats.total_programs == 3
        assert stats.best_score == 2.0

    def test_save_and_load(self, tmp_path):
        """Test persistence."""
        from src.archive.program_archive import ProgramArchive
        from src.normalizer.models import NormalizedProgram

        archive = ProgramArchive()

        normalized = NormalizedProgram(
            canonical_code="def foo(): return 1",
            ast_hash="hash123",
        )
        archive.add("def foo(): return 1", normalized, score=0.5)

        # Save
        save_path = tmp_path / "archive.json"
        archive.save(str(save_path))

        # Load
        loaded = ProgramArchive.load(str(save_path))
        assert len(loaded) == 1
        assert loaded.get_best(1)[0].score == 0.5
