# vidio-cli

A simple and easy-to-use ffmpeg wrapper for common video operations.

## Features

- **Stupidly Easy:** Simple CLI commands for common video operations.
- **Powerful Defaults:** Sensible defaults make it work great out of the box.
- **Extensible:** New commands can be easily added.

## Requirements

- Python 3.10+
- ffmpeg (must be installed and in your PATH)

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

### More Commands Coming Soon

- `grid`: Arrange videos in a grid
- `to-gif`: Convert a video to GIF
- `extract-audio`: Extract audio from video
- `screenshot`: Take a screenshot at a specific time
- `resize`: Resize a video
- `crop`: Crop a video
- `info`: Show video metadata
- ...and more!

## Development

```bash
# Clone the repo
git clone https://github.com/yourusername/vidio-cli.git
cd vidio-cli

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest
```

## License

MIT
