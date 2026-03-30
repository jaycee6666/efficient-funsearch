"""DedupFilter core class — three-level filter funnel to detect functionally duplicate programs.

Level 0: Code normalization + AST Hash (<1ms, catches variable name/comment differences)
Level 1: Behavioral fingerprint exact match (<1ms, catches functional equivalence)
Level 2: Cosine similarity approximate match (<5ms, catches near-equivalence)
"""

from __future__ import annotations

import dataclasses
import hashlib
import time

import numpy as np

from src.dedup.dedup_config import DedupConfig
from src.dedup.probing import compute_fingerprint
from src.normalizer.ast_normalizer import ProgramNormalizer


@dataclasses.dataclass
class DedupResult:
    """Result of a single dedup check."""
    is_duplicate: bool
    level_caught: int | None       # Which level caught it: 0, 1, 2, or None (not flagged as duplicate)
    time_level0: float             # Level 0 elapsed time (seconds)
    time_level1: float             # Level 1 elapsed time (seconds)
    time_level2: float             # Level 2 elapsed time (seconds)
    fingerprint: tuple | None      # Behavioral fingerprint (used for Level 2 storage)
    is_validation_pass: bool       # Whether this is a validation sample (force-passed even if caught)


class DedupFilter:
    """Three-level dedup filter.

    Quickly detects functionally duplicate programs before Sandbox evaluation, saving expensive evaluation time.
    """

    def __init__(
        self,
        config: DedupConfig,
        template_str: str,
        function_to_evolve: str,
    ):
        """
        Args:
            config: Dedup configuration
            template_str: Program template string (used to compose the full program for probe execution)
            function_to_evolve: Name of the function being evolved (e.g. 'priority')
        """
        self._config = config
        self._template_str = template_str
        self._function_to_evolve = function_to_evolve
        self._normalizer = ProgramNormalizer()

        # Level 0: AST Hash set
        self._code_hash_set: set[str] = set()

        # Level 1: Behavioral fingerprint Hash set (exact match, zero false positives)
        self._fingerprint_hash_set: set[str] = set()

        # Level 2: Fingerprint vector matrix (for cosine similarity)
        self._fingerprint_vectors: list[np.ndarray] = []

        # Statistics counter
        self._total_checks = 0

    def check(self, program_str: str, function_body: str) -> DedupResult:
        """Perform three-level dedup check on a candidate program.

        Args:
            program_str: Complete executable program string
            function_body: Function body of the evolved function (used for Level 0 normalization)

        Returns:
            DedupResult recording the check result and per-level elapsed time
        """
        if not self._config.enabled:
            return DedupResult(
                is_duplicate=False, level_caught=None,
                time_level0=0, time_level1=0, time_level2=0,
                fingerprint=None, is_validation_pass=False,
            )

        self._total_checks += 1

        # Determine if this is a validation sample (force-pass every N checks for false positive rate tracking)
        is_validation = (
            self._config.validation_interval > 0
            and self._total_checks % self._config.validation_interval == 0
        )

        time_l0 = time_l1 = time_l2 = 0.0
        fingerprint = None
        caught_l0 = caught_l1 = caught_l2 = False

        # ===== Level 0: Code normalization + AST Hash =====
        if self._config.level0_enabled:
            t0 = time.perf_counter()
            caught_l0 = self._check_level0(function_body)
            time_l0 = time.perf_counter() - t0
            if caught_l0 and not is_validation:
                return DedupResult(
                    is_duplicate=True, level_caught=0,
                    time_level0=time_l0, time_level1=0, time_level2=0,
                    fingerprint=None, is_validation_pass=False,
                )

        # ===== Level 1: Behavioral fingerprint exact match =====
        if self._config.level1_enabled:
            t1 = time.perf_counter()
            fingerprint = compute_fingerprint(
                program_str, self._function_to_evolve,
                timeout=self._config.probe_timeout_seconds,
            )
            if fingerprint is not None:
                caught_l1 = self._check_level1(fingerprint)
                time_l1 = time.perf_counter() - t1
                if caught_l1 and not is_validation:
                    return DedupResult(
                        is_duplicate=True, level_caught=1,
                        time_level0=time_l0, time_level1=time_l1, time_level2=0,
                        fingerprint=fingerprint, is_validation_pass=False,
                    )
            else:
                time_l1 = time.perf_counter() - t1

        # ===== Level 2: Cosine similarity approximate match =====
        if self._config.level2_enabled and fingerprint is not None:
            t2 = time.perf_counter()
            caught_l2 = self._check_level2(fingerprint)
            time_l2 = time.perf_counter() - t2
            if caught_l2 and not is_validation:
                return DedupResult(
                    is_duplicate=True, level_caught=2,
                    time_level0=time_l0, time_level1=time_l1, time_level2=time_l2,
                    fingerprint=fingerprint, is_validation_pass=False,
                )

        # ===== Determine if caught by any level =====
        was_caught = caught_l0 or caught_l1 or caught_l2

        # Only register truly new programs (avoid validation samples re-registering and causing self-matches)
        if not was_caught:
            self._register(function_body, fingerprint)

        # Derive level_caught (for validation samples, records "which level would have caught it")
        level_caught = None
        if was_caught:
            level_caught = 0 if caught_l0 else (1 if caught_l1 else 2)

        return DedupResult(
            is_duplicate=was_caught,
            level_caught=level_caught,
            time_level0=time_l0, time_level1=time_l1, time_level2=time_l2,
            fingerprint=fingerprint,
            is_validation_pass=is_validation,
        )

    # ------------------------------------------------------------------
    # Level 0: Code normalization + AST Hash
    # ------------------------------------------------------------------

    def _check_level0(self, function_body: str) -> bool:
        """Check if the code's AST Hash already exists."""
        ast_hash = self._compute_ast_hash(function_body)
        if ast_hash is None:
            return False  # Syntax error, skip this level
        return ast_hash in self._code_hash_set

    def _compute_ast_hash(self, function_body: str) -> str | None:
        """Wrap function body into a complete function definition and compute AST Hash."""
        try:
            # Wrap as complete function definition; ProgramNormalizer requires valid Python code.
            # Note: (item, bins) parameter names are hardcoded. AST normalization ignores type
            # annotations, so no need to write (item: float, bins: np.ndarray).
            # If the function signature parameter names change in the future, update this accordingly.
            wrapped = f"def {self._function_to_evolve}(item, bins):\n{function_body}"
            normalized = self._normalizer.normalize(wrapped)
            return normalized.ast_hash
        except (SyntaxError, Exception):
            return None

    # ------------------------------------------------------------------
    # Level 1: Behavioral fingerprint exact match
    # ------------------------------------------------------------------

    def _check_level1(self, fingerprint: tuple[int, ...]) -> bool:
        """Check if fingerprint Hash already exists (O(1) lookup, zero false positives)."""
        fp_hash = self._hash_fingerprint(fingerprint)
        return fp_hash in self._fingerprint_hash_set

    @staticmethod
    def _hash_fingerprint(fingerprint: tuple[int, ...]) -> str:
        """Convert fingerprint tuple to SHA256 Hash string."""
        return hashlib.sha256(str(fingerprint).encode()).hexdigest()

    # ------------------------------------------------------------------
    # Level 2: Cosine similarity approximate match
    # ------------------------------------------------------------------

    def _check_level2(self, fingerprint: tuple[int, ...]) -> bool:
        """Check if the max cosine similarity between this fingerprint vector and stored vectors exceeds the threshold."""
        if not self._fingerprint_vectors:
            return False
        vec = self._fingerprint_to_vector(fingerprint)
        # Matrix multiplication to compute cosine similarity (all vectors are L2-normalized)
        matrix = np.array(self._fingerprint_vectors)
        similarities = matrix @ vec
        return float(np.max(similarities)) >= self._config.cosine_threshold

    @staticmethod
    def _fingerprint_to_vector(fingerprint: tuple[int, ...]) -> np.ndarray:
        """Convert fingerprint tuple to an L2-normalized float vector."""
        vec = np.array(fingerprint, dtype=np.float64)
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec /= norm
        return vec

    # ------------------------------------------------------------------
    # Register new program (called after passing all levels)
    # ------------------------------------------------------------------

    def _register(self, function_body: str, fingerprint: tuple[int, ...] | None) -> None:
        """Register a new program into the indexes at each level."""
        # Level 0: Register AST Hash
        ast_hash = self._compute_ast_hash(function_body)
        if ast_hash is not None:
            self._code_hash_set.add(ast_hash)

        # Level 1 & 2: Register fingerprint
        if fingerprint is not None:
            fp_hash = self._hash_fingerprint(fingerprint)
            self._fingerprint_hash_set.add(fp_hash)
            vec = self._fingerprint_to_vector(fingerprint)
            self._fingerprint_vectors.append(vec)
