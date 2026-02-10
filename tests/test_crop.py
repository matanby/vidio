"""Tests for the crop command."""

import tempfile
from pathlib import Path

import pytest
from typer.testing import CliRunner

from vidio_cli.cli import app
from vidio_cli.ffmpeg_utils import check_ffmpeg

runner = CliRunner()

# Integration tests require ffmpeg and real media assets.
pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(not check_ffmpeg(), reason="ffmpeg is not available"),
]


@pytest.fixture
def sample_video():
    """Return the path to the sample video."""
    return Path(__file__).parent / "assets" / "sample.mp4"


@pytest.fixture
def temp_output():
    """Create a temporary output file path (file doesn't exist yet)."""
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=True) as f:
        output_path = Path(f.name)
    # File is deleted after context manager, so we just have the path
    yield output_path
    # Cleanup
    if output_path.exists():
        output_path.unlink()


def test_crop_help(clean_output):
    """Test that the crop command shows help."""
    result = runner.invoke(app, ["crop", "--help"])
    help_text = clean_output(result.stdout)
    assert result.exit_code == 0
    assert "Crop a video to a specific region" in help_text
    # Typer/Click help rendering differs by runtime; accept short or long flags.
    assert "--width" in help_text or "-w" in help_text
    assert "--height" in help_text or "-h" in help_text
    assert "--preset" in help_text


def test_crop_no_args():
    """Test that crop requires arguments."""
    result = runner.invoke(app, ["crop"])
    # With no_args_is_help=True, it shows help and exits with 0
    assert result.exit_code == 0
    assert "Crop a video" in result.stdout


def test_crop_missing_dimensions(sample_video, temp_output):
    """Test that crop requires width and height or preset."""
    result = runner.invoke(
        app,
        ["crop", str(sample_video), str(temp_output)],
    )
    assert result.exit_code != 0
    assert "Must specify --width and --height, or use --preset" in result.stdout


def test_crop_with_preset_center_square(sample_video, temp_output):
    """Test cropping with center-square preset."""
    result = runner.invoke(
        app,
        ["crop", str(sample_video), str(temp_output), "--preset", "center-square"],
    )
    assert result.exit_code == 0
    assert temp_output.exists()
    assert "Using preset: center-square" in result.stdout
    assert "Cropped video saved" in result.stdout


def test_crop_with_preset_16_9(sample_video, temp_output):
    """Test cropping with 16:9 preset."""
    result = runner.invoke(
        app,
        ["crop", str(sample_video), str(temp_output), "--preset", "16:9"],
    )
    assert result.exit_code == 0
    assert temp_output.exists()
    assert "Using preset: 16:9" in result.stdout


def test_crop_with_preset_9_16(sample_video, temp_output):
    """Test cropping with 9:16 preset."""
    result = runner.invoke(
        app,
        ["crop", str(sample_video), str(temp_output), "--preset", "9:16"],
    )
    assert result.exit_code == 0
    assert temp_output.exists()
    assert "Using preset: 9:16" in result.stdout


def test_crop_with_preset_4_3(sample_video, temp_output):
    """Test cropping with 4:3 preset."""
    result = runner.invoke(
        app,
        ["crop", str(sample_video), str(temp_output), "--preset", "4:3"],
    )
    assert result.exit_code == 0
    assert temp_output.exists()
    assert "Using preset: 4:3" in result.stdout


def test_crop_with_preset_1_1(sample_video, temp_output):
    """Test cropping with 1:1 preset."""
    result = runner.invoke(
        app,
        ["crop", str(sample_video), str(temp_output), "--preset", "1:1"],
    )
    assert result.exit_code == 0
    assert temp_output.exists()
    assert "Using preset: 1:1" in result.stdout


def test_crop_with_invalid_preset(sample_video, temp_output):
    """Test cropping with invalid preset."""
    result = runner.invoke(
        app,
        ["crop", str(sample_video), str(temp_output), "--preset", "invalid"],
    )
    assert result.exit_code != 0
    assert "Unknown preset" in result.stdout


def test_crop_with_manual_dimensions(sample_video, temp_output):
    """Test cropping with manual width and height."""
    # Sample video is 640x360, so use dimensions that fit
    result = runner.invoke(
        app,
        [
            "crop",
            str(sample_video),
            str(temp_output),
            "--width",
            "320",
            "--height",
            "240",
        ],
    )
    assert result.exit_code == 0
    assert temp_output.exists()
    assert "Cropping to 320x240" in result.stdout


def test_crop_with_manual_dimensions_and_offsets(sample_video, temp_output):
    """Test cropping with manual dimensions and offsets."""
    # Sample video is 640x360, so use dimensions that fit with offsets
    result = runner.invoke(
        app,
        [
            "crop",
            str(sample_video),
            str(temp_output),
            "--width",
            "400",
            "--height",
            "200",
            "--x",
            "100",
            "--y",
            "50",
        ],
    )
    assert result.exit_code == 0
    assert temp_output.exists()
    assert "Cropping to 400x200 at position (100, 50)" in result.stdout


def test_crop_with_dimensions_exceeding_video(sample_video, temp_output):
    """Test that crop fails when dimensions exceed video size."""
    # Sample video is 640x360, try to crop larger dimensions
    result = runner.invoke(
        app,
        [
            "crop",
            str(sample_video),
            str(temp_output),
            "--width",
            "800",
            "--height",
            "600",
            "--x",
            "0",
            "--y",
            "0",
        ],
    )
    assert result.exit_code != 0
    assert "exceeds video" in result.stdout


def test_crop_with_negative_offset(sample_video, temp_output):
    """Test that crop fails with negative offsets."""
    result = runner.invoke(
        app,
        [
            "crop",
            str(sample_video),
            str(temp_output),
            "--width",
            "640",
            "--height",
            "480",
            "--x",
            "-10",
        ],
    )
    assert result.exit_code != 0


def test_crop_overwrite_existing_file(sample_video, temp_output):
    """Test that crop can overwrite existing files."""
    # Create the output file first
    temp_output.touch()

    result = runner.invoke(
        app,
        [
            "crop",
            str(sample_video),
            str(temp_output),
            "--preset",
            "center-square",
            "--overwrite",
        ],
    )
    assert result.exit_code == 0
    assert temp_output.exists()


def test_crop_without_overwrite_existing_file(sample_video, temp_output):
    """Test that crop prompts when file exists without overwrite flag."""
    # Create the output file first
    temp_output.touch()

    # Simulate user saying "no" to overwrite
    result = runner.invoke(
        app,
        [
            "crop",
            str(sample_video),
            str(temp_output),
            "--preset",
            "center-square",
        ],
        input="n\n",
    )
    assert result.exit_code == 0
    assert "Aborted" in result.stdout


def test_crop_nonexistent_input_file(temp_output):
    """Test that crop fails with nonexistent input file."""
    result = runner.invoke(
        app,
        [
            "crop",
            "nonexistent.mp4",
            str(temp_output),
            "--preset",
            "center-square",
        ],
    )
    assert result.exit_code != 0


def test_crop_verbose_mode(sample_video, temp_output):
    """Test crop with verbose flag."""
    result = runner.invoke(
        app,
        [
            "--verbose",
            "crop",
            str(sample_video),
            str(temp_output),
            "--preset",
            "center-square",
        ],
    )
    assert result.exit_code == 0
    assert temp_output.exists()


def test_crop_preset_overrides_manual_params(sample_video, temp_output):
    """Test that preset overrides manual parameters with warning."""
    result = runner.invoke(
        app,
        [
            "crop",
            str(sample_video),
            str(temp_output),
            "--preset",
            "center-square",
            "--width",
            "640",
            "--height",
            "480",
        ],
    )
    assert result.exit_code == 0
    assert temp_output.exists()
    assert "ignoring manual crop parameters" in result.stdout


def test_crop_even_dimensions_adjustment(sample_video, temp_output):
    """Test that odd dimensions are adjusted to even numbers."""
    # Sample video is 640x360, use odd dimensions that fit
    result = runner.invoke(
        app,
        [
            "crop",
            str(sample_video),
            str(temp_output),
            "--width",
            "321",  # Odd number
            "--height",
            "241",  # Odd number
        ],
    )
    assert result.exit_code == 0
    assert temp_output.exists()
    # Should show adjustment messages
    assert "Adjusted" in result.stdout or "320x240" in result.stdout


# Edge case tests


def test_crop_width_exceeds_video(sample_video, temp_output):
    """Test that crop fails when width exceeds video width."""
    result = runner.invoke(
        app,
        [
            "crop",
            str(sample_video),
            str(temp_output),
            "--width",
            "1000",
            "--height",
            "200",
            "--x",
            "0",
            "--y",
            "0",
        ],
    )
    assert result.exit_code != 0
    assert "exceeds video width" in result.stdout


def test_crop_height_exceeds_video(sample_video, temp_output):
    """Test that crop fails when height exceeds video height."""
    result = runner.invoke(
        app,
        [
            "crop",
            str(sample_video),
            str(temp_output),
            "--width",
            "200",
            "--height",
            "1000",
            "--x",
            "0",
            "--y",
            "0",
        ],
    )
    assert result.exit_code != 0
    assert "exceeds video height" in result.stdout


def test_crop_offset_causes_overflow(sample_video, temp_output):
    """Test that crop fails when offset + dimension exceeds video size."""
    result = runner.invoke(
        app,
        [
            "crop",
            str(sample_video),
            str(temp_output),
            "--width",
            "400",
            "--height",
            "200",
            "--x",
            "300",  # 300 + 400 = 700 > 640
            "--y",
            "0",
        ],
    )
    assert result.exit_code != 0
    assert "exceeds video" in result.stdout


def test_crop_very_small_dimensions(sample_video, temp_output):
    """Test cropping with very small dimensions shows warning."""
    result = runner.invoke(
        app,
        [
            "crop",
            str(sample_video),
            str(temp_output),
            "--width",
            "32",
            "--height",
            "32",
        ],
    )
    assert result.exit_code == 0
    assert temp_output.exists()
    assert "Warning" in result.stdout
    assert "small crop dimensions" in result.stdout


def test_crop_minimum_dimensions(sample_video, temp_output):
    """Test cropping with minimum valid dimensions (2x2)."""
    result = runner.invoke(
        app,
        [
            "crop",
            str(sample_video),
            str(temp_output),
            "--width",
            "2",
            "--height",
            "2",
            "--x",
            "0",
            "--y",
            "0",
        ],
    )
    assert result.exit_code == 0
    assert temp_output.exists()


def test_crop_full_video_dimensions(sample_video, temp_output):
    """Test cropping with full video dimensions (no actual crop)."""
    result = runner.invoke(
        app,
        [
            "crop",
            str(sample_video),
            str(temp_output),
            "--width",
            "640",
            "--height",
            "360",
            "--x",
            "0",
            "--y",
            "0",
        ],
    )
    assert result.exit_code == 0
    assert temp_output.exists()


def test_crop_offset_at_edge(sample_video, temp_output):
    """Test cropping at the edge of the video."""
    # Sample video is 640x360
    result = runner.invoke(
        app,
        [
            "crop",
            str(sample_video),
            str(temp_output),
            "--width",
            "100",
            "--height",
            "100",
            "--x",
            "540",  # 540 + 100 = 640 (exactly at edge)
            "--y",
            "260",  # 260 + 100 = 360 (exactly at edge)
        ],
    )
    assert result.exit_code == 0
    assert temp_output.exists()


def test_crop_single_pixel_beyond_edge(sample_video, temp_output):
    """Test that crop fails when even 1 pixel beyond edge."""
    result = runner.invoke(
        app,
        [
            "crop",
            str(sample_video),
            str(temp_output),
            "--width",
            "100",
            "--height",
            "100",
            "--x",
            "541",  # 541 + 100 = 641 > 640
            "--y",
            "0",
        ],
    )
    assert result.exit_code != 0
    assert "exceeds video" in result.stdout


def test_crop_preset_on_already_correct_aspect(sample_video, temp_output):
    """Test preset on video that already has the target aspect ratio."""
    # Sample video is 640x360 which is 16:9
    result = runner.invoke(
        app,
        [
            "crop",
            str(sample_video),
            str(temp_output),
            "--preset",
            "16:9",
        ],
    )
    assert result.exit_code == 0
    assert temp_output.exists()


def test_crop_with_zero_width(sample_video, temp_output):
    """Test that crop fails with zero width."""
    result = runner.invoke(
        app,
        [
            "crop",
            str(sample_video),
            str(temp_output),
            "--width",
            "0",
            "--height",
            "100",
        ],
    )
    # Should fail at validation
    assert result.exit_code != 0


def test_crop_with_zero_height(sample_video, temp_output):
    """Test that crop fails with zero height."""
    result = runner.invoke(
        app,
        [
            "crop",
            str(sample_video),
            str(temp_output),
            "--width",
            "100",
            "--height",
            "0",
        ],
    )
    # Should fail at validation
    assert result.exit_code != 0


def test_crop_case_insensitive_preset(sample_video, temp_output):
    """Test that presets are case-insensitive."""
    result = runner.invoke(
        app,
        [
            "crop",
            str(sample_video),
            str(temp_output),
            "--preset",
            "CENTER-SQUARE",
        ],
    )
    assert result.exit_code == 0
    assert temp_output.exists()


def test_crop_mixed_case_preset(sample_video, temp_output):
    """Test preset with mixed case."""
    result = runner.invoke(
        app,
        [
            "crop",
            str(sample_video),
            str(temp_output),
            "--preset",
            "Center-Square",
        ],
    )
    assert result.exit_code == 0
    assert temp_output.exists()


def test_crop_with_only_width_specified(sample_video, temp_output):
    """Test that crop fails when only width is specified without preset."""
    result = runner.invoke(
        app,
        [
            "crop",
            str(sample_video),
            str(temp_output),
            "--width",
            "320",
        ],
    )
    assert result.exit_code != 0
    assert "Must specify --width and --height" in result.stdout


def test_crop_with_only_height_specified(sample_video, temp_output):
    """Test that crop fails when only height is specified without preset."""
    result = runner.invoke(
        app,
        [
            "crop",
            str(sample_video),
            str(temp_output),
            "--height",
            "240",
        ],
    )
    assert result.exit_code != 0
    assert "Must specify --width and --height" in result.stdout


def test_crop_with_only_offsets_specified(sample_video, temp_output):
    """Test that crop fails when only offsets are specified."""
    result = runner.invoke(
        app,
        [
            "crop",
            str(sample_video),
            str(temp_output),
            "--x",
            "100",
            "--y",
            "50",
        ],
    )
    assert result.exit_code != 0
    assert "Must specify --width and --height" in result.stdout


def test_crop_output_path_same_as_input(sample_video):
    """Test that crop handles same input/output path."""
    # This should prompt for overwrite
    result = runner.invoke(
        app,
        [
            "crop",
            str(sample_video),
            str(sample_video),
            "--preset",
            "center-square",
        ],
        input="n\n",
    )
    # Should abort
    assert "Aborted" in result.stdout or "exists" in result.stdout
