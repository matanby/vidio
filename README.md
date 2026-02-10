# vidio

**Stop Googling ffmpeg flags.** Just tell `vidio` what you want.

```bash
vidio trim long-meeting.mp4 highlight.mp4 --start 1:30 --duration 45
vidio resize raw-footage.mp4 web-ready.mp4 --width 1280
vidio to-gif funny-moment.mp4 reaction.gif --fps 15 --quality high
```

`vidio` is a CLI tool that wraps ffmpeg with sane defaults so you can trim, resize, crop, concatenate, and convert videos without memorizing arcane flags every single time.

---

## Install

Requires Python 3.10+ and [ffmpeg](https://ffmpeg.org/) in your PATH.

```bash
# Recommended — install as a standalone tool with uv
uv tool install vidio-cli

# Or run it directly without installing
uvx vidio-cli trim input.mp4 output.mp4 --start 10 --end 30

# Or if you prefer pip
pip install vidio-cli
```

Once installed, the `vidio` command is available globally.

---

## What's in the box

| Command | What it does |
|---------|-------------|
| `vidio ls` | Find video files in a directory |
| `vidio info` | Inspect metadata, codecs, resolution |
| `vidio trim` | Cut a clip by time range |
| `vidio resize` | Scale to target dimensions or percentage |
| `vidio crop` | Crop to aspect ratios like 16:9, 9:16, square |
| `vidio concat` | Place videos side-by-side or stacked |
| `vidio grid` | Build multi-video grid layouts |
| `vidio to-gif` | Convert clips to GIF with palette optimization |

That's it. No bloat, no kitchen-sink features. Just the things you actually do with video files on a regular basis.

---

## Usage

Every command has `--help`:

```bash
vidio --help
vidio trim --help
```

### Trim

```bash
# Cut from 30s to 1:30
vidio trim input.mp4 clip.mp4 --start 30 --end 1:30

# Take 45 seconds starting at 1:30
vidio trim input.mp4 clip.mp4 --start 1:30 --duration 45

# Chop off everything after 2:15
vidio trim input.mp4 clip.mp4 --end 2:15
```

### Resize

```bash
# Scale to a specific width (height calculated automatically)
vidio resize input.mp4 output.mp4 --width 1280

# Scale to 50%
vidio resize input.mp4 output.mp4 --scale 0.5

# Force exact dimensions (may distort)
vidio resize input.mp4 output.mp4 -w 1920 -h 1080 --force-aspect
```

### Crop

```bash
# Square crop, centered (great for Instagram)
vidio crop input.mp4 output.mp4 --preset center-square

# Vertical video for Reels/TikTok
vidio crop input.mp4 output.mp4 --preset 9:16

# Widescreen
vidio crop input.mp4 output.mp4 --preset 16:9

# Manual crop with offset
vidio crop input.mp4 output.mp4 -w 1280 -h 720 --x 100 --y 50
```

### Concat

```bash
# Side-by-side
vidio concat left.mp4 right.mp4 combined.mp4

# Stacked vertically
vidio concat top.mp4 bottom.mp4 combined.mp4 --vertical
```

### Grid

```bash
# Auto-arranged grid
vidio grid a.mp4 b.mp4 c.mp4 d.mp4 mosaic.mp4

# Explicit 2x2 with padding
vidio grid a.mp4 b.mp4 c.mp4 d.mp4 mosaic.mp4 --rows 2 --cols 2 --padding 10

# Custom cell size
vidio grid a.mp4 b.mp4 c.mp4 d.mp4 mosaic.mp4 --width 640 --height 360
```

### Convert to GIF

```bash
# Good defaults out of the box
vidio to-gif clip.mp4 output.gif

# Optimized for small file size
vidio to-gif clip.mp4 output.gif --scale 0.3 --fps 8 --quality low

# Specific time range
vidio to-gif clip.mp4 output.gif --start 10 --duration 5
```

### List & Info

```bash
# Quick ls-style listing
vidio ls

# Detailed view with duration, resolution, codec
vidio ls --list

# Recursive search
vidio ls --recursive

# JSON output (handy for scripting)
vidio ls --json

# Full metadata for a single file
vidio info video.mp4
vidio info video.mp4 --json
```

---

## Development

```bash
git clone https://github.com/matanb/vidio-cli.git
cd vidio-cli
uv sync --group dev

# Run tests
uv run pytest -q

# Lint
uv run ruff check .
```

## License

MIT
