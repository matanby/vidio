"""Configuration defaults for vidio-cli."""

from typing import Any

# Default settings
DEFAULTS = {
    # General settings
    "quiet": False,
    # Common ffmpeg options
    "video_codec": "libx264",
    "audio_codec": "aac",
    "crf": 23,  # Video quality (lower = better)
    "preset": "medium",  # Encoding speed/compression tradeoff
}


def get_default(key: str) -> Any:
    """
    Get a default configuration value.

    Args:
        key: The configuration key.

    Returns:
        The configuration value.
    """
    return DEFAULTS.get(key)
