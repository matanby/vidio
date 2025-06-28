"""Utilities for working with ffmpeg."""

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


def run_ffmpeg(
    command: list[str], quiet: bool = False, check: bool = True
) -> subprocess.CompletedProcess:
    """
    Run an ffmpeg command and handle output/errors.

    Args:
        command: List of command arguments, starting with ["ffmpeg", ...]
        quiet: If True, suppress all output except for errors.
        check: If True, raise an exception if the command fails.

    Returns:
        subprocess.CompletedProcess: The completed process.
    """
    ensure_ffmpeg()

    if not quiet:
        console.print(f"Running: [dim]{' '.join(command)}[/dim]")

    # Set up stdout/stderr redirection
    stdout = subprocess.PIPE if quiet else None
    stderr = subprocess.PIPE

    try:
        result = subprocess.run(
            command,
            stdout=stdout,
            stderr=stderr,
            text=True,
            check=check,
        )
        return result
    except subprocess.CalledProcessError as e:
        error_console.print("[bold red]Error:[/bold red] ffmpeg command failed")
        if e.stderr:
            error_console.print(e.stderr)
        raise typer.Exit(code=1)


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
