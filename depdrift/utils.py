"""
Utility functions for DepDrift.
"""

import os
from pathlib import Path
from typing import Optional


def find_manifest_file(directory: str = ".") -> Optional[Path]:
    """
    Find a manifest file in the given directory.

    Searches in order: pyproject.toml, requirements.txt, package.json

    Args:
        directory: Directory to search in (default: current directory)

    Returns:
        Path to the found manifest file, or None if not found
    """
    dir_path = Path(directory).resolve()

    manifest_names = ["pyproject.toml", "requirements.txt", "package.json"]

    for name in manifest_names:
        candidate = dir_path / name
        if candidate.exists() and candidate.is_file():
            return candidate

    return None


def normalize_package_name(name: str) -> str:
    """
    Normalize package name by removing extras and whitespace.

    Args:
        name: Package name (e.g., "package[extra]")

    Returns:
        Normalized package name (e.g., "package")
    """
    # Remove extras marker [...]
    if "[" in name:
        name = name.split("[")[0]

    return name.strip()
