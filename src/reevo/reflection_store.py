"""ReEvo ReflectionStore: stores LLM strategy reflections for accepted programs.

Each accepted program (one that passed dedup and received a valid score) can
optionally trigger a short LLM call asking it to describe its algorithmic
strategy in 1-2 sentences. Those reflections are stored here, sorted by score,
and the top-K are injected as code comments into future prompts so the LLM can
build on successful strategies.

Design notes:
- Single-threaded; no locks needed (FunSearch pipeline is sequential).
- Deduplicates by program body hash so the same program never gets two entries.
- Capped at `max_reflections` entries; lowest-scoring entry is evicted on overflow.
"""

from __future__ import annotations

import hashlib


class ReflectionStore:
    """Stores (score, reflection) pairs for top-performing evolved programs."""

    def __init__(self, max_reflections: int = 20) -> None:
        # Each entry: (score, short_hash, reflection_text)
        self._entries: list[tuple[float, str, str]] = []
        self._seen_hashes: set[str] = set()
        self._max_reflections = max_reflections

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add(self, body: str, score: float, reflection: str) -> None:
        """Add a reflection for an accepted program.

        Silently ignores duplicate program bodies.  If capacity is reached,
        the lowest-scoring entry is evicted to make room.
        """
        h = self._hash(body)
        if h in self._seen_hashes:
            return
        self._seen_hashes.add(h)
        self._entries.append((score, h, reflection))
        # Keep list sorted descending by score for fast top-K retrieval
        self._entries.sort(key=lambda x: x[0], reverse=True)
        if len(self._entries) > self._max_reflections:
            _, evicted_hash, _ = self._entries.pop()
            self._seen_hashes.discard(evicted_hash)

    def get_top_reflections(self, k: int = 3) -> list[tuple[float, str]]:
        """Return up to k (score, reflection_text) pairs, best-first."""
        return [(score, text) for score, _, text in self._entries[:k]]

    def __len__(self) -> int:
        return len(self._entries)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _hash(body: str) -> str:
        return hashlib.md5(body.strip().encode()).hexdigest()[:8]
