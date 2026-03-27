# DepDrift

A CLI tool to analyze dependency staleness across Python and Node.js projects.

DepDrift reads your project's dependency manifest (`requirements.txt`, `pyproject.toml`, or `package.json`), compares each declared version against a user-supplied "latest versions" lookup file, and reports how far behind each dependency is -- grouped by semantic version distance (patch, minor, major).

## Features
- **Multi-format manifest parsing** -- supports `requirements.txt`, `pyproject.toml` (PEP 621), and `package.json` (both `dependencies` and `devDependencies`)
- **Auto-detection** -- if no `--file` is given, searches the current directory for `pyproject.toml`, `requirements.txt`, or `package.json` (in that order)
- **Semver distance classification** -- categorizes each dependency as `up-to-date`, `patch`, `minor`, `major`, or `unknown`
- **Flexible output** -- ASCII table (default) or JSON, controlled via `--json` flag or `DEPDRIFT_OUTPUT` env var
- **Version specifier handling** -- strips operators (`>=`, `~=`, `^`, `~`, `==`) to extract bare version numbers for comparison

## Project Structure
```
depdrift/
  __init__.py
  __main__.py     # python -m depdrift entry point
  main.py         # Click CLI: --file, --versions, --json options
  parsers.py      # Manifest parsers (requirements.txt, pyproject.toml, package.json)
  models.py       # Dependency dataclass (name, current, latest, distance)
  version.py      # Version extraction, semver distance computation, versions file loader
  output.py       # ASCII table and JSON formatters
  utils.py        # Manifest auto-detection, package name normalization
tests/            # pytest test suite
init.sh           # Bootstrap script
```

## Quick Start

```bash
git clone https://github.com/m2ai-portfolio/depdrift.git
cd depdrift
./init.sh

# Run against a requirements file with a versions lookup
python -m depdrift --file requirements.txt --versions versions.json

# JSON output
python -m depdrift --file requirements.txt --versions versions.json --json
```

## The `versions.json` File

DepDrift compares your declared dependency versions against a lookup file that maps package names to their latest known versions. This file is a flat JSON object:

```json
{
  "requests": "2.31.0",
  "flask": "3.0.2",
  "click": "8.1.7",
  "react": "18.2.0",
  "express": "4.18.3"
}
```

You supply this file yourself -- it can be generated from `pip index versions`, `npm view <pkg> version`, or any registry API. DepDrift intentionally does not call external registries at runtime, keeping it offline-safe and deterministic.

If no `--versions` flag is provided, DepDrift looks for `versions.json` in the current directory, or checks the `DEPDRIFT_VERSFILE` environment variable.

## Supported Manifest Formats

| Format | Parser | Notes |
|--------|--------|-------|
| `requirements.txt` | `parse_requirements_txt` | Skips comments, `-r`/`-e`/`--` lines. Handles `>=`, `==`, `~=` specifiers. |
| `pyproject.toml` | `parse_pyproject_toml` | Reads `[project.dependencies]` (PEP 621). Uses `tomllib`. |
| `package.json` | `parse_package_json` | Merges `dependencies` + `devDependencies`. Preserves `^`/`~` prefixes for display. |

## Example Output

**Table format (default):**
```
Package                        Current              Latest               Distance
---------------------------------------------------------------------------------------
requests                       2.28.1               2.31.0               minor
flask                          2.3.0                3.0.2                major
click                          8.1.7                8.1.7                up-to-date
numpy                          1.24.0               <missing>            unknown
```

**JSON format (`--json`):**
```json
[
  {"package": "requests", "current": "2.28.1", "latest": "2.31.0", "distance": "minor"},
  {"package": "flask", "current": "2.3.0", "latest": "3.0.2", "distance": "major"},
  {"package": "click", "current": "8.1.7", "latest": "8.1.7", "distance": "up-to-date"}
]
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DEPDRIFT_VERSFILE` | Path to the versions JSON lookup file | `versions.json` |
| `DEPDRIFT_OUTPUT` | Output format (`table` or `json`) | `table` |

## Running Tests
```bash
pip install -e ".[dev]"
pytest tests/
```

## License
MIT
