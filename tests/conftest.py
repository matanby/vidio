"""Shared pytest helpers."""

import re

import pytest


ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-9;]*m")


@pytest.fixture
def clean_output():
    """Return a helper that strips ANSI color/style escape codes."""

    def _clean_output(text: str) -> str:
        return ANSI_ESCAPE_RE.sub("", text)

    return _clean_output
