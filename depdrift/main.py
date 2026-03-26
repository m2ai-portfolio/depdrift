"""
Main CLI entry point for DepDrift.
"""

import os
import sys
from pathlib import Path

import click

from .models import Dependency
from .parsers import parse_manifest
from .utils import find_manifest_file
from .version import check_versions, load_versions_file


@click.command()
@click.option(
    "--file",
    "file_path",
    type=click.Path(exists=True, path_type=Path),
    help="Path to manifest file (requirements.txt, pyproject.toml, or package.json)",
)
@click.option(
    "--versions",
    "versions_path",
    type=click.Path(exists=True, path_type=Path),
    help="Path to versions JSON file containing latest versions",
)
def main(file_path: Path = None, versions_path: Path = None):
    """
    DepDrift - Check how stale your dependencies are.

    Parses a dependency manifest and shows current versions.
    """
    # Find manifest file
    if file_path is None:
        file_path = find_manifest_file()
        if file_path is None:
            click.echo(
                "Error: No manifest file found. Provide --file or ensure "
                "pyproject.toml/requirements.txt/package.json exists.",
                err=True,
            )
            sys.exit(2)

    # Parse the manifest
    try:
        deps_list = parse_manifest(file_path)
    except Exception as e:
        click.echo(f"Error parsing {file_path}: {e}", err=True)
        sys.exit(1)

    if not deps_list:
        click.echo("No dependencies found in manifest.")
        return

    # Create Dependency objects
    dependencies = [
        Dependency(name=name, current=version)
        for name, version in deps_list
    ]

    # Determine versions file path
    if versions_path is None:
        # Check environment variable
        env_versions = os.environ.get("DEPDRIFT_VERSFILE")
        if env_versions:
            versions_path = Path(env_versions)
        else:
            # Default to versions.json
            versions_path = Path("versions.json")

    # Check if versions file exists and run version checking
    if versions_path.exists():
        try:
            versions = load_versions_file(str(versions_path))
            dependencies = check_versions(dependencies, versions)
            print_full_table(dependencies)
        except Exception as e:
            click.echo(f"Error loading versions file: {e}", err=True)
            sys.exit(1)
    else:
        # No versions file, just print simple table
        print_simple_table(dependencies)


def print_simple_table(dependencies: list[Dependency]):
    """
    Print a simple table of dependencies.

    Args:
        dependencies: List of Dependency objects
    """
    # Header
    click.echo(f"{'Package':<30} {'Current':<20}")
    click.echo("-" * 52)

    # Rows
    for dep in dependencies:
        package_name = dep.name[:30]  # Truncate if too long
        current_ver = dep.current[:20]  # Truncate if too long
        click.echo(f"{package_name:<30} {current_ver:<20}")


def print_full_table(dependencies: list[Dependency]):
    """
    Print a full table of dependencies with version information.

    Args:
        dependencies: List of Dependency objects with version info
    """
    # Header
    click.echo(f"{'Package':<30} {'Current':<20} {'Latest':<20} {'Distance':<15}")
    click.echo("-" * 87)

    # Rows
    for dep in dependencies:
        package_name = dep.name[:30]  # Truncate if too long
        current_ver = dep.current_parsed or dep.current
        current_ver = current_ver[:20]  # Truncate if too long
        latest_ver = dep.latest if dep.latest else "<missing>"
        latest_ver = latest_ver[:20]  # Truncate if too long
        distance = dep.distance or "unknown"

        click.echo(f"{package_name:<30} {current_ver:<20} {latest_ver:<20} {distance:<15}")


if __name__ == "__main__":
    main()
