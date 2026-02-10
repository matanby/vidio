# vidio-cli

A simple and easy-to-use ffmpeg wrapper for common video operations.

## Features

- **Stupidly Easy:** Simple CLI commands for common video operations.
- **Powerful Defaults:** Sensible defaults make it work great out of the box.
- **Focused v1 Scope:** Core commands people use repeatedly, without feature bloat.

## Requirements

- Python 3.10+
- ffmpeg (must be installed and in your PATH)

## v1 Command Scope

`vidio-cli` 0.1.0 intentionally focuses on practical, high-frequency tasks:

- `list` / `ls`: find video files quickly
- `info`: inspect metadata and streams
- `trim`: cut clips by time range
- `resize`: scale for delivery targets
- `crop`: convert to target aspect ratios
- `concat`: place videos side-by-side or stacked
- `grid`: build multi-video collages
- `to-gif`: convert clips to GIF with good defaults

Commands that are less consistently useful (for example, niche one-off transforms) are deferred to later releases.

## Installation

```bash
# Using pip
pip install vidio-cli

# Using uv
uv pip install vidio-cli
```

## Usage

```bash
# Get help
vidio --help

# Get help for a specific command
vidio concat --help
```

### Concatenate Videos

```bash
# Concatenate videos horizontally
vidio concat video1.mp4 video2.mp4 output.mp4

# Concatenate videos vertically
vidio concat video1.mp4 video2.mp4 output.mp4 --vertical
```

### List Video Files

```bash
# List videos in current directory (ls-style output)
vidio list
# or use the shorter alias
vidio ls

# List with detailed information (duration, resolution, codec)
vidio ls --list

# Search recursively in subdirectories
vidio ls --recursive

# Use table format instead of ls-style
vidio ls --table

# Get JSON output for scripting
vidio ls --json
```

### Video Information

```bash
# Display detailed metadata about a video file
vidio info video.mp4

# Get machine-readable JSON output
vidio info video.mp4 --json

# Calculate exact frame count (slower but accurate)
vidio info video.mp4 --exact-frames
```

### Create Video Grids

```bash
# Arrange videos in a 2x2 grid (auto-calculated)
vidio grid video1.mp4 video2.mp4 video3.mp4 video4.mp4 output.mp4

# Specify grid dimensions
vidio grid video1.mp4 video2.mp4 video3.mp4 video4.mp4 output.mp4 --rows 2 --cols 2

# Control cell size and add padding
vidio grid video1.mp4 video2.mp4 video3.mp4 video4.mp4 output.mp4 --width 640 --height 360 --padding 10

# Change background color
vidio grid video1.mp4 video2.mp4 video3.mp4 video4.mp4 output.mp4 --background white
```

### Trim Videos

```bash
# Trim from 30 seconds to 90 seconds
vidio trim input.mp4 output.mp4 --start 30 --end 90

# Trim from 1:30 for 45 seconds duration
vidio trim input.mp4 output.mp4 --start 1:30 --duration 45

# Trim from beginning to 2:15
vidio trim input.mp4 output.mp4 --end 2:15

# Trim using different time formats
vidio trim input.mp4 output.mp4 --start 0:01:30 --end 0:02:45
```

### Resize Videos

```bash
# Resize to specific dimensions (maintains aspect ratio)
vidio resize input.mp4 output.mp4 --width 1920 --height 1080

# Scale by percentage
vidio resize input.mp4 output.mp4 --scale 0.5  # 50% of original size

# Resize width only (height auto-calculated)
vidio resize input.mp4 output.mp4 --width 1280

# Resize height only (width auto-calculated)  
vidio resize input.mp4 output.mp4 --height 720

# Force exact dimensions (may distort)
vidio resize input.mp4 output.mp4 -w 1920 -h 1080 --force-aspect
```

### Convert to GIF

```bash
# Basic conversion with optimized palette
vidio to-gif video.mp4 output.gif

# High quality with custom frame rate
vidio to-gif video.mp4 output.gif --fps 15 --quality high

# Small file size for web
vidio to-gif video.mp4 output.gif --scale 0.3 --fps 8 --quality low

# Convert specific time range
vidio to-gif video.mp4 output.gif --start 10 --duration 5

# Custom width with different dithering
vidio to-gif video.mp4 output.gif --width 800 --dither bayer

# Fast conversion (skip optimization)
vidio to-gif video.mp4 output.gif --no-optimize
```

### Crop Videos

```bash
# Crop to center square (perfect for Instagram)
vidio crop input.mp4 output.mp4 --preset center-square

# Crop to 16:9 aspect ratio
vidio crop input.mp4 output.mp4 --preset 16:9

# Crop to 9:16 aspect ratio (vertical/portrait)
vidio crop input.mp4 output.mp4 --preset 9:16

# Crop to 4:3 aspect ratio
vidio crop input.mp4 output.mp4 --preset 4:3

# Custom crop region (centered)
vidio crop input.mp4 output.mp4 --width 1280 --height 720

# Custom crop with specific position
vidio crop input.mp4 output.mp4 -w 1280 -h 720 --x 100 --y 50
```


## Development

```bash
# Clone the repo
git clone https://github.com/matanb/vidio-cli.git
cd vidio-cli

# Install dependencies
uv sync --group dev

# Run tests
uv run pytest -q

# Run lint
uv run ruff check .
```

## License

MIT
