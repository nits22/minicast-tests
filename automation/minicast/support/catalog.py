"""The bundled sample catalog, used to data-drive the content tests."""
from __future__ import annotations

import json
from pathlib import Path

_DATA = json.loads((Path(__file__).parent / "catalog.json").read_text())

SHOWS: list[dict] = _DATA
SHOW_NAMES: list[str] = [s["show"] for s in _DATA]


def episodes(show: str) -> list[dict]:
    for s in _DATA:
        if s["show"] == show:
            return s["episodes"]
    raise KeyError(show)


def episode(show: str, duration: str) -> dict:
    """First episode of a given length, e.g. the 1:00 one used for seek tests."""
    for e in episodes(show):
        if e["duration"] == duration:
            return e
    raise KeyError(f"{show} has no {duration} episode")


# Episodes the tests reach for by name.
DAILY_BYTE = "The Daily Byte"
LONG = episode(DAILY_BYTE, "1:00")["title"]    # AI Writes Our Show Notes Now
MID = episode(DAILY_BYTE, "0:30")["title"]     # The Great Password Purge
SHORT = episode(DAILY_BYTE, "0:10")["title"]   # Zero-Day in the Coffee Machine
