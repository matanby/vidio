"""Command module for trimming videos by time range."""

from pathlib import Path

import typer
from rich.console import Console

from vidio_cli.ffmpeg_utils import check_output_file, run_ffmpeg

console = Console()


def register(app: typer.Typer) -> None:
    """
    Register the trim command with the Typer app.

    Args:
        app: The Typer app to register the command with.
    """
    app.command(no_args_is_help=True)(trim)


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


def trim(
    ctx: typer.Context,
    input_file: Path = typer.Argument(
        ...,
        help="Input video file to trim",
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
    start: str = typer.Option(
        "0",
        "--start",
        "-s",
        help="Start time (HH:MM:SS, MM:SS, or seconds)",
        callback=lambda ctx, param, value: parse_time(value) if value else "0",
    ),
    end: str = typer.Option(
        None,
        "--end",
        "-e",
        help="End time (HH:MM:SS, MM:SS, or seconds). If not specified, trim to end of video",
        callback=lambda ctx, param, value: parse_time(value) if value else None,
    ),
    duration: str = typer.Option(
        None,
        "--duration",
        "-d",
        help="Duration to trim (HH:MM:SS, MM:SS, or seconds). Alternative to --end",
        callback=lambda ctx, param, value: parse_time(value) if value else None,
    ),
    overwrite: bool = typer.Option(
        False,
        "--overwrite",
        help="Overwrite output file if it exists",
    ),
) -> None:
    """
    Trim a video by specifying start and end times or duration.

    Examples:
        - Trim from 30s to 90s: vidio trim input.mp4 output.mp4 --start 30 --end 90
        - Trim from 1:30 for 45 seconds: vidio trim input.mp4 output.mp4 --start 1:30 --duration 45
        - Trim from beginning to 2:15: vidio trim input.mp4 output.mp4 --end 2:15
        - Trim last 30 seconds: vidio trim input.mp4 output.mp4 --start -30
    """
    # Get verbose flag from global context
    verbose = ctx.obj.get("VERBOSE", False) if ctx.obj else False

    # Validate arguments
    if end and duration:
        console.print("[red]Error: Cannot specify both --end and --duration[/red]")
        raise typer.Exit(1)

    # Check if output file exists and if we should overwrite it
    if not check_output_file(output_file, overwrite):
        console.print("[yellow]Aborted.[/yellow]")
        raise typer.Exit(0)

    # Build the ffmpeg command
    command = ["ffmpeg", "-i", str(input_file)]

    # Add start time if specified
    if start != "0":
        command.extend(["-ss", start])

    # Add end time or duration
    if end:
        command.extend(["-to", end])
    elif duration:
        command.extend(["-t", duration])

    # Add output options
    command.extend([
        "-c", "copy",  # Copy streams without re-encoding for speed
        "-avoid_negative_ts", "make_zero",  # Handle negative timestamps
        "-y" if overwrite else "-n",  # Overwrite if specified
        str(output_file),
    ])

    # Run the command
    run_ffmpeg(command, verbose=verbose)

    console.print(f"[green]✓[/green] Trimmed video saved to {output_file}")