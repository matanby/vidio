"""Command module for concatenating videos horizontally or vertically."""

from pathlib import Path
from typing import List

import typer
from rich.console import Console

from vidio_cli.ffmpeg_utils import check_output_file, run_ffmpeg

console = Console()


def register(app: typer.Typer) -> None:
    """
    Register the concat command with the Typer app.

    Args:
        app: The Typer app to register the command with.
    """
    app.command()(concat)


def concat(
    input_files: List[Path] = typer.Argument(
        ...,
        help="Input video files to concatenate",
        exists=True,
        dir_okay=False,
        resolve_path=True,
        min=2,
    ),
    output_file: Path = typer.Argument(
        ...,
        help="Output video file",
        dir_okay=False,
        resolve_path=True,
    ),
    vertical: bool = typer.Option(
        False,
        "--vertical",
        "-v",
        help="Stack videos vertically instead of horizontally",
    ),
    overwrite: bool = typer.Option(
        False,
        "--overwrite",
        help="Overwrite output file if it exists",
    ),
    quiet: bool = typer.Option(
        False,
        "--quiet",
        "-q",
        help="Suppress all output except errors",
    ),
) -> None:
    """
    Concatenate multiple videos side by side (horizontally) or stacked (vertically).

    Examples:
        - Concatenate videos horizontally: vidio concat video1.mp4 video2.mp4 output.mp4
        - Stack videos vertically: vidio concat video1.mp4 video2.mp4 output.mp4 --vertical
    """
    # Check if output file exists and if we should overwrite it
    if not check_output_file(output_file, overwrite):
        console.print("[yellow]Aborted.[/yellow]")
        raise typer.Exit(code=0)

    if not quiet:
        direction = "vertically" if vertical else "horizontally"
        console.print(f"Concatenating {len(input_files)} videos {direction}...")

    # Build the filter complex string for concatenation
    filter_complex = ""

    # Prepare inputs
    inputs = []
    for i, _ in enumerate(input_files):
        inputs.extend(["-i", str(input_files[i])])

    # Set the layout direction
    layout = "vstack" if vertical else "hstack"

    # Create filter_complex setting for proper scaling
    inputs_str = "[0:v]"
    for i in range(1, len(input_files)):
        inputs_str += f"[{i}:v]"

    filter_complex = f"{inputs_str}{layout}=inputs={len(input_files)}[v]"

    # Build the ffmpeg command
    command = [
        "ffmpeg",
        *inputs,
        "-filter_complex",
        filter_complex,
        "-map",
        "[v]",
        # Map all audio streams (if present)
        "-map",
        "0:a?",
        # Use the first audio stream for output
        "-c:a",
        "aac",
        "-shortest",  # End when shortest input ends
        "-y" if overwrite else "-n",  # Overwrite if specified
        str(output_file),
    ]

    # Run the command
    run_ffmpeg(command, quiet=quiet)

    if not quiet:
        console.print(f"[green]Concatenation completed![/green] Output saved to: {output_file}")

    return
