"""
Program archive module.

This module provides storage for evaluated programs with efficient
duplicate detection capabilities.
"""

from src.archive.models import Program
from src.archive.program_archive import ProgramArchive

__all__ = ["Program", "ProgramArchive"]
