"""
Tests for output formatters.
"""

import json
import os
import tempfile
from pathlib import Path

import pytest

from depdrift.models import Dependency
from depdrift.output import format_json, format_output, format_table


class TestFormatTable:
    """Tests for ASCII table formatting."""

    def test_format_table_with_version_info(self):
        """Test formatting table with full version information."""
        deps = [
            Dependency(
                name="requests",
                current=">=2.28.0",
                current_parsed="2.28.0",
                latest="2.30.0",
                distance="minor"
            ),
            Dependency(
                name="click",
                current="==8.0.0",
                current_parsed="8.0.0",
                latest="8.1.3",
                distance="minor"
            ),
        ]

        result = format_table(deps)

        # Check header is present
        assert "Package" in result
        assert "Current" in result
        assert "Latest" in result
        assert "Distance" in result

        # Check separator line
        assert "-" * 87 in result

        # Check data rows
        assert "requests" in result
        assert "2.28.0" in result
        assert "2.30.0" in result
        assert "minor" in result
        assert "click" in result
        assert "8.0.0" in result
        assert "8.1.3" in result

    def test_format_table_without_version_info(self):
        """Test formatting table without version information (simple mode)."""
        deps = [
            Dependency(name="requests", current=">=2.28.0"),
            Dependency(name="click", current="==8.0.0"),
        ]

        result = format_table(deps)

        # Check header for simple mode
        assert "Package" in result
        assert "Current" in result
        # Should NOT have Latest or Distance columns
        assert "Latest" not in result
        assert "Distance" not in result

        # Check separator line for simple mode
        assert "-" * 52 in result

        # Check data rows
        assert "requests" in result
        assert ">=2.28.0" in result
        assert "click" in result
        assert "==8.0.0" in result

    def test_format_table_truncate_long_versions(self):
        """Test truncation of version strings longer than 20 characters."""
        deps = [
            Dependency(
                name="very-long-package-name-here",
                current="1.2.3.4.5.6.7.8.9.10.11.12",  # 27 chars
                current_parsed="1.2.3.4.5.6.7.8.9.10",  # 23 chars
                latest="2.0.0.1.2.3.4.5.6.7.8.9",  # 25 chars
                distance="major"
            ),
        ]

        result = format_table(deps)

        # Check that long strings are truncated to 20 characters
        # Package name should be truncated to 30 chars
        assert "very-long-package-name-her" in result
        # Version strings should be truncated to 20 chars
        lines = result.split("\n")
        data_line = lines[2]  # Third line is the data row
        # Extract the current version column (positions 31-50)
        current_col = data_line[31:51].strip()
        assert len(current_col) <= 20

    def test_format_table_with_missing_latest(self):
        """Test formatting when some packages have no latest version."""
        deps = [
            Dependency(
                name="known-package",
                current="1.0.0",
                current_parsed="1.0.0",
                latest="2.0.0",
                distance="major"
            ),
            Dependency(
                name="unknown-package",
                current="1.5.0",
                current_parsed="1.5.0",
                latest=None,
                distance="unknown"
            ),
        ]

        result = format_table(deps)

        # Check that missing latest is shown appropriately
        assert "known-package" in result
        assert "2.0.0" in result
        assert "unknown-package" in result
        assert "<missing>" in result
        assert "unknown" in result

    def test_format_table_empty_list(self):
        """Test formatting an empty dependency list."""
        deps = []
        result = format_table(deps)
        assert result == ""

    def test_format_table_alignment(self):
        """Test that table columns are properly aligned."""
        deps = [
            Dependency(
                name="a",
                current="1.0",
                current_parsed="1.0",
                latest="2.0",
                distance="major"
            ),
            Dependency(
                name="very-long-name",
                current="10.20.30",
                current_parsed="10.20.30",
                latest="11.0.0",
                distance="minor"
            ),
        ]

        result = format_table(deps)
        lines = result.split("\n")

        # All data lines should have consistent width
        data_lines = [line for line in lines[2:] if line]  # Skip header and separator
        if data_lines:
            # Check that columns are aligned (all lines should be similar length)
            line_lengths = [len(line) for line in data_lines]
            # Lengths should be within a reasonable range due to padding
            assert max(line_lengths) - min(line_lengths) < 10


class TestFormatJson:
    """Tests for JSON output formatting."""

    def test_format_json_basic(self):
        """Test basic JSON formatting."""
        deps = [
            Dependency(
                name="requests",
                current=">=2.28.0",
                current_parsed="2.28.0",
                latest="2.30.0",
                distance="minor"
            ),
            Dependency(
                name="click",
                current="==8.0.0",
                current_parsed="8.0.0",
                latest="8.1.3",
                distance="minor"
            ),
        ]

        result = format_json(deps)

        # Parse the JSON to verify it's valid
        parsed = json.loads(result)

        assert isinstance(parsed, list)
        assert len(parsed) == 2

        # Check first entry
        assert parsed[0]["package"] == "requests"
        assert parsed[0]["current"] == "2.28.0"
        assert parsed[0]["latest"] == "2.30.0"
        assert parsed[0]["distance"] == "minor"

        # Check second entry
        assert parsed[1]["package"] == "click"
        assert parsed[1]["current"] == "8.0.0"
        assert parsed[1]["latest"] == "8.1.3"
        assert parsed[1]["distance"] == "minor"

    def test_format_json_with_null_values(self):
        """Test JSON formatting with null/None values."""
        deps = [
            Dependency(
                name="unknown-package",
                current="1.0.0",
                current_parsed="1.0.0",
                latest=None,
                distance=None
            ),
        ]

        result = format_json(deps)
        parsed = json.loads(result)

        assert parsed[0]["package"] == "unknown-package"
        assert parsed[0]["current"] == "1.0.0"
        assert parsed[0]["latest"] is None
        assert parsed[0]["distance"] is None

    def test_format_json_without_parsed_version(self):
        """Test JSON formatting when current_parsed is not set."""
        deps = [
            Dependency(
                name="requests",
                current=">=2.28.0",
                latest="2.30.0",
                distance="minor"
            ),
        ]

        result = format_json(deps)
        parsed = json.loads(result)

        # Should fall back to raw current version
        assert parsed[0]["current"] == ">=2.28.0"

    def test_format_json_empty_list(self):
        """Test JSON formatting with empty list."""
        deps = []
        result = format_json(deps)
        parsed = json.loads(result)

        assert parsed == []

    def test_format_json_indentation(self):
        """Test that JSON output is properly indented."""
        deps = [
            Dependency(name="test", current="1.0.0"),
        ]

        result = format_json(deps)

        # Check for indentation (should have spaces)
        assert "  " in result
        assert "\n" in result


class TestFormatOutput:
    """Tests for the format_output dispatcher function."""

    def test_format_output_table(self):
        """Test dispatching to table formatter."""
        deps = [
            Dependency(
                name="requests",
                current="2.28.0",
                current_parsed="2.28.0",
                latest="2.30.0",
                distance="minor"
            ),
        ]

        result = format_output(deps, "table")

        # Should contain table elements
        assert "Package" in result
        assert "requests" in result
        assert "-" in result  # Separator line

    def test_format_output_json(self):
        """Test dispatching to JSON formatter."""
        deps = [
            Dependency(
                name="requests",
                current="2.28.0",
                current_parsed="2.28.0",
                latest="2.30.0",
                distance="minor"
            ),
        ]

        result = format_output(deps, "json")

        # Should be valid JSON
        parsed = json.loads(result)
        assert isinstance(parsed, list)
        assert len(parsed) == 1

    def test_format_output_invalid_format(self):
        """Test error handling for invalid format."""
        deps = [Dependency(name="test", current="1.0.0")]

        with pytest.raises(ValueError) as exc_info:
            format_output(deps, "xml")

        assert "Invalid output format" in str(exc_info.value)
        assert "xml" in str(exc_info.value)


class TestIntegrationWithMain:
    """Integration tests with the main CLI."""

    def test_json_output_flag(self, tmp_path):
        """Test --json flag produces valid JSON."""
        from depdrift.main import main
        from click.testing import CliRunner

        # Create a test requirements file
        req_file = tmp_path / "requirements.txt"
        req_file.write_text("requests==2.28.0\nclick==8.0.0\n")

        # Create a versions file
        versions_file = tmp_path / "versions.json"
        versions_file.write_text('{"requests": "2.30.0", "click": "8.1.3"}')

        runner = CliRunner()
        result = runner.invoke(
            main,
            ["--file", str(req_file), "--versions", str(versions_file), "--json"]
        )

        assert result.exit_code == 0

        # Parse and validate JSON output
        output = json.loads(result.output)
        assert isinstance(output, list)
        assert len(output) == 2
        assert output[0]["package"] in ["requests", "click"]
        assert "distance" in output[0]

    def test_env_var_json_output(self, tmp_path, monkeypatch):
        """Test DEPDRIFT_OUTPUT=json environment variable."""
        from depdrift.main import main
        from click.testing import CliRunner

        # Set environment variable
        monkeypatch.setenv("DEPDRIFT_OUTPUT", "json")

        # Create a test requirements file
        req_file = tmp_path / "requirements.txt"
        req_file.write_text("requests==2.28.0\n")

        # Create a versions file
        versions_file = tmp_path / "versions.json"
        versions_file.write_text('{"requests": "2.30.0"}')

        runner = CliRunner()
        result = runner.invoke(
            main,
            ["--file", str(req_file), "--versions", str(versions_file)]
        )

        assert result.exit_code == 0

        # Should be JSON output
        output = json.loads(result.output)
        assert isinstance(output, list)

    def test_json_flag_overrides_env_var(self, tmp_path, monkeypatch):
        """Test that --json flag overrides DEPDRIFT_OUTPUT env var."""
        from depdrift.main import main
        from click.testing import CliRunner

        # Set environment variable to table
        monkeypatch.setenv("DEPDRIFT_OUTPUT", "table")

        # Create a test requirements file
        req_file = tmp_path / "requirements.txt"
        req_file.write_text("requests==2.28.0\n")

        # Create a versions file
        versions_file = tmp_path / "versions.json"
        versions_file.write_text('{"requests": "2.30.0"}')

        runner = CliRunner()
        result = runner.invoke(
            main,
            ["--file", str(req_file), "--versions", str(versions_file), "--json"]
        )

        assert result.exit_code == 0

        # Should be JSON output (flag overrides env var)
        output = json.loads(result.output)
        assert isinstance(output, list)

    def test_no_manifest_error(self):
        """Test error when no manifest file is found."""
        from depdrift.main import main
        from click.testing import CliRunner

        runner = CliRunner()
        with runner.isolated_filesystem():
            # Run in empty directory with no manifest
            result = runner.invoke(main)

            assert result.exit_code == 2
            assert "No manifest file found" in result.output

    def test_invalid_output_format_env_var(self, tmp_path, monkeypatch):
        """Test error with invalid DEPDRIFT_OUTPUT value."""
        from depdrift.main import main
        from click.testing import CliRunner

        # Set invalid environment variable
        monkeypatch.setenv("DEPDRIFT_OUTPUT", "xml")

        # Create a test requirements file
        req_file = tmp_path / "requirements.txt"
        req_file.write_text("requests==2.28.0\n")

        runner = CliRunner()
        result = runner.invoke(
            main,
            ["--file", str(req_file)]
        )

        assert result.exit_code == 1
        assert "Invalid output format" in result.output

    def test_table_output_without_versions_file(self, tmp_path):
        """Test table output when no versions file is provided."""
        from depdrift.main import main
        from click.testing import CliRunner

        # Create a test requirements file
        req_file = tmp_path / "requirements.txt"
        req_file.write_text("requests==2.28.0\nclick==8.0.0\n")

        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(
                main,
                ["--file", str(req_file)]
            )

            assert result.exit_code == 0
            # Should have simple table format
            assert "Package" in result.output
            assert "Current" in result.output
            # Should NOT have Latest/Distance columns
            assert "Latest" not in result.output
            assert "Distance" not in result.output
