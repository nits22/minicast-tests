"""Core playback: start, pause, resume, and what the platform is told about it."""
from __future__ import annotations

import time

import allure
import pytest

from minicast.pages import NowPlaying, Pages
from minicast.probes import PlaybackProbe
from minicast.support import catalog
from tests.conftest import covers


def start_long(pages: Pages) -> NowPlaying:
    """Play the 1:00 episode and land on Now Playing."""
    pages.discover.open_show(catalog.DAILY_BYTE)
    pages.show.play(catalog.LONG)
    pages.show.open_now_playing()
    return pages.now


@allure.feature("Playback")
@allure.story("Play, pause, resume")
@covers("TC-0.3", "TC-3.1", "TC-3.2", "TC-3.3", "TC-3.10")
@pytest.mark.smoke
@pytest.mark.regression
@pytest.mark.playback
def test_play_pause_and_resume(pages: Pages, probe: PlaybackProbe):
    """Full journey: audio starts, metadata is right, pause freezes, resume carries on."""
    now = start_long(pages)

    with allure.step("metadata and duration"):
        assert now.episode_title() == catalog.LONG
        assert now.show_title() == catalog.DAILY_BYTE
        assert now.duration() == 60

    # The app carries a position between episodes (BUG-003), so this episode can
    # open near its end and finish mid-test. Wind back before measuring anything.
    now.pause()
    for _ in range(6):
        now.skip_back()
    now.resume()

    with allure.step("playback actually starts"):
        now.wait_for_position(3, timeout=20)
        first = now.position()
        time.sleep(4)
        assert now.position() > first, "position label is not advancing"
        assert probe.state() == "PLAYING"
        # Raises with both readings if they never converge.
        now.wait_until_agrees(probe)
        assert probe.audio_active(), "no active audio player - the UI is ticking without sound"

    with allure.step("pause freezes the position"):
        now.pause()
        paused_at = now.position()
        time.sleep(5)
        assert now.position() == paused_at, (
            f"position moved from {paused_at}s to {now.position()}s while paused")

    with allure.step("resume continues from there, not from zero"):
        now.resume()
        now.wait_for_position(paused_at + 2, timeout=15)
        assert now.position() >= paused_at


@allure.feature("Playback")
@allure.story("Media session")
@covers("TC-3.2", "TC-7.3")
@pytest.mark.android_only
@pytest.mark.xfail(strict=True,
                   reason="BUG-001: in-app pause leaves the media session reporting PLAYING")
@pytest.mark.regression
@pytest.mark.playback
@pytest.mark.known_bug
def test_pause_is_reported_to_the_system(pages: Pages, probe: PlaybackProbe):
    """Pausing in the app should tell the platform, so the lock screen agrees.

    Only the notification and media-key routes update session state today.
    Strict, so this goes red the day BUG-001 is fixed.
    """
    now = start_long(pages)
    now.wait_for_position(5, timeout=25)
    now.pause()
    time.sleep(2)
    assert probe.state() == "PAUSED", f"session still reports {probe.state()}"
