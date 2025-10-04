"""Command module for listing video files in the current directory."""

import json
import subprocess
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from vidio_cli.ffmpeg_utils import run_command

console = Console()

# Common video file extensions
VIDEO_EXTENSIONS = {
    ".mp4",
    ".avi",
    ".mov",
    ".mkv",
    ".wmv",
    ".flv",
    ".webm",
    ".m4v",
    ".3gp",
    ".3g2",
    ".mxf",
    ".roq",
    ".nsv",
    ".f4v",
    ".f4p",
    ".f4a",
    ".f4b",
}


def register(app: typer.Typer) -> None:
    """
    Register the list command with the Typer app.

    Args:
        app: The Typer app to register the command with.
    """
    # Register both 'list' and 'ls' as aliases for the same command
    app.command("list", no_args_is_help=False)(list_videos)
    app.command("ls", no_args_is_help=False)(list_videos)


def get_video_info(video_file: Path, verbose: bool = False) -> Optional[dict]:
    """
    Get basic information about a video file using ffprobe.

    Args:
        video_file: Path to the video file.
        verbose: If True, show ffprobe commands and other debug info.

    Returns:
        dict: Video information or None if failed to get info.
    """
    command = [
        "ffprobe",
        "-v",
        "quiet",
        "-print_format",
        "json",
        "-show_format",
        "-show_streams",
        str(video_file),
    ]

    try:
        result = run_command(command, verbose=verbose, check=True, capture_output=True)
        return json.loads(result.stdout)
    except (json.JSONDecodeError, subprocess.CalledProcessError, FileNotFoundError):
        return None


def format_duration(seconds: float) -> str:
    """
    Format duration from seconds to HH:MM:SS format.

    Args:
        seconds: Duration in seconds.

    Returns:
        str: Formatted duration string.
    """
    if seconds <= 0:
        return "00:00:00"

    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{int(hours):02d}:{int(minutes):02d}:{int(secs):02d}"


def format_size(bytes_size: int) -> str:
    """
    Format file size in human-readable format.

    Args:
        bytes_size: Size in bytes.

    Returns:
        str: Formatted size string.
    """
    for unit in ["B", "KB", "MB", "GB"]:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} TB"


def format_ls_output(video_data: list[dict], verbose: bool = False) -> None:
    """
    Format video data in ls -l style output with colors.
    
    Args:
        video_data: List of video file information dictionaries.
        verbose: If True, show detailed information.
    """
    if not video_data:
        return
    
    # Calculate column widths for alignment
    max_size_width = max(len(video["size_formatted"]) for video in video_data)
    max_duration_width = max(len(video.get("duration_formatted", "")) for video in video_data) if verbose else 0
    max_resolution_width = max(len(video.get("resolution", "")) for video in video_data) if verbose else 0
    
    for video in video_data:
        # File size (right-aligned like ls -l)
        size_str = f"{video['size_formatted']:>{max_size_width}}"
        
        if verbose:
            # Detailed format: size duration resolution codec filename
            duration_str = f"{video.get('duration_formatted', 'Unknown'):<{max_duration_width}}"
            resolution_str = f"{video.get('resolution', 'Unknown'):<{max_resolution_width}}"
            codec_str = video.get('codec', 'Unknown')
            
            console.print(
                f"[green]{size_str}[/green] "
                f"[yellow]{duration_str}[/yellow] "
                f"[magenta]{resolution_str}[/magenta] "
                f"[blue]{codec_str:<8}[/blue] "
                f"[cyan]{video['name']}[/cyan]"
            )
        else:
            # Simple format: size filename (like ls -l)
            console.print(
                f"[green]{size_str}[/green] [cyan]{video['name']}[/cyan]"
            )


def list_videos(
    ctx: typer.Context,
    directory: Optional[Path] = typer.Argument(
        None,
        help="Directory to list video files from (default: current directory)",
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
    detailed: bool = typer.Option(
        False,
        "--list",
        "-l",
        help="Show detailed information including duration and resolution",
    ),
    recursive: bool = typer.Option(
        False,
        "--recursive",
        "-r",
        help="Search for video files recursively in subdirectories",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Output information in JSON format",
    ),
    table_format: bool = typer.Option(
        False,
        "--table",
        "-t",
        help="Use table format instead of ls-style output",
    ),
) -> None:
    """
    List all video files in the specified directory (or current directory).
    
    By default, shows files in ls-style format with colors. Use --table for table format.

    Examples:
        - List videos in current directory: vidio list (or vidio ls)
        - List with details: vidio list -l (or vidio ls -l)
        - Search recursively: vidio list --recursive
        - Get JSON output: vidio list --json
        - Use table format: vidio list --table
        - List videos in specific directory: vidio list /path/to/videos
    """
    # Get verbose flag from global context
    verbose = ctx.obj.get("VERBOSE", False) if ctx.obj else False

    # Use current directory if none specified
    target_dir = directory or Path.cwd()

    # Find video files
    video_files = []

    if recursive:
        # Search recursively
        for ext in VIDEO_EXTENSIONS:
            video_files.extend(target_dir.rglob(f"*{ext}"))
            video_files.extend(target_dir.rglob(f"*{ext.upper()}"))
    else:
        # Search only in the specified directory
        for ext in VIDEO_EXTENSIONS:
            video_files.extend(target_dir.glob(f"*{ext}"))
            video_files.extend(target_dir.glob(f"*{ext.upper()}"))

    # Remove duplicates and sort
    video_files = sorted(set(video_files))

    if not video_files:
        search_location = "recursively" if recursive else "in directory"
        console.print(
            f"[yellow]No video files found {search_location}: {target_dir}[/yellow]"
        )
        return

    # Prepare data for output
    video_data = []

    for video_file in video_files:
        file_stat = video_file.stat()
        file_info = {
            "name": video_file.name,
            "path": str(video_file),
            "size_bytes": file_stat.st_size,
            "size_formatted": format_size(file_stat.st_size),
        }

        # Get detailed info if requested or for default ls-style output
        if detailed or json_output or not table_format:
            video_info = get_video_info(video_file, verbose)
            if video_info:
                format_info = video_info.get("format", {})
                duration = float(format_info.get("duration", 0))
                file_info["duration_seconds"] = duration
                file_info["duration_formatted"] = format_duration(duration)

                # Find video stream for resolution
                video_streams = [
                    s
                    for s in video_info.get("streams", [])
                    if s.get("codec_type") == "video"
                ]
                if video_streams:
                    video_stream = video_streams[0]
                    width = video_stream.get("width", 0)
                    height = video_stream.get("height", 0)
                    file_info["width"] = width
                    file_info["height"] = height
                    file_info["resolution"] = (
                        f"{width}x{height}" if width and height else "Unknown"
                    )
                    file_info["codec"] = video_stream.get("codec_name", "Unknown")
                else:
                    file_info["resolution"] = "Unknown"
                    file_info["codec"] = "Unknown"
            else:
                file_info["duration_seconds"] = 0
                file_info["duration_formatted"] = "Unknown"
                file_info["resolution"] = "Unknown"
                file_info["codec"] = "Unknown"

        video_data.append(file_info)

    # Output results
    if json_output:
        console.print_json(json.dumps(video_data, indent=2))
        return

    # Use table format if explicitly requested
    if table_format:
        if detailed:
            table = Table(title=f"Video Files in {target_dir}")
            table.add_column("Name", style="cyan")
            table.add_column("Size", style="green")
            table.add_column("Duration", style="yellow")
            table.add_column("Resolution", style="magenta")
            table.add_column("Codec", style="blue")

            for video in video_data:
                table.add_row(
                    video["name"],
                    video["size_formatted"],
                    video.get("duration_formatted", "Unknown"),
                    video.get("resolution", "Unknown"),
                    video.get("codec", "Unknown"),
                )
        else:
            table = Table(title=f"Video Files in {target_dir}")
            table.add_column("Name", style="cyan")
            table.add_column("Size", style="green")

            for video in video_data:
                table.add_row(video["name"], video["size_formatted"])

        console.print(table)
    else:
        # Default ls-style output
        format_ls_output(video_data, verbose=detailed)

    console.print(f"\n[bold]Found {len(video_files)} video file(s)[/bold]")
