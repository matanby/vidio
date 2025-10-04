"""Tests for the to-gif command."""

import tempfile
from pathlib import Path

import pytest
from typer.testing import CliRunner

from vidio_cli.cli import app
from vidio_cli.ffmpeg_utils import check_ffmpeg

# Skip all tests if ffmpeg is not available
pytestmark = pytest.mark.skipif(not check_ffmpeg(), reason="ffmpeg is not available")

runner = CliRunner()

# Test video path
ASSET_DIR = Path(__file__).parent / "assets"
TEST_VIDEO = ASSET_DIR / "sample.mp4"


@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield Path(tmpdirname)


def test_to_gif_help():
    """Test that the to-gif command help works."""
    result = runner.invoke(app, ["to-gif", "--help"])
    assert result.exit_code == 0
    assert "Convert a video to high-quality GIF" in result.stdout


def test_to_gif_basic(temp_output_dir):
    """Test basic GIF conversion."""
    output_file = temp_output_dir / "output.gif"

    result = runner.invoke(
        app, ["to-gif", str(TEST_VIDEO), str(output_file)]
    )

    assert result.exit_code == 0
    assert output_file.exists()
    assert "GIF created" in result.stdout


def test_to_gif_with_fps(temp_output_dir):
    """Test GIF conversion with custom FPS."""
    output_file = temp_output_dir / "output.gif"

    result = runner.invoke(
        app, ["to-gif", str(TEST_VIDEO), str(output_file), "--fps", "5"]
    )

    assert result.exit_code == 0
    assert output_file.exists()


def test_to_gif_with_scale(temp_output_dir):
    """Test GIF conversion with scaling."""
    output_file = temp_output_dir / "output.gif"

    result = runner.invoke(
        app, ["to-gif", str(TEST_VIDEO), str(output_file), "--scale", "0.5"]
    )

    assert result.exit_code == 0
    assert output_file.exists()


def test_to_gif_with_width(temp_output_dir):
    """Test GIF conversion with custom width."""
    output_file = temp_output_dir / "output.gif"

    result = runner.invoke(
        app, ["to-gif", str(TEST_VIDEO), str(output_file), "--width", "320"]
    )

    assert result.exit_code == 0
    assert output_file.exists()


def test_to_gif_with_time_range(temp_output_dir):
    """Test GIF conversion with time range."""
    output_file = temp_output_dir / "output.gif"

    result = runner.invoke(
        app, ["to-gif", str(TEST_VIDEO), str(output_file), "--start", "1", "--duration", "3"]
    )

    assert result.exit_code == 0
    assert output_file.exists()


def test_to_gif_quality_levels(temp_output_dir):
    """Test different quality levels."""
    for quality in ["low", "medium", "high"]:
        output_file = temp_output_dir / f"output_{quality}.gif"
        
        result = runner.invoke(
            app, ["to-gif", str(TEST_VIDEO), str(output_file), "--quality", quality, "--duration", "2"]
        )
        
        assert result.exit_code == 0
        assert output_file.exists()


def test_to_gif_quality_numeric(temp_output_dir):
    """Test numeric quality levels."""
    output_file = temp_output_dir / "output.gif"

    result = runner.invoke(
        app, ["to-gif", str(TEST_VIDEO), str(output_file), "--quality", "8", "--duration", "2"]
    )

    assert result.exit_code == 0
    assert output_file.exists()


def test_to_gif_no_optimize(temp_output_dir):
    """Test GIF conversion without palette optimization."""
    output_file = temp_output_dir / "output.gif"

    result = runner.invoke(
        app, ["to-gif", str(TEST_VIDEO), str(output_file), "--no-optimize", "--duration", "2"]
    )

    assert result.exit_code == 0
    assert output_file.exists()
    assert "Skipping palette optimization" in result.stdout


def test_to_gif_dithering_options(temp_output_dir):
    """Test different dithering algorithms."""
    for dither in ["none", "bayer", "floyd_steinberg"]:
        output_file = temp_output_dir / f"output_{dither}.gif"
        
        result = runner.invoke(
            app, ["to-gif", str(TEST_VIDEO), str(output_file), "--dither", dither, "--duration", "2"]
        )
        
        assert result.exit_code == 0
        assert output_file.exists()


def test_to_gif_conflicting_time_options():
    """Test that specifying both --end and --duration fails."""
    result = runner.invoke(
        app, ["to-gif", str(TEST_VIDEO), "output.gif", "--end", "10", "--duration", "5"]
    )

    assert result.exit_code == 1
    assert "Cannot specify both --end and --duration" in result.stdout


def test_to_gif_conflicting_size_options():
    """Test that specifying both --scale and --width fails."""
    result = runner.invoke(
        app, ["to-gif", str(TEST_VIDEO), "output.gif", "--scale", "0.5", "--width", "320"]
    )

    assert result.exit_code == 1
    assert "Cannot specify both --scale and --width" in result.stdout


def test_to_gif_invalid_quality():
    """Test invalid quality values."""
    result = runner.invoke(
        app, ["to-gif", str(TEST_VIDEO), "output.gif", "--quality", "invalid"]
    )
    
    assert result.exit_code != 0


def test_to_gif_overwrite_protection(temp_output_dir):
    """Test that existing files are protected unless --overwrite is used."""
    output_file = temp_output_dir / "existing.gif"
    output_file.write_text("existing file")

    # Should fail without --overwrite
    result = runner.invoke(
        app, ["to-gif", str(TEST_VIDEO), str(output_file), "--duration", "1"],
        input="n\n"  # Answer "no" to overwrite prompt
    )

    assert result.exit_code == 0
    assert "Aborted" in result.stdout