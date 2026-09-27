"""What a test is allowed to ask about playback, regardless of platform."""
from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class PlaybackProbe(Protocol):
    """Playback truth from outside the app's own UI.

    Tests depend on this, never on adb. iOS has no external equivalent of the
    Android media session, so its implementation skips the calls it cannot answer.
    """

    def state(self) -> str:
        """PLAYING | PAUSED | STOPPED | BUFFERING | NONE."""

    def position(self) -> float:
        """Seconds into the current track."""

    def speed(self) -> float:
        ...

    def audio_active(self) -> bool:
        """True when the platform has a player actively writing to the audio output."""

    def frames_written(self) -> int | None:
        """Audio frames delivered to the sink, or None when unavailable."""
