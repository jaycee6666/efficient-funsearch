"""
Program archive for storing evaluated programs.

This module provides the main ProgramArchive class for storing and
retrieving programs with efficient duplicate detection.
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Iterator, Optional

from src.archive.models import Program
from src.normalizer.models import NormalizedProgram
from src.archive.hash_store import HashStore
from src.config import ArchiveConfig


class ArchiveStats:
    """Statistics about the archive."""

    def __init__(
        self,
        total_programs: int = 0,
        unique_programs: int = 0,
        duplicate_count: int = 0,
        avg_score: Optional[float] = None,
        best_score: Optional[float] = None,
        memory_usage_mb: float = 0.0,
    ):
        self.total_programs = total_programs
        self.unique_programs = unique_programs
        self.duplicate_count = duplicate_count
        self.avg_score = avg_score
        self.best_score = best_score
        self.memory_usage_mb = memory_usage_mb


class ProgramArchive:
    """
    Archive for storing evaluated programs with duplicate detection.

    Supports efficient O(1) hash-based duplicate detection and
    score-based retrieval of best programs.
    """

    def __init__(self, config: Optional[ArchiveConfig] = None):
        """
        Initialize the archive.

        Args:
            config: Archive configuration (uses defaults if None)
        """
        self.config = config or ArchiveConfig()
        self._programs: dict[str, Program] = {}
        self._ast_index: HashStore = HashStore()
        self._score_heap: list[tuple[float, str]] = []  # (score, program_id)

    def add(
        self,
        source_code: str,
        normalized: NormalizedProgram,
        score: Optional[float] = None,
        generation: int = 0,
        parent_ids: Optional[list[str]] = None,
    ) -> str:
        """
        Add a program to the archive.

        Args:
            source_code: Original source code
            normalized: Normalized program representation
            score: Evaluation score (optional)
            generation: Generation number
            parent_ids: Parent program IDs

        Returns:
            Program ID

        Raises:
            ValueError: If archive is full
        """
        if len(self._programs) >= self.config.max_archive_size:
            raise ValueError("Archive is full")

        program_id = str(uuid.uuid4())

        program = Program(
            id=program_id,
            source_code=source_code,
            normalized_code=normalized.canonical_code,
            ast_hash=normalized.ast_hash,
            score=score,
            generation=generation,
            parent_ids=parent_ids or [],
        )

        # Store program
        self._programs[program_id] = program

        # Add to hash index
        self._ast_index.add(normalized.ast_hash, program_id)

        # Add to score heap
        if score is not None:
            self._score_heap.append((score, program_id))
            # Note: Not maintaining heap property, will sort when needed

        return program_id

    def get(self, program_id: str) -> Optional[Program]:
        """
        Get a program by ID.

        Args:
            program_id: Program ID

        Returns:
            Program if found, None otherwise
        """
        return self._programs.get(program_id)

    def is_duplicate(self, normalized: NormalizedProgram) -> bool:
        """
        Check if a normalized program is a duplicate.

        Args:
            normalized: Normalized program to check

        Returns:
            True if duplicate exists
        """
        return self._ast_index.contains(normalized.ast_hash)

    def find_similar(
        self,
        normalized: NormalizedProgram,
        k: int = 5,
    ) -> list[tuple[Program, float]]:
        """
        Find similar programs (currently exact hash match only).

        Args:
            normalized: Normalized program to find similar to
            k: Maximum results (unused for exact match)

        Returns:
            List of (program, similarity) tuples
        """
        program_id = self._ast_index.get_id(normalized.ast_hash)
        if program_id:
            program = self._programs.get(program_id)
            if program:
                return [(program, 1.0)]
        return []

    def get_best(self, k: int = 10) -> list[Program]:
        """
        Get the best-scoring programs.

        Args:
            k: Number of programs to return

        Returns:
            List of programs sorted by score (descending)
        """
        if not self._score_heap:
            return []

        # Sort by score (descending)
        sorted_programs = sorted(
            self._score_heap,
            key=lambda x: x[0],
            reverse=True,
        )

        result = []
        for score, program_id in sorted_programs[:k]:
            program = self._programs.get(program_id)
            if program:
                result.append(program)

        return result

    def get_by_generation(self, generation: int) -> list[Program]:
        """
        Get all programs from a specific generation.

        Args:
            generation: Generation number

        Returns:
            List of programs from that generation
        """
        return [p for p in self._programs.values() if p.generation == generation]

    def update_score(self, program_id: str, score: float) -> None:
        """
        Update a program's score.

        Args:
            program_id: Program ID
            score: New score
        """
        program = self._programs.get(program_id)
        if program:
            program.score = score
            # Update heap
            self._score_heap.append((score, program_id))

    def remove(self, program_id: str) -> bool:
        """
        Remove a program from the archive.

        Args:
            program_id: Program ID to remove

        Returns:
            True if removed
        """
        program = self._programs.get(program_id)
        if program:
            self._ast_index.remove(program.ast_hash)
            del self._programs[program_id]
            return True
        return False

    def stats(self) -> ArchiveStats:
        """
        Get archive statistics.

        Returns:
            ArchiveStats object
        """
        programs = list(self._programs.values())
        scores = [p.score for p in programs if p.score is not None]

        return ArchiveStats(
            total_programs=len(programs),
            unique_programs=len(programs),  # All are unique after dedup
            duplicate_count=0,  # Tracked elsewhere
            avg_score=sum(scores) / len(scores) if scores else None,
            best_score=max(scores) if scores else None,
            memory_usage_mb=0.0,  # Approximate
        )

    def save(self, path: Optional[str] = None) -> None:
        """
        Save archive to a JSON file.

        Args:
            path: File path (uses config.persistence_path if None)
        """
        save_path = path or self.config.persistence_path
        if not save_path:
            raise ValueError("No save path specified")

        data = {
            "version": "1.0",
            "config": self.config.to_dict(),
            "programs": [p.to_dict() for p in self._programs.values()],
        }

        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    @classmethod
    def load(cls, path: str) -> "ProgramArchive":
        """
        Load archive from a JSON file.

        Args:
            path: File path

        Returns:
            Loaded ProgramArchive
        """
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        config = ArchiveConfig.from_dict(data.get("config", {}))
        archive = cls(config)

        for program_data in data.get("programs", []):
            program = Program.from_dict(program_data)
            archive._programs[program.id] = program
            archive._ast_index.add(program.ast_hash, program.id)
            if program.score is not None:
                archive._score_heap.append((program.score, program.id))

        return archive

    def clear(self) -> None:
        """Clear all programs from the archive."""
        self._programs.clear()
        self._ast_index.clear()
        self._score_heap.clear()

    def __len__(self) -> int:
        """Return number of programs in archive."""
        return len(self._programs)

    def __iter__(self) -> Iterator[Program]:
        """Iterate over all programs."""
        return iter(self._programs.values())

    def __contains__(self, program_id: str) -> bool:
        """Check if program ID exists."""
        return program_id in self._programs
