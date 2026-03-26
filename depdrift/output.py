"""
Output formatters for DepDrift.
"""

import json
from typing import List

from .models import Dependency


def format_table(deps: List[Dependency]) -> str:
    """
    Format dependencies as an aligned ASCII table.

    Args:
        deps: List of Dependency objects

    Returns:
        Formatted table string with columns: Package, Current, Latest, Distance
        Truncates version strings longer than 20 characters.
    """
    if not deps:
        return ""

    # Check if we have full version info (latest/distance)
    has_version_info = any(dep.latest is not None for dep in deps)

    if has_version_info:
        # Full table with all columns
        header = f"{'Package':<30} {'Current':<20} {'Latest':<20} {'Distance':<15}"
        separator = "-" * 87

        lines = [header, separator]

        for dep in deps:
            package_name = dep.name[:30]  # Truncate if too long
            current_ver = dep.current_parsed or dep.current
            current_ver = str(current_ver)[:20]  # Truncate if too long
            latest_ver = dep.latest if dep.latest else "<missing>"
            latest_ver = str(latest_ver)[:20]  # Truncate if too long
            distance = dep.distance or "unknown"

            line = f"{package_name:<30} {current_ver:<20} {latest_ver:<20} {distance:<15}"
            lines.append(line)
    else:
        # Simple table with just Package and Current
        header = f"{'Package':<30} {'Current':<20}"
        separator = "-" * 52

        lines = [header, separator]

        for dep in deps:
            package_name = dep.name[:30]  # Truncate if too long
            current_ver = dep.current[:20]  # Truncate if too long

            line = f"{package_name:<30} {current_ver:<20}"
            lines.append(line)

    return "\n".join(lines)


def format_json(deps: List[Dependency]) -> str:
    """
    Format dependencies as JSON array.

    Args:
        deps: List of Dependency objects

    Returns:
        JSON string with array of objects containing:
        package, current, latest, distance fields
    """
    result = []

    for dep in deps:
        obj = {
            "package": dep.name,
            "current": dep.current_parsed or dep.current,
            "latest": dep.latest,
            "distance": dep.distance
        }
        result.append(obj)

    return json.dumps(result, indent=2)


def format_output(deps: List[Dependency], output_format: str) -> str:
    """
    Format dependencies according to the specified output format.

    Args:
        deps: List of Dependency objects
        output_format: Either "table" or "json"

    Returns:
        Formatted output string

    Raises:
        ValueError: If output_format is not "table" or "json"
    """
    if output_format == "table":
        return format_table(deps)
    elif output_format == "json":
        return format_json(deps)
    else:
        raise ValueError(f"Invalid output format: {output_format}. Must be 'table' or 'json'.")
