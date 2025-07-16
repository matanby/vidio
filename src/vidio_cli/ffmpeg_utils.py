"""Utilities for working with ffmpeg."""

import json
import shutil
import subprocess
from pathlib import Path

import typer
from rich.console import Console

console = Console()
error_console = Console(stderr=True)


def check_ffmpeg() -> bool:
    """
    Check if ffmpeg is available on the system.

    Returns:
        bool: True if ffmpeg is available, False otherwise.
    """
    return shutil.which("ffmpeg") is not None


def ensure_ffmpeg():
    """
    Ensure that ffmpeg is available, or exit with an error message.
    """
    if not check_ffmpeg():
        error_console.print("[bold red]Error:[/bold red] ffmpeg not found in PATH")
        error_console.print("Please install ffmpeg and make sure it's in your PATH.")
        error_console.print(
            "Installation instructions: https://ffmpeg.org/download.html"
        )
        raise typer.Exit(code=1)


def run_command(
    command: list[str],
    verbose: bool = False,
    check: bool = True,
    capture_output: bool = True,
) -> subprocess.CompletedProcess:
    """
    Run a command and handle output/errors in a unified way.

    Args:
        command: List of command arguments.
        verbose: If True, print the command and show output.
        check: If True, raise an exception if the command fails.
        capture_output: If True, capture stdout/stderr. If False and verbose is True,
                       output will be shown in real-time.

    Returns:
        subprocess.CompletedProcess: The completed process.
    """
    if verbose:
        console.print(f"Running: [dim]{' '.join(command)}[/dim]")

    # Determine stdout/stderr handling
    if capture_output:
        stdout = subprocess.PIPE
        stderr = subprocess.PIPE
    elif verbose:
        # Show output in real-time when verbose and not capturing
        stdout = None
        stderr = None
    else:
        # Capture but don't show when not verbose
        stdout = subprocess.PIPE
        stderr = subprocess.PIPE

    try:
        result = subprocess.run(
            command,
            stdout=stdout,
            stderr=stderr,
            text=True,
            check=check,
        )

        # If verbose and we captured output, show it
        if verbose and capture_output:
            if result.stdout:
                console.print(result.stdout)
            if result.stderr:
                console.print(result.stderr, style="red")

        return result
    except subprocess.CalledProcessError as e:
        error_console.print(f"[bold red]Error:[/bold red] {command[0]} command failed")
        if e.stderr:
            error_console.print(e.stderr)
        raise typer.Exit(code=1)


def get_video_info(file_path: Path, verbose: bool = False) -> dict:
    """
    Get video information using ffprobe.

    Args:
        file_path: Path to the video file.
        verbose: If True, show ffprobe commands and other debug info.

    Returns:
        dict: The video information as a dictionary.
    """
    ensure_ffmpeg()  # ffprobe is part of ffmpeg installation
    command = [
        "ffprobe",
        "-v",
        "quiet",
        "-print_format",
        "json",
        "-show_format",
        "-show_streams",
        str(file_path),
    ]

    try:
        result = run_command(command, verbose=verbose, check=True, capture_output=True)
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        error_console.print(
            "[bold red]Error:[/bold red] Failed to parse ffprobe output."
        )
        raise typer.Exit(code=1)


def run_ffmpeg(
    command: list[str], verbose: bool = False, check: bool = True
) -> subprocess.CompletedProcess:
    """
    Run an ffmpeg command and handle output/errors.

    Args:
        command: List of command arguments, starting with ["ffmpeg", ...]
        verbose: If True, print the command and show ffmpeg output.
        check: If True, raise an exception if the command fails.

    Returns:
        subprocess.CompletedProcess: The completed process.
    """
    ensure_ffmpeg()

    # For ffmpeg, we typically don't want to capture output when verbose
    # so users can see progress in real-time
    capture_output = not verbose
    return run_command(
        command, verbose=verbose, check=check, capture_output=capture_output
    )


def check_output_file(output_file: Path, force_overwrite: bool = False) -> bool:
    """
    Check if an output file exists and prompt for overwrite if needed.

    Args:
        output_file: Path to the output file.
        force_overwrite: If True, overwrite without prompting.

    Returns:
        bool: True if it's safe to write to the file, False otherwise.
    """
    if not output_file.exists():
        return True

    if force_overwrite:
        return True

    overwrite = typer.confirm(
        f"Output file {output_file} already exists. Overwrite?", default=False
    )
    return overwrite
