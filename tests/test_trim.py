"""Tests for the trim command."""

import tempfile
from pathlib import Path

import pytest
from typer.testing import CliRunner

from vidio_cli.cli import app
from vidio_cli.ffmpeg_utils import check_ffmpeg

# Skip all tests if ffmpeg is not available
pytestmark = pytest.mark.skipif(not check_ffmpeg(), reason="ffmpeg is not available")

runner = CliRunner()

# Replace this with actual test video paths
ASSET_DIR = Path(__file__).parent / "assets"
TEST_VIDEO = ASSET_DIR / "sample.mp4"


@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield Path(tmpdirname)


def test_trim_help():
    """Test that the trim command help works."""
    result = runner.invoke(app, ["trim", "--help"])
    assert result.exit_code == 0
    assert "Trim a video by specifying start and end times" in result.stdout


def test_trim_with_start_and_end(temp_output_dir):
    """Test trimming with start and end times."""
    output_file = temp_output_dir / "trimmed.mp4"

    result = runner.invoke(
        app, ["trim", str(TEST_VIDEO), str(output_file), "--start", "1", "--end", "3"]
    )

    assert result.exit_code == 0
    assert output_file.exists()


def test_trim_with_duration(temp_output_dir):
    """Test trimming with start time and duration."""
    output_file = temp_output_dir / "trimmed.mp4"

    result = runner.invoke(
        app, ["trim", str(TEST_VIDEO), str(output_file), "--start", "1", "--duration", "2"]
    )

    assert result.exit_code == 0
    assert output_file.exists()


def test_trim_from_beginning(temp_output_dir):
    """Test trimming from beginning to specified end time."""
    output_file = temp_output_dir / "trimmed.mp4"

    result = runner.invoke(
        app, ["trim", str(TEST_VIDEO), str(output_file), "--end", "5"]
    )

    assert result.exit_code == 0
    assert output_file.exists()


def test_trim_time_formats(temp_output_dir):
    """Test different time formats."""
    output_file = temp_output_dir / "trimmed.mp4"

    # Test MM:SS format
    result = runner.invoke(
        app, ["trim", str(TEST_VIDEO), str(output_file), "--start", "0:01", "--end", "0:03"]
    )

    assert result.exit_code == 0
    assert output_file.exists()


def test_trim_conflicting_options():
    """Test that specifying both --end and --duration fails."""
    result = runner.invoke(
        app, ["trim", str(TEST_VIDEO), "output.mp4", "--end", "10", "--duration", "5"]
    )

    assert result.exit_code == 1
    assert "Cannot specify both --end and --duration" in result.stdout


def test_trim_overwrite_protection(temp_output_dir):
    """Test that existing files are protected unless --overwrite is used."""
    output_file = temp_output_dir / "existing.mp4"
    output_file.write_text("existing file")

    # Should fail without --overwrite
    result = runner.invoke(
        app, ["trim", str(TEST_VIDEO), str(output_file), "--start", "1", "--end", "3"],
        input="n\n"  # Answer "no" to overwrite prompt
    )

    assert result.exit_code == 0
    assert "Aborted" in result.stdout