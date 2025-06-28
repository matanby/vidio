"""CLI entry point for vidio - A simple ffmpeg wrapper."""

import typer
from rich.console import Console

from vidio_cli import __version__
from vidio_cli.commands import get_commands
from vidio_cli.ffmpeg_utils import ensure_ffmpeg

# Create Typer app
app = typer.Typer(
    help="A simple ffmpeg wrapper for common video operations",
    add_completion=False,  # No shell completion for now
    no_args_is_help=True,
)

console = Console()


def version_callback(value: bool) -> None:
    """Print the version of the package."""
    if value:
        console.print(f"[bold]vidio[/bold] version: {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    ctx: typer.Context,
    version: bool = typer.Option(
        False,
        "--version",
        "-V",
        help="Show the version and exit.",
        callback=version_callback,
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show ffmpeg commands and other debug info.",
    ),
) -> None:
    """
    A simple CLI tool to perform common video operations using ffmpeg.
    """
    # Check if ffmpeg is installed
    ensure_ffmpeg()

    # Store verbose flag in context for global access
    ctx.ensure_object(dict)
    ctx.obj["VERBOSE"] = verbose


# Dynamic command registration
commands = get_commands()
for name, register_func in commands.items():
    register_func(app)


if __name__ == "__main__":
    app()
