<p align="center">
  <img src="assets/infographic.png" alt="DepDrift" width="800">
</p>

<h3 align="center">CLI tool that reads requirements.txt/pyproject.toml/package.json and reports how far behind each dependency is from latest, grouped by severity (patch/minor/major). JSON or terminal table output.</h3>

<p align="center">
  <a href="#quick-start">Quick Start</a> &bull;
  <a href="#features">Features</a> &bull;
  <a href="#examples">Examples</a> &bull;
  <a href="#contributing">Contributing</a>
</p>

## What is this?
DepDrift is a command‑line utility that scans dependency manifest files and reports how many versions each package lags behind the latest release, sorting the results by update severity. It is ideal for solo maintainers or small teams who want a quick, local view of dependency staleness without setting up external bots.

Example:
```
$ depdrift --file requirements.txt
Package        Current  Latest  Severity
requests       2.25.1   2.31.0  minor
numpy          1.21.0   1.24.2  major
```

## Problem
Dependency staleness accumulates silently in projects, especially those maintained by solo developers. Existing tools (dependabot, renovate) require hosted infrastructure; no simple CLI gives a local staleness report.

## Features
| Feature | Description |
|---------|-------------|
| Multi‑format support | Parses requirements.txt, pyproject.toml, and package.json files |
| Version distance calculation | Computes exact version difference between installed and latest releases |
| Severity grouping | Classifies updates as patch, minor, or major based on semantic versioning |
| Dual output modes | Renders results as a terminal table or machine‑readable JSON |
| Auto‑detect mode | Automatically locates a supported manifest in the current directory |
| Quiet flag | Suppresses informational messages for CI‑friendly output |

## Quick Start
1. Clone the repository:  
   `git clone https://github.com/yourusername/DepDrift.git`
2. Enter the project directory:  
   `cd DepDrift`
3. Install the package in editable mode:  
   `pip install -e .`
4. Run a basic check on a requirements file:  
   `depdrift --file requirements.txt`

## Examples
**Basic requirements check**  
Run DepDrift on a Python project’s requirements file.  
```
$ depdrift --file requirements.txt
Package        Current  Latest  Severity
requests       2.25.1   2.31.0  minor
numpy          1.21.0   1.24.2  major
```

**JSON output for CI integration**  
Generate a JSON payload that can be consumed by automated scripts.  
```
$ depdrift --file pyproject.toml --output json
{
  "dependencies": [
    {"name": "requests", "current": "2.25.1", "latest": "2.31.0", "severity": "minor"},
    {"name": "django",   "current": "3.2.0",   "latest": "4.2.0",   "severity": "major"}
  ]
}
```

**Package.json scan with quiet mode**  
Check a Node.js project while suppressing extra output.  
```
$ depdrift --file package.json --quiet
lodash   4.17.15  4.17.21  patch
express  4.16.0   4.18.2   minor
```

## File Structure
```
DepDrift/
  depdrift/          # Core source code
    __init__.py
    __main__.py      # CLI entry point
    main.py          # Orchestrates parsing, checking, and output
    models.py        # Data models for dependencies and releases
    output.py        # Table and JSON formatting logic
    parsers.py       # Parsers for requirements.txt, pyproject.toml, package.json
    utils.py         # Helper functions (version comparison, file detection)
    version.py       # Version metadata
  tests/             # Unit test suite
    test_parsers.py
    test_output.py
    test_version.py
  .gitignore
  README.md
  init.sh
```

## Tech Stack
| Technology | Purpose |
|------------|---------|
| Python 3.8+ | Core language |
| packaging   | Version parsing and comparison |
| toml        | Reading pyproject.toml files |
| json        | Built‑in handling of package.json |
| setuptools  | Project packaging and distribution |

## Contributing
Fork the repo, make your changes, run the test suite, and submit a pull request.  
Please keep code style consistent with the existing base.

## License
MIT

## Author
```
Matthew Snow -- [M2AI](https://m2ai.co) | [@m2ai-portfolio](https://github.com/m2ai-portfolio)