"""Command module for displaying video file information."""

import json
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from vidio_cli.ffmpeg_utils import run_command

console = Console()


def register(app: typer.Typer) -> None:
    """
    Register the info command with the Typer app.

    Args:
        app: The Typer app to register the command with.
    """
    app.command(no_args_is_help=True)(info)


def count_frames(input_file: Path, verbose: bool = False) -> int:
    """
    Count the exact number of frames in a video file.

    Args:
        input_file: Path to the video file.
        verbose: If True, show ffmpeg commands and other debug info.

    Returns:
        int: The total number of frames.
    """
    console.print("Calculating exact frame count (this may take a while)...")

    # Use ffprobe to count frames accurately
    command = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-count_packets",
        "-show_entries",
        "stream=nb_read_packets",
        "-of",
        "csv=p=0",
        str(input_file),
    ]

    try:
        result = run_command(command, verbose=verbose, check=True, capture_output=True)
        frames = int(result.stdout.strip())
        return frames
    except (ValueError, TypeError):
        return 0


def info(
    ctx: typer.Context,
    input_file: Path = typer.Argument(
        ...,
        help="Input video file to display information for",
        exists=True,
        dir_okay=False,
        resolve_path=True,
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Output information in JSON format",
    ),
    exact_frames: bool = typer.Option(
        False,
        "--exact-frames",
        help="Calculate exact frame count (slower but accurate)",
    ),
) -> None:
    """
    Display detailed information about a video file.

    Examples:
        - Show video info in a nice table: vidio info video.mp4
        - Get JSON output for scripting: vidio info video.mp4 --json
        - Calculate exact frame count: vidio info video.mp4 --exact-frames
    """
    # Get verbose flag from global context
    verbose = ctx.obj.get("VERBOSE", False) if ctx.obj else False

    # Run ffprobe to get file information
    command = [
        "ffprobe",
        "-v",
        "quiet",
        "-print_format",
        "json",
        "-show_format",
        "-show_streams",
        str(input_file),
    ]

    try:
        result = run_command(command, verbose=verbose, check=True, capture_output=True)
        info_data = json.loads(result.stdout)
    except json.JSONDecodeError:
        console.print("[red]Error parsing ffprobe output.[/red]")
        raise typer.Exit(1)

    # Extract relevant information
    format_info = info_data.get("format", {})
    duration_seconds = float(format_info.get("duration", 0))
    file_size_bytes = int(format_info.get("size", 0))

    # Find video and audio streams
    video_streams = []
    audio_streams = []
    subtitle_streams = []

    for stream in info_data.get("streams", []):
        if stream.get("codec_type") == "video":
            video_streams.append(stream)
        elif stream.get("codec_type") == "audio":
            audio_streams.append(stream)
        elif stream.get("codec_type") == "subtitle":
            subtitle_streams.append(stream)

    # Calculate total frames if needed
    has_frame_count = False
    total_frames = 0

    if video_streams:
        # Try to get frame count from metadata first
        video = video_streams[0]
        if "nb_frames" in video and video["nb_frames"] not in ("N/A", "0"):
            total_frames = int(video["nb_frames"])
            has_frame_count = True

        # If metadata doesn't have frame count or exact count requested, calculate it
        if not has_frame_count or exact_frames:
            total_frames = count_frames(input_file, verbose)
            has_frame_count = True

            # Update the info_data for JSON output
            if video_streams:
                video_streams[0]["nb_frames"] = str(total_frames)

    # Format information nicely
    if json_output:
        # Just output the raw JSON for scripting
        console.print_json(json.dumps(info_data))
        return

    # Create pretty table output
    table = Table(title=f"Video Information: {input_file.name}")

    # General information
    table.add_section()
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")

    # Format human-readable duration
    hours, remainder = divmod(duration_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    duration_str = f"{int(hours):02d}:{int(minutes):02d}:{seconds:06.3f}"

    # Format human-readable file size
    size_mb = file_size_bytes / (1024 * 1024)

    table.add_row("Duration", duration_str)
    table.add_row("File Size", f"{size_mb:.2f} MB ({file_size_bytes:,} bytes)")
    table.add_row("Format", format_info.get("format_name", "Unknown"))
    table.add_row("Bit Rate", f"{int(format_info.get('bit_rate', 0)) / 1000:.2f} kbps")

    # Video stream information
    if video_streams:
        video = video_streams[0]  # Primary video stream

        table.add_section()
        table.add_row("Video Codec", video.get("codec_name", "Unknown"))

        # Resolution
        width = video.get("width", 0)
        height = video.get("height", 0)
        table.add_row("Resolution", f"{width}x{height}")

        # Frame rate
        frame_rate = "Unknown"
        if "r_frame_rate" in video:
            rate_parts = video["r_frame_rate"].split("/")
            if len(rate_parts) == 2 and int(rate_parts[1]) != 0:
                fps = float(rate_parts[0]) / float(rate_parts[1])
                frame_rate = f"{fps:.2f} fps"
        table.add_row("Frame Rate", frame_rate)

        # Always show total frames
        if has_frame_count:
            table.add_row("Total Frames", f"{total_frames:,}")

        # Pixel format
        table.add_row("Pixel Format", video.get("pix_fmt", "Unknown"))

        # Color information
        if "color_space" in video:
            table.add_row("Color Space", video.get("color_space"))

        # Bitrate for video
        if "bit_rate" in video:
            video_bitrate = int(video["bit_rate"]) / 1000
            table.add_row("Video Bitrate", f"{video_bitrate:.2f} kbps")

    # Audio stream information
    if audio_streams:
        audio = audio_streams[0]  # Primary audio stream

        table.add_section()
        table.add_row("Audio Codec", audio.get("codec_name", "Unknown"))
        table.add_row("Audio Channels", str(audio.get("channels", "Unknown")))

        # Sample rate
        sample_rate = audio.get("sample_rate")
        if sample_rate:
            table.add_row("Sample Rate", f"{int(sample_rate) / 1000:.1f} kHz")

        # Bitrate for audio
        if "bit_rate" in audio:
            audio_bitrate = int(audio["bit_rate"]) / 1000
            table.add_row("Audio Bitrate", f"{audio_bitrate:.2f} kbps")

    # Subtitle information
    if subtitle_streams:
        table.add_section()
        table.add_row("Subtitle Tracks", str(len(subtitle_streams)))
        for i, sub in enumerate(subtitle_streams):
            lang = sub.get("tags", {}).get("language", "Unknown")
            table.add_row(
                f"Subtitle {i + 1}", f"{sub.get('codec_name', 'Unknown')} ({lang})"
            )

    console.print(table)

    return
