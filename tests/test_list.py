"""Tests for the list command."""

import json
import tempfile
from pathlib import Path

import pytest
from typer.testing import CliRunner

from vidio_cli.cli import app
from vidio_cli.ffmpeg_utils import check_ffmpeg

# Integration tests require ffmpeg and real media assets.
pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(not check_ffmpeg(), reason="ffmpeg is not available"),
]

runner = CliRunner()

# Test video path
ASSET_DIR = Path(__file__).parent / "assets"
TEST_VIDEO = ASSET_DIR / "sample.mp4"


def test_list_help():
    """Test that the list command help works."""
    result = runner.invoke(app, ["list", "--help"])
    assert result.exit_code == 0
    assert "List all video files" in result.stdout


def test_list_empty_directory():
    """Test listing videos in an empty directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        result = runner.invoke(app, ["list", tmpdir])
        assert result.exit_code == 0
        assert "No video files found" in result.stdout


def test_list_with_videos():
    """Test listing videos in directory with video files."""
    result = runner.invoke(app, ["list", str(ASSET_DIR)])
    assert result.exit_code == 0
    assert "sample.mp4" in result.stdout
    assert "Found 1 video file(s)" in result.stdout


def test_ls_alias():
    """Test that ls alias works the same as list."""
    result = runner.invoke(app, ["ls", str(ASSET_DIR)])
    assert result.exit_code == 0
    assert "sample.mp4" in result.stdout
    assert "Found 1 video file(s)" in result.stdout


def test_list_detailed():
    """Test listing videos with detailed information using -l flag."""
    result = runner.invoke(app, ["list", str(ASSET_DIR), "-l"])
    assert result.exit_code == 0
    assert "sample.mp4" in result.stdout
    # In ls-style format, these appear as data, not headers
    assert "00:00:" in result.stdout  # Duration format
    assert "640x360" in result.stdout  # Resolution
    assert "h264" in result.stdout  # Codec


def test_list_detailed_long_form():
    """Test listing videos with detailed information using --list flag."""
    result = runner.invoke(app, ["list", str(ASSET_DIR), "--list"])
    assert result.exit_code == 0
    assert "sample.mp4" in result.stdout
    # In ls-style format, these appear as data, not headers
    assert "00:00:" in result.stdout  # Duration format
    assert "640x360" in result.stdout  # Resolution
    assert "h264" in result.stdout  # Codec


def test_list_table_format():
    """Test table format output."""
    result = runner.invoke(app, ["list", str(ASSET_DIR), "--table", "-l"])
    assert result.exit_code == 0
    assert "sample.mp4" in result.stdout
    # In table format, these appear as headers
    assert "Duration" in result.stdout
    assert "Resolution" in result.stdout
    assert "Codec" in result.stdout


def test_list_json_output():
    """Test JSON output format."""
    result = runner.invoke(app, ["list", str(ASSET_DIR), "--json"])
    assert result.exit_code == 0
    
    # Parse JSON output
    output_data = json.loads(result.stdout)
    assert isinstance(output_data, list)
    assert len(output_data) == 1
    
    video_info = output_data[0]
    assert video_info["name"] == "sample.mp4"
    assert "size_bytes" in video_info
    assert "duration_seconds" in video_info
    assert "resolution" in video_info


def test_list_current_directory():
    """Test listing videos in current directory (no argument)."""
    result = runner.invoke(app, ["list"])
    assert result.exit_code == 0
    # Should work even if no videos found
    assert "video file" in result.stdout.lower()
