"""
Main CLI entry point for DepDrift.
"""

import os
import sys
from pathlib import Path

import click

from .models import Dependency
from .output import format_output
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
@click.option(
    "--json",
    "json_output",
    is_flag=True,
    help="Output results as JSON instead of ASCII table",
)
def main(file_path: Path = None, versions_path: Path = None, json_output: bool = False):
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

    # Determine output format
    # Priority: --json flag > DEPDRIFT_OUTPUT env var > default (table)
    if json_output:
        output_format = "json"
    else:
        env_output = os.environ.get("DEPDRIFT_OUTPUT", "table")
        output_format = env_output.lower()

    # Validate output format
    if output_format not in ["table", "json"]:
        click.echo(
            f"Error: Invalid output format '{output_format}'. "
            "Must be 'table' or 'json'.",
            err=True,
        )
        sys.exit(1)

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
        except Exception as e:
            click.echo(f"Error loading versions file: {e}", err=True)
            sys.exit(1)

    # Format and output results
    output = format_output(dependencies, output_format)
    click.echo(output)


if __name__ == "__main__":
    main()
