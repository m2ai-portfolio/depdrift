"""
Main CLI entry point for DepDrift.
"""

import sys
from pathlib import Path

import click

from .models import Dependency
from .parsers import parse_manifest
from .utils import find_manifest_file


@click.command()
@click.option(
    "--file",
    "file_path",
    type=click.Path(exists=True, path_type=Path),
    help="Path to manifest file (requirements.txt, pyproject.toml, or package.json)",
)
def main(file_path: Path = None):
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

    # For Feature 1, just print a simple table
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


if __name__ == "__main__":
    main()
