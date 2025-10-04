"""Command module for resizing videos."""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from vidio_cli.ffmpeg_utils import check_output_file, get_video_info, run_ffmpeg

console = Console()


def register(app: typer.Typer) -> None:
    """
    Register the resize command with the Typer app.

    Args:
        app: The Typer app to register the command with.
    """
    app.command(no_args_is_help=True)(resize)


def validate_dimensions(width: Optional[int], height: Optional[int], scale: Optional[float]) -> None:
    """
    Validate resize parameters.
    
    Args:
        width: Target width in pixels
        height: Target height in pixels  
        scale: Scale factor
        
    Raises:
        typer.BadParameter: If parameters are invalid
    """
    if not any([width, height, scale]):
        raise typer.BadParameter("Must specify at least one of: --width, --height, or --scale")
    
    if scale and (width or height):
        raise typer.BadParameter("Cannot use --scale with --width or --height")
    
    if scale and (scale <= 0 or scale > 10):
        raise typer.BadParameter("Scale must be between 0 and 10")
    
    if width and width <= 0:
        raise typer.BadParameter("Width must be positive")
        
    if height and height <= 0:
        raise typer.BadParameter("Height must be positive")


def build_scale_filter(
    width: Optional[int], 
    height: Optional[int], 
    scale: Optional[float],
    maintain_aspect: bool,
    original_width: int,
    original_height: int
) -> str:
    """
    Build the ffmpeg scale filter string.
    
    Args:
        width: Target width
        height: Target height
        scale: Scale factor
        maintain_aspect: Whether to maintain aspect ratio
        original_width: Original video width
        original_height: Original video height
        
    Returns:
        str: ffmpeg scale filter string
    """
    if scale:
        # Scale both dimensions by the same factor
        new_width = int(original_width * scale)
        new_height = int(original_height * scale)
        # Ensure even dimensions for better codec compatibility
        new_width = new_width - (new_width % 2)
        new_height = new_height - (new_height % 2)
        return f"scale={new_width}:{new_height}"
    
    if maintain_aspect:
        # Use -2 to maintain aspect ratio and ensure even dimensions
        if width and height:
            return f"scale={width}:{height}"
        elif width:
            return f"scale={width}:-2"
        elif height:
            return f"scale=-2:{height}"
    else:
        # Force exact dimensions (may distort)
        w = width or original_width
        h = height or original_height
        return f"scale={w}:{h}"
    
    return "scale=-2:-2"  # Fallback


def resize(
    ctx: typer.Context,
    input_file: Path = typer.Argument(
        ...,
        help="Input video file to resize",
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
        help="Target width in pixels",
        min=1,
    ),
    height: Optional[int] = typer.Option(
        None,
        "--height",
        "-h",
        help="Target height in pixels", 
        min=1,
    ),
    scale: Optional[float] = typer.Option(
        None,
        "--scale",
        "-s",
        help="Scale factor (e.g., 0.5 for 50%, 2.0 for 200%)",
        min=0.1,
        max=10.0,
    ),
    force_aspect: bool = typer.Option(
        False,
        "--force-aspect",
        help="Force exact dimensions (may distort image)",
    ),
    overwrite: bool = typer.Option(
        False,
        "--overwrite",
        help="Overwrite output file if it exists",
    ),
) -> None:
    """
    Resize a video to new dimensions or scale factor.

    By default, maintains aspect ratio. Use --force-aspect to allow distortion.

    Examples:
        - Resize to 1920x1080: vidio resize input.mp4 output.mp4 --width 1920 --height 1080
        - Scale to 50%: vidio resize input.mp4 output.mp4 --scale 0.5
        - Resize width, keep aspect ratio: vidio resize input.mp4 output.mp4 --width 1280
        - Force exact dimensions: vidio resize input.mp4 output.mp4 -w 1920 -h 1080 --force-aspect
    """
    # Get verbose flag from global context
    verbose = ctx.obj.get("VERBOSE", False) if ctx.obj else False

    # Validate parameters
    validate_dimensions(width, height, scale)

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

    # Build the scale filter
    maintain_aspect = not force_aspect
    scale_filter = build_scale_filter(
        width, height, scale, maintain_aspect, original_width, original_height
    )

    # Show what we're doing
    if scale:
        console.print(f"[blue]Scaling video by {scale}x[/blue]")
    else:
        target_w = width or "auto"
        target_h = height or "auto"
        console.print(f"[blue]Resizing video to {target_w}x{target_h}[/blue]")
        
    if not maintain_aspect:
        console.print("[yellow]Warning: Forcing aspect ratio may distort the video[/yellow]")

    # Build the ffmpeg command
    command = [
        "ffmpeg",
        "-i", str(input_file),
        "-vf", scale_filter,
        "-c:a", "copy",  # Copy audio without re-encoding
        "-y" if overwrite else "-n",  # Overwrite if specified
        str(output_file),
    ]

    # Run the command
    run_ffmpeg(command, verbose=verbose)

    console.print(f"[green]✓[/green] Resized video saved to {output_file}")