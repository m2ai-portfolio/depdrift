"""
Version comparison and distance calculation for DepDrift.
"""

import json
import re
from pathlib import Path
from typing import List, Optional

from packaging.version import parse as parse_version, Version

from .models import Dependency


def extract_version(version_str: str) -> str:
    """
    Extract bare version string from a version specifier.

    Strips version operators like >=, ~=, ==, ^, ~ etc. and returns the version number.

    Args:
        version_str: Raw version string with possible specifiers (e.g., ">=2.0", "~=1.5.0")

    Returns:
        Bare version string (e.g., "2.0", "1.5.0")

    Examples:
        >>> extract_version(">=2.28.0")
        "2.28.0"
        >>> extract_version("==1.5.0")
        "1.5.0"
        >>> extract_version("~=2.0")
        "2.0"
        >>> extract_version("^4.18.0")
        "4.18.0"
        >>> extract_version("2.28.1")
        "2.28.1"
    """
    # Remove common version specifiers: ==, >=, <=, >, <, ~=, !=, ^, ~
    # Also handle multiple constraints like ">=4.0,<5.0"

    # First, handle npm-style operators (^, ~)
    version_str = version_str.strip()

    # Remove operators and whitespace
    # Pattern matches operators at the start and extracts the version part
    pattern = r'^[\s\^~]*[><=!~]*[\s]*([0-9][0-9a-zA-Z\.\-]*)'
    match = re.search(pattern, version_str)

    if match:
        version = match.group(1)
        # If there are multiple constraints (e.g., ">=4.0,<5.0"), take the first one
        if ',' in version:
            version = version.split(',')[0].strip()
        return version

    # Fallback: if no match, try to find any version-like pattern
    version_pattern = r'([0-9]+\.?[0-9]*\.?[0-9]*[a-zA-Z0-9\-]*)'
    match = re.search(version_pattern, version_str)
    if match:
        return match.group(1)

    # If all else fails, return the original string
    return version_str


def compute_distance(current: str, latest: str) -> str:
    """
    Compute version distance between current and latest versions.

    Uses semantic versioning to determine if the gap is major, minor, patch, or up-to-date.

    Args:
        current: Current version string (e.g., "2.28.1")
        latest: Latest version string (e.g., "2.30.0")

    Returns:
        Distance string: "major", "minor", "patch", or "up-to-date"

    Examples:
        >>> compute_distance("2.28.1", "3.0.0")
        "major"
        >>> compute_distance("2.28.1", "2.30.0")
        "minor"
        >>> compute_distance("2.28.1", "2.28.5")
        "patch"
        >>> compute_distance("2.28.1", "2.28.1")
        "up-to-date"
    """
    try:
        current_ver: Version = parse_version(current)
        latest_ver: Version = parse_version(latest)

        # Extract major, minor, patch components
        # packaging.version.Version stores these in the release tuple
        current_parts = current_ver.release
        latest_parts = latest_ver.release

        # Ensure we have at least 3 parts (major, minor, patch)
        current_major = current_parts[0] if len(current_parts) > 0 else 0
        current_minor = current_parts[1] if len(current_parts) > 1 else 0
        current_patch = current_parts[2] if len(current_parts) > 2 else 0

        latest_major = latest_parts[0] if len(latest_parts) > 0 else 0
        latest_minor = latest_parts[1] if len(latest_parts) > 1 else 0
        latest_patch = latest_parts[2] if len(latest_parts) > 2 else 0

        # Check if versions are the same
        if current_ver == latest_ver:
            return "up-to-date"

        # Check major version difference
        if latest_major > current_major:
            return "major"

        # Check minor version difference
        if latest_minor > current_minor:
            return "minor"

        # Check patch version difference
        if latest_patch > current_patch:
            return "patch"

        # If latest is older than current (shouldn't happen normally)
        # Still return up-to-date to avoid confusion
        return "up-to-date"

    except Exception as e:
        # If version parsing fails, return unknown
        return "unknown"


def load_versions_file(path: str) -> dict:
    """
    Load the versions lookup file.

    Args:
        path: Path to JSON file containing {package: version} mappings

    Returns:
        Dictionary mapping package names to version strings

    Raises:
        FileNotFoundError: If the file doesn't exist
        json.JSONDecodeError: If the file is not valid JSON
    """
    file_path = Path(path)

    if not file_path.exists():
        raise FileNotFoundError(f"Versions file not found: {path}")

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Validate that it's a flat dictionary
    if not isinstance(data, dict):
        raise ValueError("Versions file must contain a JSON object")

    return data


def check_versions(deps: List[Dependency], versions: dict) -> List[Dependency]:
    """
    Check versions for all dependencies and fill in latest/distance fields.

    Args:
        deps: List of Dependency objects
        versions: Dictionary mapping package names to latest versions

    Returns:
        Updated list of Dependency objects with latest/distance/current_parsed filled
    """
    for dep in deps:
        # Extract the bare version from the current version string
        dep.current_parsed = extract_version(dep.current)

        # Look up the latest version
        if dep.name in versions:
            dep.latest = versions[dep.name]

            # Compute distance
            dep.distance = compute_distance(dep.current_parsed, dep.latest)
        else:
            # Package not found in versions file
            dep.latest = None
            dep.distance = "unknown"

    return deps
