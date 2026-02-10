"""CLI smoke tests."""

import pytest
from typer.testing import CliRunner

from vidio_cli import __version__
from vidio_cli.cli import app
from vidio_cli.commands import get_commands
from vidio_cli.ffmpeg_utils import check_ffmpeg

runner = CliRunner()


def test_dynamic_command_registration():
    """Ensure expected commands are discovered dynamically."""
    commands = get_commands()
    expected = {
        "concat",
        "crop",
        "grid",
        "info",
        "list",
        "resize",
        "to-gif",
        "trim",
    }
    assert expected.issubset(commands.keys())


@pytest.mark.skipif(not check_ffmpeg(), reason="ffmpeg is not available")
def test_version_flag():
    """Ensure top-level version output works."""
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.stdout
