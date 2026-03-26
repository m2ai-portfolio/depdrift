"""
Manifest file parsers for different dependency formats.
"""

import json
import re
import tomllib
from pathlib import Path
from typing import List, Tuple

from packaging.requirements import Requirement

from .utils import normalize_package_name


def parse_requirements_txt(file_path: Path) -> List[Tuple[str, str]]:
    """
    Parse a requirements.txt file.

    Args:
        file_path: Path to requirements.txt

    Returns:
        List of (package_name, version_string) tuples
    """
    dependencies = []

    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            # Remove comments
            line = line.split("#")[0].strip()

            # Skip empty lines
            if not line:
                continue

            # Skip lines starting with -r, -e, --
            if line.startswith(("-r", "-e", "--")):
                continue

            try:
                # Use packaging.requirements to parse
                req = Requirement(line)
                name = normalize_package_name(req.name)

                # Extract version specifier as raw string
                if req.specifier:
                    version_str = str(req.specifier)
                else:
                    # No version specified
                    version_str = "*"

                dependencies.append((name, version_str))

            except Exception:
                # If parsing fails, try simple regex fallback
                match = re.match(r"([a-zA-Z0-9_-]+)(.*)", line)
                if match:
                    name = normalize_package_name(match.group(1))
                    version_str = match.group(2).strip() or "*"
                    dependencies.append((name, version_str))

    return dependencies


def parse_pyproject_toml(file_path: Path) -> List[Tuple[str, str]]:
    """
    Parse a pyproject.toml file (PEP 621 format).

    Args:
        file_path: Path to pyproject.toml

    Returns:
        List of (package_name, version_string) tuples
    """
    dependencies = []

    with open(file_path, "rb") as f:
        data = tomllib.load(f)

    # Look for [project.dependencies] section
    project = data.get("project", {})
    deps_list = project.get("dependencies", [])

    for dep_str in deps_list:
        try:
            req = Requirement(dep_str)
            name = normalize_package_name(req.name)

            # Extract version specifier as raw string
            if req.specifier:
                version_str = str(req.specifier)
            else:
                version_str = "*"

            dependencies.append((name, version_str))

        except Exception:
            # Fallback to simple parsing
            match = re.match(r"([a-zA-Z0-9_-]+)(.*)", dep_str)
            if match:
                name = normalize_package_name(match.group(1))
                version_str = match.group(2).strip() or "*"
                dependencies.append((name, version_str))

    return dependencies


def parse_package_json(file_path: Path) -> List[Tuple[str, str]]:
    """
    Parse a package.json file.

    Args:
        file_path: Path to package.json

    Returns:
        List of (package_name, version_string) tuples
    """
    dependencies = []

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Get both dependencies and devDependencies
    deps = data.get("dependencies", {})
    dev_deps = data.get("devDependencies", {})

    # Combine both
    all_deps = {**deps, **dev_deps}

    for name, version in all_deps.items():
        # npm version strings can have ^ or ~ prefixes, keep them as-is for now
        dependencies.append((name, version))

    return dependencies


def parse_manifest(file_path: Path) -> List[Tuple[str, str]]:
    """
    Auto-detect and parse a manifest file based on its name.

    Args:
        file_path: Path to the manifest file

    Returns:
        List of (package_name, version_string) tuples

    Raises:
        ValueError: If the file format is not supported
    """
    file_name = file_path.name.lower()

    if file_name == "requirements.txt":
        return parse_requirements_txt(file_path)
    elif file_name == "pyproject.toml":
        return parse_pyproject_toml(file_path)
    elif file_name == "package.json":
        return parse_package_json(file_path)
    else:
        raise ValueError(f"Unsupported manifest file: {file_name}")
