"""Command module for arranging videos in a grid layout."""

import math
from pathlib import Path

import typer
from rich.console import Console

from vidio_cli.ffmpeg_utils import run_ffmpeg, check_output_file

console = Console()


def register(app: typer.Typer) -> None:
    """
    Register the grid command with the Typer app.

    Args:
        app: The Typer app to register the command with.
    """
    app.command(no_args_is_help=True)(grid)


def calculate_grid_size(
    num_videos: int, rows: int | None = None, cols: int | None = None
) -> tuple[int, int]:
    """
    Calculate the optimal grid size for the given number of videos.

    Args:
        num_videos: Number of videos to arrange.
        rows: Desired number of rows (optional).
        cols: Desired number of columns (optional).

    Returns:
        tuple[int, int]: (rows, cols) for the grid.

    Raises:
        ValueError: If the specified rows/cols don't accommodate all videos.
    """
    if rows is not None and cols is not None:
        # Both specified - validate they can hold all videos
        if rows * cols < num_videos:
            raise ValueError(
                f"Grid size {rows}×{cols} ({rows * cols} cells) cannot accommodate {num_videos} videos"
            )
        return rows, cols
    elif rows is not None:
        # Only rows specified - calculate cols
        cols = math.ceil(num_videos / rows)
        return rows, cols
    elif cols is not None:
        # Only cols specified - calculate rows
        rows = math.ceil(num_videos / cols)
        return rows, cols
    else:
        # Neither specified - calculate optimal square-ish grid
        # Prefer more columns over rows for better aspect ratio
        sqrt_videos = math.sqrt(num_videos)
        cols = math.ceil(sqrt_videos)
        rows = math.ceil(num_videos / cols)
        return rows, cols


def grid(
    ctx: typer.Context,
    input_files: list[Path] = typer.Argument(
        ...,
        help="Input video files to arrange in a grid",
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
    rows: int | None = typer.Option(
        None,
        "--rows",
        "-r",
        help="Number of rows in the grid (calculated if not specified)",
    ),
    cols: int | None = typer.Option(
        None,
        "--cols",
        "-c",
        help="Number of columns in the grid (calculated if not specified)",
    ),
    width: int | None = typer.Option(
        None,
        "--width",
        "-w",
        help="Width of each cell in pixels (maintains aspect ratio, original size if not specified)",
    ),
    height: int | None = typer.Option(
        None,
        "--height",
        "-h",
        help="Height of each cell in pixels (maintains aspect ratio, original size if not specified)",
    ),
    padding: int = typer.Option(
        0,
        "--padding",
        "-p",
        help="Padding between videos in pixels",
    ),
    background: str = typer.Option(
        "black",
        "--background",
        "-b",
        help="Background color for empty cells and padding",
    ),
    overwrite: bool = typer.Option(
        False,
        "--overwrite",
        help="Overwrite output file if it exists",
    ),
) -> None:
    """
    Arrange multiple videos in a grid layout.

    Examples:
        - Create a 2x2 grid: vidio grid video1.mp4 video2.mp4 video3.mp4 video4.mp4 output.mp4
        - Specify grid dimensions: vidio grid video1.mp4 video2.mp4 video3.mp4 video4.mp4 output.mp4 --rows 2
        - Set cell size: vidio grid video1.mp4 video2.mp4 video3.mp4 video4.mp4 output.mp4 --width 640 --height 360
        - Add padding: vidio grid video1.mp4 video2.mp4 video3.mp4 video4.mp4 output.mp4 --padding 10
    """
    # Get verbose flag from global context
    verbose = ctx.obj.get("VERBOSE", False) if ctx.obj else False

    # Check if output file exists and if we should overwrite it
    if not check_output_file(output_file, overwrite):
        console.print("[yellow]Aborted.[/yellow]")
        raise typer.Exit(code=0)

    # Calculate grid dimensions
    try:
        grid_rows, grid_cols = calculate_grid_size(len(input_files), rows, cols)
    except ValueError as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        raise typer.Exit(code=1)

    if verbose:
        console.print(
            f"Creating {grid_rows}×{grid_cols} video grid with {len(input_files)} videos..."
        )

    # Prepare inputs
    inputs = []
    for i, file_path in enumerate(input_files):
        inputs.extend(["-i", str(file_path)])

    # Count of videos to include in the grid
    video_count = min(len(input_files), grid_rows * grid_cols)

    # Build the filter complex based on whether width/height are specified
    if width is not None and height is not None:
        # With specific dimensions: use scale + xstack with fixed positions

        # Scale all videos to the same size
        filter_complex = ""
        for i in range(video_count):
            filter_complex += (
                f"[{i}:v]scale={width}:{height}:force_original_aspect_ratio=decrease,"
                f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:{background}[v{i}];"
            )

        # Calculate positions for each video in the grid
        positions = []
        for i in range(video_count):
            row = i // grid_cols
            col = i % grid_cols
            x = col * (width + padding)
            y = row * (height + padding)
            positions.append(f"{x}_{y}")

        # Create inputs string for xstack
        inputs_str = ""
        for i in range(video_count):
            inputs_str += f"[v{i}]"

        # Add xstack filter
        filter_complex += (
            f"{inputs_str}xstack=inputs={video_count}:layout={'|'.join(positions)}"
        )

        # Add background color for padding
        if padding > 0:
            filter_complex += f":fill={background}"

        # Add output label
        filter_complex += "[v]"

    else:
        # Without width/height: use a simplified hstack/vstack approach
        filter_complex = ""
        default_height = 360  # Use a reasonable default height

        # 1. Scale all videos to the same height and label them [v0], [v1], ...
        for i in range(video_count):
            filter_complex += f"[{i}:v]scale=-1:{default_height}[v{i}];"

        row_labels = []  # To store labels like [row0], [row1]

        # 2. Create each row using hstack (or copy for single video rows)
        for r in range(grid_rows):
            current_row_input_videos = []  # Collect video labels for the current row, e.g., ["[v0]", "[v1]"]
            for c in range(grid_cols):
                video_idx = r * grid_cols + c
                if video_idx < video_count:
                    current_row_input_videos.append(f"[v{video_idx}]")

            if current_row_input_videos:  # If there are videos in this row
                row_input_str = "".join(current_row_input_videos)
                if len(current_row_input_videos) > 1:
                    filter_complex += f"{row_input_str}hstack=inputs={len(current_row_input_videos)}[row{r}];"
                else:  # Single video in this row
                    filter_complex += f"{row_input_str}copy[row{r}];"
                row_labels.append(f"[row{r}]")

        # 3. Stack all created rows vertically (or copy for a single row)
        if row_labels:  # Should always be true if video_count > 0 (min inputs is 2)
            final_rows_input_str = "".join(row_labels)
            if len(row_labels) > 1:
                filter_complex += (
                    f"{final_rows_input_str}vstack=inputs={len(row_labels)}[v];"
                )
            else:  # Single row overall
                filter_complex += f"{final_rows_input_str}copy[v];"
        # If row_labels is empty (e.g. video_count was 0, though not possible here due to min=2),
        # filter_complex would just contain scaling filters, leading to an error.
        # However, with min=2 inputs, row_labels will always have at least one item.

    # Debug output
    if verbose:
        console.print(f"Filter complex: {filter_complex}")

    # Build the ffmpeg command
    command = [
        "ffmpeg",
        *inputs,
        "-filter_complex",
        filter_complex,
        "-map",
        "[v]",
        "-c:v",
        "libx264",
        "-an",  # No audio
        "-y" if overwrite else "-n",
        str(output_file),
    ]

    # Run the command
    run_ffmpeg(command, verbose=verbose)
