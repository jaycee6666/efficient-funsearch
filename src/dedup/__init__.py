"""Phase 2: Behavioral deduplication module — three-level filter funnel to detect and skip functionally duplicate programs."""

from src.dedup.dedup_config import DedupConfig
from src.dedup.dedup_filter import DedupFilter, DedupResult

__all__ = ["DedupConfig", "DedupFilter", "DedupResult"]
