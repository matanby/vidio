# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`vidio-cli` is a Python-based CLI tool that provides a simple, user-friendly wrapper around ffmpeg for common video operations. It uses Typer for CLI framework and Rich for terminal output formatting.

## Development Setup

This project uses `uv` for package management:

```bash
# Install dependencies
uv sync

# Install with dev dependencies
uv sync --group dev

# Install in development mode (editable install)
uv pip install -e .
```

## Running Commands

```bash
# Run the CLI during development
uv run vidio <command>

# Or after installing in dev mode
vidio <command>

# Run tests
uv run pytest

# Run tests with verbose output
uv run pytest -v

# Run specific test file
uv run pytest tests/test_concat.py

# Lint with ruff
uv run ruff check .

# Format with ruff
uv run ruff format .
```

## Architecture

### Command Registration System

Commands are **dynamically discovered and registered** at startup via `src/vidio_cli/commands/__init__.py`:

1. The `get_commands()` function scans the `commands/` directory for Python modules
2. Each module with a `register()` function is treated as a command
3. Module names (with underscores) become command names (with hyphens), e.g., `to_gif.py` → `to-gif`
4. Commands are registered with the main Typer app in `src/vidio_cli/cli.py`

### Command Module Pattern

Each command module follows this structure:

```python
def register(app: typer.Typer) -> None:
    """Register the command with the Typer app."""
    app.command(no_args_is_help=True)(command_function)

def command_function(
    ctx: typer.Context,
    # ... command arguments and options
) -> None:
    """Command implementation."""
    verbose = ctx.obj.get("VERBOSE", False) if ctx.obj else False
    # ... command logic using ffmpeg_utils
```

### Shared Utilities

- **`ffmpeg_utils.py`**: Core utilities for running ffmpeg/ffprobe commands
  - `ensure_ffmpeg()`: Verifies ffmpeg is installed
  - `run_ffmpeg()`: Executes ffmpeg commands with error handling
  - `get_video_info()`: Retrieves video metadata using ffprobe
  - `check_output_file()`: Handles output file overwrite checks

- **`config.py`**: Default settings for video encoding (codec, quality, preset)

### Global Context

The verbose flag (`--verbose` / `-v`) is stored in the Typer context object and accessed by commands via `ctx.obj.get("VERBOSE", False)`.

## Adding a New Command

1. Create `src/vidio_cli/commands/<command_name>.py`
2. Implement the `register(app: typer.Typer)` function
3. Implement the command function with appropriate arguments/options
4. Use `ffmpeg_utils` functions for running ffmpeg operations
5. Access verbose flag from context: `verbose = ctx.obj.get("VERBOSE", False)`
6. Create corresponding test file: `tests/test_<command_name>.py`
7. The command will be automatically discovered and registered (no manual registration needed)

## Testing

Tests use pytest and should cover:
- Command registration
- Argument/option validation
- ffmpeg command generation (can mock `run_ffmpeg`)
- Error handling

Test videos can be placed in `tests/assets/` if needed.

## Dependencies

- **typer**: CLI framework with type annotations
- **rich**: Terminal formatting and colors
- **ffmpeg**: External dependency (must be in PATH)

## PyPI Release Workflow

Use this release flow for `vidio-cli`:

1. Update version in `pyproject.toml`.
2. Update `CHANGELOG.md` with the release date and notable changes.
3. Run quality checks locally:
   - `uv run ruff check .`
   - `uv run pytest -q`
4. Build and validate the distribution:
   - `uv build`
   - `python -m twine check dist/*`
5. Commit and tag:
   - `git tag v<version>`
   - `git push origin main --tags`
6. Publish:
   - Preferred: create a GitHub Release from the version tag; this triggers `.github/workflows/publish.yml` and publishes to PyPI.
   - Optional: run the publish workflow manually with `workflow_dispatch` to publish to TestPyPI first.

### Trusted Publishing Setup

The project should use PyPI Trusted Publishing with GitHub Actions:

- In PyPI/TestPyPI project settings, add a trusted publisher for this repository.
- Point it to workflow file `.github/workflows/publish.yml`.
- Restrict to the `main` branch and/or release tags as needed.
