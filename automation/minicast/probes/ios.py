"""iOS probe. Never exercised: there is no iOS build.

XCUITest cannot read MPNowPlayingInfoCenter from outside the app, so the session
signals have no iOS equivalent. Rather than fake them, the probe skips, and any
test that needs them is skipped on iOS with a clear reason.
"""
from __future__ import annotations

import pytest

_REASON = "no external playback probe on iOS; assert via the Now Playing UI instead"


class IOSProbe:
    def state(self) -> str:
        pytest.skip(_REASON)

    def position(self) -> float:
        pytest.skip(_REASON)

    def speed(self) -> float:
        pytest.skip(_REASON)

    def audio_active(self) -> bool:
        pytest.skip(_REASON)

    def frames_written(self) -> int | None:
        return None
