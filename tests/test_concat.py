"""Tests for the concat command."""

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
TEST_VIDEO1 = ASSET_DIR / "sample.mp4"


@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield Path(tmpdirname)


def test_concat_help():
    """Test that the concat command help works."""
    result = runner.invoke(app, ["concat", "--help"])
    assert result.exit_code == 0
    assert "Concatenate multiple videos" in result.stdout


def test_concat_horizontal(temp_output_dir):
    """Test the concat command with horizontal layout."""
    output_file = temp_output_dir / "output.mp4"

    # Run the command
    result = runner.invoke(
        app, ["concat", str(TEST_VIDEO1), str(TEST_VIDEO1), str(output_file)]
    )

    # Check that it succeeded
    assert result.exit_code == 0
    assert output_file.exists()
    assert "Concatenation completed" in result.stdout


def test_concat_vertical(temp_output_dir):
    """Test the concat command with vertical layout."""
    output_file = temp_output_dir / "output.mp4"

    # Run the command
    result = runner.invoke(
        app,
        ["concat", str(TEST_VIDEO1), str(TEST_VIDEO1), str(output_file), "--vertical"],
    )

    # Check that it succeeded
    assert result.exit_code == 0
    assert output_file.exists()
    assert "Concatenation completed" in result.stdout
