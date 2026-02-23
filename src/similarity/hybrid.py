"""
Hybrid similarity detector combining embedding and AST comparison.

This module provides a hybrid detector that uses embedding-based pre-filtering
followed by AST verification for accurate duplicate detection.
"""

import time
from typing import Optional

import numpy as np

from src.normalizer.models import NormalizedProgram
from src.similarity.models import SimilarityResult, DetectorConfig
from src.similarity.embedding import compute_embedding, cosine_similarity
from src.similarity.ast_compare import compute_ast_similarity, compute_ast_hash


class HybridSimilarityDetector:
    """
    Hybrid detector combining embedding and AST-based similarity.

    Uses a two-stage approach:
    1. Embedding-based pre-filtering (fast)
    2. AST-based verification (accurate)
    """

    def __init__(self, config: Optional[DetectorConfig] = None):
        """
        Initialize the detector.

        Args:
            config: Detector configuration (uses defaults if None)
        """
        self.config = config or DetectorConfig()

    def is_similar(
        self,
        program_a: NormalizedProgram,
        program_b: NormalizedProgram,
    ) -> SimilarityResult:
        """
        Check if two programs are similar.

        Args:
            program_a: First normalized program
            program_b: Second normalized program

        Returns:
            SimilarityResult with similarity scores and duplicate status
        """
        start_time = time.time()

        # Quick hash check first
        if program_a.ast_hash == program_b.ast_hash:
            detection_time = time.time() - start_time
            return SimilarityResult(
                program_a_id=program_a.ast_hash,
                program_b_id=program_b.ast_hash,
                embedding_similarity=1.0,
                ast_similarity=1.0,
                is_duplicate=True,
                detection_time=detection_time,
                detection_method="hash_match",
            )

        embedding_similarity = 0.0
        ast_similarity = 0.0
        detection_method = "ast_only"

        # Stage 1: Embedding-based pre-filtering (if enabled)
        if self.config.use_embedding:
            # Get or compute embeddings
            if not program_a.has_embedding:
                program_a.embedding = list(compute_embedding(program_a.canonical_code))
            if not program_b.has_embedding:
                program_b.embedding = list(compute_embedding(program_b.canonical_code))

            emb_a = np.array(program_a.embedding)
            emb_b = np.array(program_b.embedding)
            embedding_similarity = cosine_similarity(emb_a, emb_b)

            # If embedding similarity is too low, skip AST check
            if embedding_similarity < self.config.embedding_threshold:
                detection_time = time.time() - start_time
                return SimilarityResult(
                    program_a_id=program_a.ast_hash,
                    program_b_id=program_b.ast_hash,
                    embedding_similarity=embedding_similarity,
                    ast_similarity=0.0,
                    is_duplicate=False,
                    detection_time=detection_time,
                    detection_method="embedding_only",
                )

            detection_method = "hybrid"

        # Stage 2: AST-based verification
        ast_similarity = compute_ast_similarity(
            program_a.canonical_code,
            program_b.canonical_code,
        )

        # Determine if duplicate
        is_duplicate = (
            embedding_similarity >= self.config.embedding_threshold
            and ast_similarity >= self.config.ast_threshold
        )

        detection_time = time.time() - start_time

        return SimilarityResult(
            program_a_id=program_a.ast_hash,
            program_b_id=program_b.ast_hash,
            embedding_similarity=embedding_similarity,
            ast_similarity=ast_similarity,
            is_duplicate=is_duplicate,
            detection_time=detection_time,
            detection_method=detection_method,
        )

    def find_similar(
        self,
        program: NormalizedProgram,
        candidates: list[NormalizedProgram],
        k: int = 5,
    ) -> list[SimilarityResult]:
        """
        Find the most similar programs from a list of candidates.

        Args:
            program: Target program to compare against
            candidates: List of candidate programs
            k: Maximum number of results to return

        Returns:
            List of SimilarityResult objects, sorted by similarity
        """
        if not candidates:
            return []

        results = []
        for candidate in candidates:
            result = self.is_similar(program, candidate)
            results.append(result)

        # Sort by combined score (descending)
        results.sort(key=lambda r: r.combined_score, reverse=True)

        return results[:k]

    def check_duplicate(
        self,
        program: NormalizedProgram,
        archive: "ProgramArchive",
    ) -> Optional[SimilarityResult]:
        """
        Check if program is a duplicate of any in the archive.

        Args:
            program: Program to check
            archive: Program archive to search

        Returns:
            SimilarityResult if duplicate found, None otherwise
        """
        # First check exact hash match
        for stored_program in archive:
            if stored_program.ast_hash == program.ast_hash:
                return SimilarityResult(
                    program_a_id=program.ast_hash,
                    program_b_id=stored_program.ast_hash,
                    embedding_similarity=1.0,
                    ast_similarity=1.0,
                    is_duplicate=True,
                    detection_time=0.0,
                    detection_method="hash_match",
                )

        # Check similarity with all programs
        candidates = list(archive)
        results = self.find_similar(program, candidates, k=1)

        if results and results[0].is_duplicate:
            return results[0]

        return None
