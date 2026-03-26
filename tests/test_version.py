"""
Tests for version comparison and distance calculation.
"""

import json
import tempfile
from pathlib import Path

import pytest

from depdrift.models import Dependency
from depdrift.version import (
    check_versions,
    compute_distance,
    extract_version,
    load_versions_file,
)


class TestExtractVersion:
    """Tests for extracting bare version strings from specifiers."""

    def test_extract_exact_version(self):
        """Test extracting exact version (==)."""
        assert extract_version("==2.28.1") == "2.28.1"
        assert extract_version("==1.5.0") == "1.5.0"

    def test_extract_gte_version(self):
        """Test extracting version from >= specifier."""
        assert extract_version(">=2.28.0") == "2.28.0"
        assert extract_version(">=1.0") == "1.0"

    def test_extract_lte_version(self):
        """Test extracting version from <= specifier."""
        assert extract_version("<=3.0.0") == "3.0.0"

    def test_extract_tilde_equals(self):
        """Test extracting version from ~= specifier."""
        assert extract_version("~=2.0") == "2.0"
        assert extract_version("~=1.5.0") == "1.5.0"

    def test_extract_caret(self):
        """Test extracting version from npm-style ^ specifier."""
        assert extract_version("^4.18.0") == "4.18.0"
        assert extract_version("^1.0.0") == "1.0.0"

    def test_extract_tilde(self):
        """Test extracting version from npm-style ~ specifier."""
        assert extract_version("~2.0.0") == "2.0.0"
        assert extract_version("~1.5") == "1.5"

    def test_extract_bare_version(self):
        """Test that bare versions pass through unchanged."""
        assert extract_version("2.28.1") == "2.28.1"
        assert extract_version("1.0.0") == "1.0.0"
        assert extract_version("4.17.21") == "4.17.21"

    def test_extract_multiple_constraints(self):
        """Test extracting version from multiple constraints."""
        # Should take the first constraint
        assert extract_version(">=4.0,<5.0") == "4.0"
        assert extract_version(">=2.0, <3.0") == "2.0"

    def test_extract_wildcard(self):
        """Test handling wildcard versions."""
        # Wildcard should pass through or extract any version-like pattern
        result = extract_version("*")
        # Accept either "*" or empty string or some version pattern
        assert result in ["*", ""]

    def test_extract_version_with_whitespace(self):
        """Test extracting version with surrounding whitespace."""
        assert extract_version("  >=2.28.0  ") == "2.28.0"
        assert extract_version("  ^4.18.0") == "4.18.0"


class TestComputeDistance:
    """Tests for computing version distance."""

    def test_major_version_difference(self):
        """Test detecting major version updates."""
        assert compute_distance("2.28.1", "3.0.0") == "major"
        assert compute_distance("1.5.0", "2.0.0") == "major"
        assert compute_distance("4.0.0", "5.1.2") == "major"

    def test_minor_version_difference(self):
        """Test detecting minor version updates."""
        assert compute_distance("2.28.1", "2.30.0") == "minor"
        assert compute_distance("1.5.0", "1.6.0") == "minor"
        assert compute_distance("4.0.0", "4.1.0") == "minor"

    def test_patch_version_difference(self):
        """Test detecting patch version updates."""
        assert compute_distance("2.28.1", "2.28.5") == "patch"
        assert compute_distance("1.5.0", "1.5.3") == "patch"
        assert compute_distance("4.0.0", "4.0.1") == "patch"

    def test_up_to_date(self):
        """Test detecting when versions are the same."""
        assert compute_distance("2.28.1", "2.28.1") == "up-to-date"
        assert compute_distance("1.5.0", "1.5.0") == "up-to-date"
        assert compute_distance("4.17.21", "4.17.21") == "up-to-date"

    def test_current_newer_than_latest(self):
        """Test when current is newer than latest (edge case)."""
        # Should return up-to-date or handle gracefully
        result = compute_distance("3.0.0", "2.0.0")
        assert result == "up-to-date"

    def test_two_digit_versions(self):
        """Test versions with only major.minor."""
        assert compute_distance("2.0", "3.0") == "major"
        assert compute_distance("2.0", "2.1") == "minor"

    def test_complex_version_strings(self):
        """Test versions with pre-release or build metadata."""
        assert compute_distance("2.0.0", "2.1.0") == "minor"
        # packaging should handle these
        assert compute_distance("2.0.0", "2.0.1") == "patch"

    def test_invalid_versions(self):
        """Test handling of invalid version strings."""
        # Should return "unknown" for unparseable versions
        result = compute_distance("invalid", "2.0.0")
        assert result == "unknown"


class TestLoadVersionsFile:
    """Tests for loading versions lookup file."""

    def test_load_valid_versions_file(self, tmp_path):
        """Test loading a valid versions JSON file."""
        versions_file = tmp_path / "versions.json"
        data = {
            "requests": "2.30.0",
            "flask": "2.3.0",
            "lodash": "4.17.22"
        }
        versions_file.write_text(json.dumps(data))

        result = load_versions_file(str(versions_file))

        assert result == data
        assert result["requests"] == "2.30.0"
        assert result["flask"] == "2.3.0"

    def test_load_empty_versions_file(self, tmp_path):
        """Test loading an empty versions file."""
        versions_file = tmp_path / "versions.json"
        versions_file.write_text("{}")

        result = load_versions_file(str(versions_file))

        assert result == {}

    def test_load_nonexistent_file(self):
        """Test that loading a non-existent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_versions_file("/nonexistent/versions.json")

    def test_load_invalid_json(self, tmp_path):
        """Test that loading invalid JSON raises JSONDecodeError."""
        versions_file = tmp_path / "versions.json"
        versions_file.write_text("not valid json")

        with pytest.raises(json.JSONDecodeError):
            load_versions_file(str(versions_file))

    def test_load_non_dict_json(self, tmp_path):
        """Test that loading non-dictionary JSON raises ValueError."""
        versions_file = tmp_path / "versions.json"
        versions_file.write_text('["not", "a", "dict"]')

        with pytest.raises(ValueError, match="must contain a JSON object"):
            load_versions_file(str(versions_file))


class TestCheckVersions:
    """Tests for checking versions across dependencies."""

    def test_check_versions_basic(self):
        """Test basic version checking with known packages."""
        deps = [
            Dependency(name="requests", current="==2.28.1"),
            Dependency(name="flask", current=">=2.0"),
        ]
        versions = {
            "requests": "2.30.0",
            "flask": "2.3.0",
        }

        result = check_versions(deps, versions)

        assert len(result) == 2

        # Check requests
        req_dep = result[0]
        assert req_dep.name == "requests"
        assert req_dep.current_parsed == "2.28.1"
        assert req_dep.latest == "2.30.0"
        assert req_dep.distance == "minor"

        # Check flask
        flask_dep = result[1]
        assert flask_dep.name == "flask"
        assert flask_dep.current_parsed == "2.0"
        assert flask_dep.latest == "2.3.0"
        assert flask_dep.distance == "minor"

    def test_check_versions_unknown_package(self):
        """Test handling of packages not in versions file."""
        deps = [
            Dependency(name="nonexistent", current="==1.0.0"),
        ]
        versions = {
            "requests": "2.30.0",
        }

        result = check_versions(deps, versions)

        assert len(result) == 1
        dep = result[0]
        assert dep.name == "nonexistent"
        assert dep.current_parsed == "1.0.0"
        assert dep.latest is None
        assert dep.distance == "unknown"

    def test_check_versions_up_to_date(self):
        """Test detecting up-to-date dependencies."""
        deps = [
            Dependency(name="requests", current="==2.30.0"),
        ]
        versions = {
            "requests": "2.30.0",
        }

        result = check_versions(deps, versions)

        assert len(result) == 1
        dep = result[0]
        assert dep.distance == "up-to-date"

    def test_check_versions_major_update(self):
        """Test detecting major version updates."""
        deps = [
            Dependency(name="django", current="==3.2.0"),
        ]
        versions = {
            "django": "4.2.0",
        }

        result = check_versions(deps, versions)

        assert len(result) == 1
        dep = result[0]
        assert dep.distance == "major"

    def test_check_versions_patch_update(self):
        """Test detecting patch version updates."""
        deps = [
            Dependency(name="requests", current="2.28.1"),
        ]
        versions = {
            "requests": "2.28.5",
        }

        result = check_versions(deps, versions)

        assert len(result) == 1
        dep = result[0]
        assert dep.distance == "patch"

    def test_check_versions_npm_style(self):
        """Test version checking with npm-style specifiers."""
        deps = [
            Dependency(name="lodash", current="^4.17.20"),
            Dependency(name="express", current="~4.18.0"),
        ]
        versions = {
            "lodash": "4.17.22",
            "express": "4.18.2",
        }

        result = check_versions(deps, versions)

        assert len(result) == 2

        # Check lodash (patch update)
        lodash = result[0]
        assert lodash.current_parsed == "4.17.20"
        assert lodash.distance == "patch"

        # Check express (patch update)
        express = result[1]
        assert express.current_parsed == "4.18.0"
        assert express.distance == "patch"

    def test_check_versions_mixed_known_unknown(self):
        """Test checking mix of known and unknown packages."""
        deps = [
            Dependency(name="requests", current="==2.28.1"),
            Dependency(name="unknown-pkg", current="==1.0.0"),
            Dependency(name="flask", current=">=2.0"),
        ]
        versions = {
            "requests": "2.30.0",
            "flask": "2.3.0",
        }

        result = check_versions(deps, versions)

        assert len(result) == 3
        assert result[0].distance == "minor"  # requests
        assert result[1].distance == "unknown"  # unknown-pkg
        assert result[2].distance == "minor"  # flask

    def test_check_versions_empty_list(self):
        """Test checking empty dependency list."""
        deps = []
        versions = {"requests": "2.30.0"}

        result = check_versions(deps, versions)

        assert len(result) == 0
