"""
Data models for DepDrift.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Dependency:
    """
    Represents a single dependency from a manifest file.

    Attributes:
        name: Package name
        current: Raw version string from manifest (may contain specifiers)
        current_parsed: Normalized version (e.g., "2.28.1")
        latest: Latest available version
        distance: Version distance ("major", "minor", "patch", "up-to-date", "unknown")
    """
    name: str
    current: str
    current_parsed: Optional[str] = None
    latest: Optional[str] = None
    distance: Optional[str] = None
