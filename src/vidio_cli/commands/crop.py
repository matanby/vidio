"""Command module for cropping videos."""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from vidio_cli.ffmpeg_utils import check_output_file, get_video_info, run_ffmpeg

console = Console()


def register(app: typer.Typer) -> None:
    """
    Register the crop command with the Typer app.

    Args:
        app: The Typer app to register the command with.
    """
    app.command(no_args_is_help=True)(crop)


def validate_crop_params(
    width: int,
    height: int,
    x: int,
    y: int,
    original_width: int,
    original_height: int,
) -> None:
    """
    Validate crop parameters against original video dimensions.

    Args:
        width: Crop width
        height: Crop height
        x: X offset
        y: Y offset
        original_width: Original video width
        original_height: Original video height

    Raises:
        typer.BadParameter: If parameters are invalid
    """
    if width <= 0 or height <= 0:
        raise typer.BadParameter("Width and height must be positive")

    if x < 0 or y < 0:
        raise typer.BadParameter("X and Y offsets must be non-negative")

    if x + width > original_width:
        raise typer.BadParameter(
            f"Crop region exceeds video width: {x} + {width} > {original_width}"
        )

    if y + height > original_height:
        raise typer.BadParameter(
            f"Crop region exceeds video height: {y} + {height} > {original_height}"
        )


def parse_preset(
    preset: str,
    original_width: int,
    original_height: int,
) -> tuple[int, int, int, int]:
    """
    Parse preset crop values.

    Args:
        preset: Preset name (center-square, 16:9, 9:16, 4:3, 1:1)
        original_width: Original video width
        original_height: Original video height

    Returns:
        tuple: (width, height, x, y)

    Raises:
        typer.BadParameter: If preset is invalid or video dimensions are invalid
    """
    if original_width <= 0 or original_height <= 0:
        raise typer.BadParameter(
            f"Invalid video dimensions: {original_width}x{original_height}"
        )

    preset = preset.lower()

    if preset == "center-square" or preset == "1:1":
        # Crop to largest centered square
        size = min(original_width, original_height)
        x = (original_width - size) // 2
        y = (original_height - size) // 2
        return size, size, x, y

    elif preset == "16:9":
        # Crop to 16:9 aspect ratio
        target_ratio = 16 / 9
        current_ratio = original_width / original_height

        if current_ratio > target_ratio:
            # Too wide, crop width
            height = original_height
            width = int(height * target_ratio)
            x = (original_width - width) // 2
            y = 0
        else:
            # Too tall, crop height
            width = original_width
            height = int(width / target_ratio)
            x = 0
            y = (original_height - height) // 2

        return width, height, x, y

    elif preset == "9:16":
        # Crop to 9:16 aspect ratio (vertical/portrait)
        target_ratio = 9 / 16
        current_ratio = original_width / original_height

        if current_ratio > target_ratio:
            # Too wide, crop width
            height = original_height
            width = int(height * target_ratio)
            x = (original_width - width) // 2
            y = 0
        else:
            # Too tall, crop height
            width = original_width
            height = int(width / target_ratio)
            x = 0
            y = (original_height - height) // 2

        return width, height, x, y

    elif preset == "4:3":
        # Crop to 4:3 aspect ratio
        target_ratio = 4 / 3
        current_ratio = original_width / original_height

        if current_ratio > target_ratio:
            # Too wide, crop width
            height = original_height
            width = int(height * target_ratio)
            x = (original_width - width) // 2
            y = 0
        else:
            # Too tall, crop height
            width = original_width
            height = int(width / target_ratio)
            x = 0
            y = (original_height - height) // 2

        return width, height, x, y

    else:
        raise typer.BadParameter(
            f"Unknown preset: {preset}. Valid presets: center-square, 16:9, 9:16, 4:3, 1:1"
        )


def crop(
    ctx: typer.Context,
    input_file: Path = typer.Argument(
        ...,
        help="Input video file to crop",
        exists=True,
        dir_okay=False,
        resolve_path=True,
    ),
    output_file: Path = typer.Argument(
        ...,
        help="Output video file",
        dir_okay=False,
        resolve_path=True,
    ),
    width: Optional[int] = typer.Option(
        None,
        "--width",
        "-w",
        help="Width of the cropped region in pixels",
        min=1,
    ),
    height: Optional[int] = typer.Option(
        None,
        "--height",
        "-h",
        help="Height of the cropped region in pixels",
        min=1,
    ),
    x: Optional[int] = typer.Option(
        None,
        "--x",
        help="X offset (left edge) of the crop region in pixels",
        min=0,
    ),
    y: Optional[int] = typer.Option(
        None,
        "--y",
        help="Y offset (top edge) of the crop region in pixels",
        min=0,
    ),
    preset: Optional[str] = typer.Option(
        None,
        "--preset",
        "-p",
        help="Use a preset crop (center-square, 16:9, 9:16, 4:3, 1:1)",
    ),
    keep_aspect: bool = typer.Option(
        True,
        "--keep-aspect/--no-keep-aspect",
        help="Keep aspect ratio when using width/height only",
    ),
    overwrite: bool = typer.Option(
        False,
        "--overwrite",
        help="Overwrite output file if it exists",
    ),
) -> None:
    """
    Crop a video to a specific region.

    You can specify the crop region manually with --width, --height, --x, --y,
    or use a preset for common aspect ratios.

    Examples:
        - Crop to center square: vidio crop input.mp4 output.mp4 --preset center-square
        - Crop to 16:9: vidio crop input.mp4 output.mp4 --preset 16:9
        - Custom crop: vidio crop input.mp4 output.mp4 -w 1280 -h 720 --x 100 --y 50
        - Crop from top-left: vidio crop input.mp4 output.mp4 -w 1920 -h 1080
    """
    # Get verbose flag from global context
    verbose = ctx.obj.get("VERBOSE", False) if ctx.obj else False

    # Check if output file exists and if we should overwrite it
    if not check_output_file(output_file, overwrite):
        console.print("[yellow]Aborted.[/yellow]")
        raise typer.Exit(0)

    # Get original video dimensions
    try:
        video_info = get_video_info(input_file, verbose)
        video_streams = [
            s for s in video_info.get("streams", []) if s.get("codec_type") == "video"
        ]

        if not video_streams:
            console.print("[red]Error: No video stream found in input file[/red]")
            console.print(
                "[dim]The file may be corrupted or not a valid video file.[/dim]"
            )
            raise typer.Exit(1)

        original_width = video_streams[0].get("width", 0)
        original_height = video_streams[0].get("height", 0)

        if not original_width or not original_height:
            console.print(
                "[red]Error: Could not determine original video dimensions[/red]"
            )
            console.print(
                "[dim]The video file may be corrupted or in an unsupported format.[/dim]"
            )
            raise typer.Exit(1)

        # Validate dimensions are reasonable
        if original_width > 16384 or original_height > 16384:
            console.print(
                f"[yellow]Warning: Very large video dimensions ({original_width}x{original_height}). "
                "Processing may be slow.[/yellow]"
            )

        if original_width < 2 or original_height < 2:
            console.print(
                f"[red]Error: Video dimensions too small ({original_width}x{original_height}). "
                "Cannot crop.[/red]"
            )
            raise typer.Exit(1)

        console.print(
            f"[dim]Original video dimensions: {original_width}x{original_height}[/dim]"
        )

    except typer.Exit:
        raise
    except Exception as e:
        console.print(f"[red]Error reading video info: {e}[/red]")
        console.print("[dim]Make sure the input file is a valid video file.[/dim]")
        raise typer.Exit(1)

    # Determine crop parameters
    if preset:
        if any([width, height, x, y]):
            console.print(
                "[yellow]Warning: Preset specified, ignoring manual crop parameters[/yellow]"
            )

        try:
            crop_width, crop_height, crop_x, crop_y = parse_preset(
                preset, original_width, original_height
            )
            console.print(f"[blue]Using preset: {preset}[/blue]")
        except typer.BadParameter as e:
            console.print(f"[red]Error: {e}[/red]")
            raise typer.Exit(1)

    else:
        # Manual crop parameters
        if width is None or height is None:
            console.print(
                "[red]Error: Must specify --width and --height, or use --preset[/red]"
            )
            raise typer.Exit(1)

        # Validate manual dimensions don't exceed video
        if width > original_width:
            console.print(
                f"[red]Error: Crop width ({width}) exceeds video width ({original_width})[/red]"
            )
            raise typer.Exit(1)

        if height > original_height:
            console.print(
                f"[red]Error: Crop height ({height}) exceeds video height ({original_height})[/red]"
            )
            raise typer.Exit(1)

        crop_width = width
        crop_height = height
        crop_x = x if x is not None else 0
        crop_y = y if y is not None else 0

        # Default to center if no offsets specified and keep_aspect is True
        if x is None and y is None and keep_aspect:
            crop_x = (original_width - crop_width) // 2
            crop_y = (original_height - crop_height) // 2
            console.print("[dim]Centering crop region (no offsets specified)[/dim]")

    # Ensure even dimensions for better codec compatibility
    if crop_width % 2 != 0:
        crop_width -= 1
        console.print(
            f"[dim]Adjusted width to {crop_width} (must be even for codec compatibility)[/dim]"
        )

    if crop_height % 2 != 0:
        crop_height -= 1
        console.print(
            f"[dim]Adjusted height to {crop_height} (must be even for codec compatibility)[/dim]"
        )

    # Warn if crop dimensions are very small
    if crop_width < 64 or crop_height < 64:
        console.print(
            f"[yellow]Warning: Very small crop dimensions ({crop_width}x{crop_height}). "
            "Output quality may be poor.[/yellow]"
        )

    # Validate crop parameters
    try:
        validate_crop_params(
            crop_width, crop_height, crop_x, crop_y, original_width, original_height
        )
    except typer.BadParameter as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)

    # Show what we're doing
    console.print(
        f"[blue]Cropping to {crop_width}x{crop_height} at position ({crop_x}, {crop_y})[/blue]"
    )

    # Build the ffmpeg command with crop filter
    crop_filter = f"crop={crop_width}:{crop_height}:{crop_x}:{crop_y}"

    command = [
        "ffmpeg",
        "-i",
        str(input_file),
        "-vf",
        crop_filter,
        "-c:a",
        "copy",  # Copy audio without re-encoding
        "-y" if overwrite else "-n",  # Overwrite if specified
        str(output_file),
    ]

    # Run the command
    run_ffmpeg(command, verbose=verbose)

    console.print(f"[green]✓[/green] Cropped video saved to {output_file}")
