"""
Tests for manifest parsers.
"""

import json
import tempfile
from pathlib import Path

import pytest

from depdrift.parsers import (
    parse_manifest,
    parse_package_json,
    parse_pyproject_toml,
    parse_requirements_txt,
)


class TestRequirementsTxt:
    """Tests for requirements.txt parser."""

    def test_parse_simple_requirements(self, tmp_path):
        """Test parsing simple requirements with exact versions."""
        req_file = tmp_path / "requirements.txt"
        req_file.write_text(
            "requests==2.28.1\n"
            "flask==2.0.0\n"
            "django==4.1.0\n"
        )

        deps = parse_requirements_txt(req_file)

        assert len(deps) == 3
        assert ("requests", "==2.28.1") in deps
        assert ("flask", "==2.0.0") in deps
        assert ("django", "==4.1.0") in deps

    def test_parse_requirements_with_specifiers(self, tmp_path):
        """Test parsing requirements with version specifiers."""
        req_file = tmp_path / "requirements.txt"
        req_file.write_text(
            "requests>=2.28.0\n"
            "flask~=2.0\n"
            "django>=4.0,<5.0\n"
        )

        deps = parse_requirements_txt(req_file)

        assert len(deps) == 3
        assert ("requests", ">=2.28.0") in deps
        assert ("flask", "~=2.0") in deps
        # packaging normalizes specifier order, so check for django name and that it has both constraints
        django_deps = [d for d in deps if d[0] == "django"]
        assert len(django_deps) == 1
        assert ">=4.0" in django_deps[0][1] and "<5.0" in django_deps[0][1]

    def test_parse_requirements_with_comments(self, tmp_path):
        """Test that comments are ignored."""
        req_file = tmp_path / "requirements.txt"
        req_file.write_text(
            "# This is a comment\n"
            "requests==2.28.1\n"
            "flask>=2.0  # inline comment\n"
            "# Another comment\n"
        )

        deps = parse_requirements_txt(req_file)

        assert len(deps) == 2
        assert ("requests", "==2.28.1") in deps
        assert ("flask", ">=2.0") in deps

    def test_parse_requirements_with_empty_lines(self, tmp_path):
        """Test that empty lines are ignored."""
        req_file = tmp_path / "requirements.txt"
        req_file.write_text(
            "\n"
            "requests==2.28.1\n"
            "\n"
            "\n"
            "flask>=2.0\n"
            "\n"
        )

        deps = parse_requirements_txt(req_file)

        assert len(deps) == 2

    def test_parse_requirements_with_extras(self, tmp_path):
        """Test that extras markers are removed."""
        req_file = tmp_path / "requirements.txt"
        req_file.write_text(
            "requests[security]==2.28.1\n"
            "flask[async]>=2.0\n"
        )

        deps = parse_requirements_txt(req_file)

        assert len(deps) == 2
        # Package name should not include extras
        names = [name for name, _ in deps]
        assert "requests" in names
        assert "flask" in names

    def test_parse_requirements_skip_options(self, tmp_path):
        """Test that -r, -e, and -- lines are skipped."""
        req_file = tmp_path / "requirements.txt"
        req_file.write_text(
            "requests==2.28.1\n"
            "-r other-requirements.txt\n"
            "-e git+https://github.com/example/repo.git\n"
            "--index-url https://pypi.org/simple\n"
            "flask>=2.0\n"
        )

        deps = parse_requirements_txt(req_file)

        assert len(deps) == 2
        assert ("requests", "==2.28.1") in deps
        assert ("flask", ">=2.0") in deps


class TestPyprojectToml:
    """Tests for pyproject.toml parser."""

    def test_parse_simple_pyproject(self, tmp_path):
        """Test parsing simple pyproject.toml."""
        pyproject_file = tmp_path / "pyproject.toml"
        pyproject_file.write_text(
            '[project]\n'
            'dependencies = [\n'
            '    "requests==2.28.1",\n'
            '    "flask>=2.0",\n'
            ']\n'
        )

        deps = parse_pyproject_toml(pyproject_file)

        assert len(deps) == 2
        assert ("requests", "==2.28.1") in deps
        assert ("flask", ">=2.0") in deps

    def test_parse_pyproject_no_dependencies(self, tmp_path):
        """Test parsing pyproject.toml with no dependencies."""
        pyproject_file = tmp_path / "pyproject.toml"
        pyproject_file.write_text(
            '[project]\n'
            'name = "myproject"\n'
        )

        deps = parse_pyproject_toml(pyproject_file)

        assert len(deps) == 0

    def test_parse_pyproject_no_project_section(self, tmp_path):
        """Test parsing pyproject.toml with no [project] section."""
        pyproject_file = tmp_path / "pyproject.toml"
        pyproject_file.write_text(
            '[tool.pytest.ini_options]\n'
            'testpaths = ["tests"]\n'
        )

        deps = parse_pyproject_toml(pyproject_file)

        assert len(deps) == 0

    def test_parse_pyproject_with_extras(self, tmp_path):
        """Test parsing dependencies with extras."""
        pyproject_file = tmp_path / "pyproject.toml"
        pyproject_file.write_text(
            '[project]\n'
            'dependencies = [\n'
            '    "requests[security]==2.28.1",\n'
            ']\n'
        )

        deps = parse_pyproject_toml(pyproject_file)

        assert len(deps) == 1
        name, _ = deps[0]
        assert name == "requests"


class TestPackageJson:
    """Tests for package.json parser."""

    def test_parse_simple_package_json(self, tmp_path):
        """Test parsing simple package.json."""
        package_file = tmp_path / "package.json"
        data = {
            "dependencies": {
                "lodash": "4.17.21",
                "express": "^4.18.0",
            }
        }
        package_file.write_text(json.dumps(data))

        deps = parse_package_json(package_file)

        assert len(deps) == 2
        assert ("lodash", "4.17.21") in deps
        assert ("express", "^4.18.0") in deps

    def test_parse_package_json_with_dev_dependencies(self, tmp_path):
        """Test parsing package.json with devDependencies."""
        package_file = tmp_path / "package.json"
        data = {
            "dependencies": {
                "lodash": "4.17.21",
            },
            "devDependencies": {
                "jest": "^29.0.0",
            }
        }
        package_file.write_text(json.dumps(data))

        deps = parse_package_json(package_file)

        assert len(deps) == 2
        assert ("lodash", "4.17.21") in deps
        assert ("jest", "^29.0.0") in deps

    def test_parse_package_json_no_dependencies(self, tmp_path):
        """Test parsing package.json with no dependencies."""
        package_file = tmp_path / "package.json"
        data = {
            "name": "myproject",
            "version": "1.0.0",
        }
        package_file.write_text(json.dumps(data))

        deps = parse_package_json(package_file)

        assert len(deps) == 0

    def test_parse_package_json_version_prefixes(self, tmp_path):
        """Test that version prefixes like ^ and ~ are preserved."""
        package_file = tmp_path / "package.json"
        data = {
            "dependencies": {
                "pkg1": "^1.0.0",
                "pkg2": "~2.0.0",
                "pkg3": ">=3.0.0",
            }
        }
        package_file.write_text(json.dumps(data))

        deps = parse_package_json(package_file)

        assert len(deps) == 3
        assert ("pkg1", "^1.0.0") in deps
        assert ("pkg2", "~2.0.0") in deps
        assert ("pkg3", ">=3.0.0") in deps


class TestParseManifest:
    """Tests for auto-detect parse_manifest function."""

    def test_parse_manifest_requirements_txt(self, tmp_path):
        """Test auto-detect for requirements.txt."""
        req_file = tmp_path / "requirements.txt"
        req_file.write_text("requests==2.28.1\n")

        deps = parse_manifest(req_file)

        assert len(deps) == 1
        assert ("requests", "==2.28.1") in deps

    def test_parse_manifest_pyproject_toml(self, tmp_path):
        """Test auto-detect for pyproject.toml."""
        pyproject_file = tmp_path / "pyproject.toml"
        pyproject_file.write_text(
            '[project]\n'
            'dependencies = ["requests==2.28.1"]\n'
        )

        deps = parse_manifest(pyproject_file)

        assert len(deps) == 1
        assert ("requests", "==2.28.1") in deps

    def test_parse_manifest_package_json(self, tmp_path):
        """Test auto-detect for package.json."""
        package_file = tmp_path / "package.json"
        data = {"dependencies": {"lodash": "4.17.21"}}
        package_file.write_text(json.dumps(data))

        deps = parse_manifest(package_file)

        assert len(deps) == 1
        assert ("lodash", "4.17.21") in deps

    def test_parse_manifest_unsupported_file(self, tmp_path):
        """Test that unsupported files raise ValueError."""
        unsupported_file = tmp_path / "deps.yaml"
        unsupported_file.write_text("requests: 2.28.1\n")

        with pytest.raises(ValueError, match="Unsupported manifest file"):
            parse_manifest(unsupported_file)
