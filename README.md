# DepDrift

A CLI tool to analyze dependency staleness across Python/Node projects.

DepDrift reads your project's dependency manifest (requirements.txt, pyproject.toml, or package.json), compares each declared version against a user-supplied "latest versions" lookup file, and reports how far behind each dependency is — grouped by semantic version distance (patch, minor, major).

## Quick Start

```bash
# Install dependencies
./init.sh

# Run with a requirements file
python -m depdrift --file requirements.txt --versions versions.json

# Output as JSON
python -m depdrift --file requirements.txt --versions versions.json --json
```

## Tech Stack
- Python 3.11+
- click (CLI ergonomics)
- packaging (version parsing)
- pytest (testing)
