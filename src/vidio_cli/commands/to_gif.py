"""Command module for converting videos to GIF format."""

import tempfile
from pathlib import Path
from typing import Optional

import click
import typer
from rich.console import Console

from vidio_cli.ffmpeg_utils import check_output_file, get_video_info, run_ffmpeg

console = Console()


def register(app: typer.Typer) -> None:
    """
    Register the to-gif command with the Typer app.

    Args:
        app: The Typer app to register the command with.
    """
    app.command("to-gif", no_args_is_help=True)(to_gif)


def parse_time(time_str: str) -> str:
    """
    Parse and validate time format.
    
    Args:
        time_str: Time string in format like "00:01:30", "90", "1:30"
        
    Returns:
        str: Validated time string for ffmpeg
    """
    # If it's just numbers, assume seconds
    if time_str.isdigit():
        return time_str
    
    # Basic validation for HH:MM:SS or MM:SS format
    parts = time_str.split(":")
    if len(parts) > 3:
        raise typer.BadParameter("Time format should be HH:MM:SS, MM:SS, or seconds")
    
    return time_str


def validate_quality(quality: str) -> str:
    """
    Validate and normalize quality setting.
    
    Args:
        quality: Quality string (low/medium/high or 1-10)
        
    Returns:
        str: Normalized quality level
    """
    quality_lower = quality.lower()
    if quality_lower in ["low", "medium", "high"]:
        return quality_lower
    
    # Try to parse as number
    try:
        q_num = int(quality)
        if 1 <= q_num <= 10:
            if q_num <= 3:
                return "low"
            elif q_num <= 7:
                return "medium"
            else:
                return "high"
        else:
            raise typer.BadParameter("Quality number must be between 1-10")
    except ValueError:
        raise typer.BadParameter("Quality must be 'low', 'medium', 'high', or a number 1-10")


def build_filter_complex(
    fps: int,
    width: Optional[int],
    scale: Optional[float],
    start: Optional[str],
    end: Optional[str],
    duration: Optional[str],
    original_width: int,
    original_height: int,
) -> tuple[list[str], str]:
    """
    Build ffmpeg filter complex and input arguments for GIF conversion.
    
    Returns:
        tuple: (input_args, filter_string)
    """
    input_args = []
    
    # Add time range options to input
    if start and start != "0":
        input_args.extend(["-ss", start])
    if end:
        input_args.extend(["-to", end])
    elif duration:
        input_args.extend(["-t", duration])
    
    # Build scale filter
    if scale:
        new_width = int(original_width * scale)
        new_height = int(original_height * scale)
        # Ensure even dimensions
        new_width = new_width - (new_width % 2)
        new_height = new_height - (new_height % 2)
        scale_filter = f"scale={new_width}:{new_height}:flags=lanczos"
    elif width:
        scale_filter = f"scale={width}:-2:flags=lanczos"
    else:
        scale_filter = f"scale={original_width}:{original_height}:flags=lanczos"
    
    # Combine filters
    filter_string = f"fps={fps},{scale_filter}"
    
    return input_args, filter_string


def to_gif(
    ctx: typer.Context,
    input_file: Path = typer.Argument(
        ...,
        help="Input video file to convert to GIF",
        exists=True,
        dir_okay=False,
        resolve_path=True,
    ),
    output_file: Path = typer.Argument(
        ...,
        help="Output GIF file",
        dir_okay=False,
        resolve_path=True,
    ),
    fps: int = typer.Option(
        10,
        "--fps",
        "-f",
        help="Frame rate for the GIF",
        min=1,
        max=30,
    ),
    width: Optional[int] = typer.Option(
        None,
        "--width",
        "-w",
        help="Target width in pixels (height auto-calculated)",
        min=1,
    ),
    scale: Optional[float] = typer.Option(
        None,
        "--scale",
        "-s",
        help="Scale factor (e.g., 0.5 for 50%)",
        min=0.1,
        max=2.0,
    ),
    quality: str = typer.Option(
        "medium",
        "--quality",
        "-q",
        help="Quality level: low, medium, high, or 1-10",
        callback=lambda ctx, param, value: validate_quality(value) if value else "medium",
    ),
    start: str = typer.Option(
        "0",
        "--start",
        "-t",
        help="Start time (HH:MM:SS, MM:SS, or seconds)",
        callback=lambda ctx, param, value: parse_time(value) if value else "0",
    ),
    end: Optional[str] = typer.Option(
        None,
        "--end",
        "-e",
        help="End time (HH:MM:SS, MM:SS, or seconds)",
        callback=lambda ctx, param, value: parse_time(value) if value else None,
    ),
    duration: Optional[str] = typer.Option(
        None,
        "--duration",
        "-d",
        help="Duration to convert (HH:MM:SS, MM:SS, or seconds)",
        callback=lambda ctx, param, value: parse_time(value) if value else None,
    ),
    loop: int = typer.Option(
        0,
        "--loop",
        help="Number of loops (0 = infinite)",
        min=0,
    ),
    dither: str = typer.Option(
        "floyd_steinberg",
        "--dither",
        help="Dithering algorithm",
        click_type=click.Choice(["none", "bayer", "floyd_steinberg"]),
    ),
    no_optimize: bool = typer.Option(
        False,
        "--no-optimize",
        help="Skip palette optimization (faster but lower quality)",
    ),
    overwrite: bool = typer.Option(
        False,
        "--overwrite",
        help="Overwrite output file if it exists",
    ),
) -> None:
    """
    Convert a video to high-quality GIF format using two-pass optimization.

    Uses palette generation for better quality and smaller file sizes.

    Examples:
        - Basic conversion: vidio to-gif video.mp4 output.gif
        - High quality: vidio to-gif video.mp4 output.gif --fps 15 --quality high
        - Small file size: vidio to-gif video.mp4 output.gif --scale 0.3 --fps 8
        - Time range: vidio to-gif video.mp4 output.gif --start 10 --duration 5
        - Custom width: vidio to-gif video.mp4 output.gif --width 800
    """
    # Get verbose flag from global context
    verbose = ctx.obj.get("VERBOSE", False) if ctx.obj else False

    # Validate arguments
    if end and duration:
        console.print("[red]Error: Cannot specify both --end and --duration[/red]")
        raise typer.Exit(1)
    
    if scale and width:
        console.print("[red]Error: Cannot specify both --scale and --width[/red]")
        raise typer.Exit(1)

    # Check if output file exists and if we should overwrite it
    if not check_output_file(output_file, overwrite):
        console.print("[yellow]Aborted.[/yellow]")
        raise typer.Exit(0)

    # Get original video dimensions
    try:
        video_info = get_video_info(input_file, verbose)
        video_streams = [s for s in video_info.get("streams", []) if s.get("codec_type") == "video"]
        
        if not video_streams:
            console.print("[red]Error: No video stream found in input file[/red]")
            raise typer.Exit(1)
            
        original_width = video_streams[0].get("width", 0)
        original_height = video_streams[0].get("height", 0)
        
        if not original_width or not original_height:
            console.print("[red]Error: Could not determine original video dimensions[/red]")
            raise typer.Exit(1)
            
    except Exception as e:
        console.print(f"[red]Error reading video info: {e}[/red]")
        raise typer.Exit(1)

    # Build filter arguments
    input_args, base_filter = build_filter_complex(
        fps, width, scale, start, end, duration, original_width, original_height
    )

    # Show what we're doing
    if scale:
        console.print(f"[blue]Converting to GIF with {scale}x scale at {fps} fps[/blue]")
    elif width:
        console.print(f"[blue]Converting to GIF with width {width}px at {fps} fps[/blue]")
    else:
        console.print(f"[blue]Converting to GIF at original size with {fps} fps[/blue]")

    if no_optimize:
        console.print("[yellow]Skipping palette optimization (faster but lower quality)[/yellow]")
        
        # Single-pass conversion without palette optimization
        command = [
            "ffmpeg",
            *input_args,
            "-i", str(input_file),
            "-vf", base_filter,
            "-loop", str(loop),
            "-y" if overwrite else "-n",
            str(output_file),
        ]
        
        run_ffmpeg(command, verbose=verbose)
    else:
        console.print("[blue]Using two-pass conversion with palette optimization...[/blue]")
        
        # Two-pass conversion with palette optimization
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as palette_file:
            palette_path = Path(palette_file.name)
            
        try:
            # Pass 1: Generate palette
            console.print("[dim]Pass 1: Generating optimal color palette...[/dim]")
            
            # Quality-based palette generation
            if quality == "high":
                palette_filter = f"{base_filter},palettegen=max_colors=256:reserve_transparent=0"
            elif quality == "low":
                palette_filter = f"{base_filter},palettegen=max_colors=128:reserve_transparent=0"
            else:  # medium
                palette_filter = f"{base_filter},palettegen=max_colors=192:reserve_transparent=0"
            
            palette_command = [
                "ffmpeg",
                *input_args,
                "-i", str(input_file),
                "-vf", palette_filter,
                "-y",
                str(palette_path),
            ]
            
            run_ffmpeg(palette_command, verbose=verbose)
            
            # Pass 2: Create GIF with palette
            console.print("[dim]Pass 2: Creating GIF with optimized palette...[/dim]")
            
            # Dithering options
            dither_option = f"dither={dither}" if dither != "none" else "dither=none"
            
            gif_command = [
                "ffmpeg",
                *input_args,
                "-i", str(input_file),
                "-i", str(palette_path),
                "-filter_complex", f"{base_filter}[x];[x][1:v]paletteuse={dither_option}",
                "-loop", str(loop),
                "-y" if overwrite else "-n",
                str(output_file),
            ]
            
            run_ffmpeg(gif_command, verbose=verbose)
            
        finally:
            # Clean up temporary palette file
            if palette_path.exists():
                palette_path.unlink()

    # Show file size info
    if output_file.exists():
        file_size = output_file.stat().st_size
        size_mb = file_size / (1024 * 1024)
        console.print(f"[green]✓[/green] GIF created: {output_file}")
        console.print(f"[dim]File size: {size_mb:.2f} MB ({file_size:,} bytes)[/dim]")
    else:
        console.print("[red]Error: GIF file was not created[/red]")
        raise typer.Exit(1)
