"""Tests for the grid command."""

import tempfile
from pathlib import Path

import pytest
from typer.testing import CliRunner

from vidio_cli.cli import app
from vidio_cli.ffmpeg_utils import check_ffmpeg
from vidio_cli.commands.grid import calculate_grid_size

# Integration tests require ffmpeg and real media assets.
pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(not check_ffmpeg(), reason="ffmpeg is not available"),
]

runner = CliRunner()

# Replace this with actual test video paths
ASSET_DIR = Path(__file__).parent / "assets"
TEST_VIDEO = ASSET_DIR / "sample.mp4"


@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield Path(tmpdirname)


def test_grid_help():
    """Test that the grid command help works."""
    result = runner.invoke(app, ["grid", "--help"])
    assert result.exit_code == 0
    assert "Arrange multiple videos in a grid layout" in result.stdout


def test_calculate_grid_size():
    """Test the grid size calculation function."""
    # Test with both rows and columns specified
    assert calculate_grid_size(4, 2, 2) == (2, 2)

    # Test with only rows specified
    assert calculate_grid_size(5, 2) == (2, 3)

    # Test with only columns specified
    assert calculate_grid_size(5, None, 2) == (3, 2)

    # Test with neither specified (should be as square as possible)
    assert calculate_grid_size(4) == (2, 2)
    assert calculate_grid_size(5) == (2, 3)
    assert calculate_grid_size(9) == (3, 3)

    # Test with invalid grid size
    with pytest.raises(ValueError):
        calculate_grid_size(5, 1, 2)  # 1x2 grid can't fit 5 videos


def test_grid_basic(temp_output_dir):
    """Test the grid command with basic options."""
    output_file = temp_output_dir / "output.mp4"

    # Run the command with 4 videos in a 2x2 grid
    result = runner.invoke(
        app,
        [
            "grid",
            str(TEST_VIDEO),
            str(TEST_VIDEO),
            str(TEST_VIDEO),
            str(TEST_VIDEO),
            str(output_file),
            "--rows",
            "2",
        ],
    )

    # Check that it succeeded
    assert result.exit_code == 0
    assert output_file.exists()


def test_grid_with_padding(temp_output_dir):
    """Test the grid command with padding."""
    output_file = temp_output_dir / "output.mp4"

    # Run the command with 4 videos in a 2x2 grid with padding
    result = runner.invoke(
        app,
        [
            "grid",
            str(TEST_VIDEO),
            str(TEST_VIDEO),
            str(TEST_VIDEO),
            str(TEST_VIDEO),
            str(output_file),
            "--padding",
            "10",
            "--background",
            "white",
        ],
    )

    # Check that it succeeded
    assert result.exit_code == 0
    assert output_file.exists()
