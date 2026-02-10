"""Tests for the resize command."""

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


@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield Path(tmpdirname)


def test_resize_help():
    """Test that the resize command help works."""
    result = runner.invoke(app, ["resize", "--help"])
    assert result.exit_code == 0
    assert "Resize a video to new dimensions" in result.stdout


def test_resize_with_width_and_height(temp_output_dir):
    """Test resizing with specific width and height."""
    output_file = temp_output_dir / "resized.mp4"

    result = runner.invoke(
        app, ["resize", str(TEST_VIDEO), str(output_file), "--width", "320", "--height", "240"]
    )

    assert result.exit_code == 0
    assert output_file.exists()


def test_resize_with_scale(temp_output_dir):
    """Test resizing with scale factor."""
    output_file = temp_output_dir / "resized.mp4"

    result = runner.invoke(
        app, ["resize", str(TEST_VIDEO), str(output_file), "--scale", "0.5"]
    )

    assert result.exit_code == 0
    assert output_file.exists()


def test_resize_width_only(temp_output_dir):
    """Test resizing with width only (maintain aspect ratio)."""
    output_file = temp_output_dir / "resized.mp4"

    result = runner.invoke(
        app, ["resize", str(TEST_VIDEO), str(output_file), "--width", "320"]
    )

    assert result.exit_code == 0
    assert output_file.exists()


def test_resize_height_only(temp_output_dir):
    """Test resizing with height only (maintain aspect ratio)."""
    output_file = temp_output_dir / "resized.mp4"

    result = runner.invoke(
        app, ["resize", str(TEST_VIDEO), str(output_file), "--height", "240"]
    )

    assert result.exit_code == 0
    assert output_file.exists()


def test_resize_force_aspect(temp_output_dir):
    """Test resizing with forced aspect ratio."""
    output_file = temp_output_dir / "resized.mp4"

    result = runner.invoke(
        app, ["resize", str(TEST_VIDEO), str(output_file), "--width", "100", "--height", "300", "--force-aspect"]
    )

    assert result.exit_code == 0
    assert output_file.exists()
    assert "may distort" in result.stdout


def test_resize_no_parameters():
    """Test that resize fails without any size parameters."""
    result = runner.invoke(
        app, ["resize", str(TEST_VIDEO), "output.mp4"]
    )

    assert result.exit_code != 0
    assert "Must specify at least one" in result.stdout


def test_resize_conflicting_parameters():
    """Test that scale conflicts with width/height."""
    result = runner.invoke(
        app, ["resize", str(TEST_VIDEO), "output.mp4", "--scale", "0.5", "--width", "320"]
    )

    assert result.exit_code != 0


def test_resize_invalid_scale():
    """Test invalid scale values."""
    # Test negative scale
    result = runner.invoke(
        app, ["resize", str(TEST_VIDEO), "output.mp4", "--scale", "-1"]
    )
    assert result.exit_code != 0

    # Test zero scale  
    result = runner.invoke(
        app, ["resize", str(TEST_VIDEO), "output.mp4", "--scale", "0"]
    )
    assert result.exit_code != 0


def test_resize_overwrite_protection(temp_output_dir):
    """Test that existing files are protected unless --overwrite is used."""
    output_file = temp_output_dir / "existing.mp4"
    output_file.write_text("existing file")

    # Should fail without --overwrite
    result = runner.invoke(
        app, ["resize", str(TEST_VIDEO), str(output_file), "--width", "320"],
        input="n\n"  # Answer "no" to overwrite prompt
    )

    assert result.exit_code == 0
    assert "Aborted" in result.stdout
