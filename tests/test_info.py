"""Tests for the info command."""

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from vidio_cli.cli import app
from vidio_cli.ffmpeg_utils import check_ffmpeg

# Skip all tests if ffmpeg is not available
pytestmark = pytest.mark.skipif(not check_ffmpeg(), reason="ffmpeg is not available")

runner = CliRunner()

# Replace this with actual test video path
ASSET_DIR = Path(__file__).parent / "assets"
TEST_VIDEO = ASSET_DIR / "sample.mp4"


def test_info_help():
    """Test that the info command help works."""
    result = runner.invoke(app, ["info", "--help"])
    assert result.exit_code == 0
    assert "Display detailed information about a video file" in result.stdout


def test_info_basic():
    """Test the info command with basic output."""
    result = runner.invoke(app, ["info", str(TEST_VIDEO)])

    # Check that it succeeded
    assert result.exit_code == 0
    assert "Video Information:" in result.stdout
    assert "Duration" in result.stdout
    assert "Resolution" in result.stdout


def test_info_json():
    """Test the info command with JSON output."""
    result = runner.invoke(app, ["info", str(TEST_VIDEO), "--json"])

    # Check that it succeeded
    assert result.exit_code == 0

    # Should be valid JSON
    try:
        data = json.loads(result.stdout)
        assert "format" in data
        assert "streams" in data
    except json.JSONDecodeError:
        pytest.fail("Output is not valid JSON")  # ty: ignore
