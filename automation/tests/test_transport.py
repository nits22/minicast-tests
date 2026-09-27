"""Now Playing transport controls: skip, clamp and playback speed."""
from __future__ import annotations

import time

import allure
import pytest

from minicast.pages import Pages
from minicast.probes import PlaybackProbe
from minicast.support import catalog
from tests.conftest import covers


@allure.feature("Transport")
@allure.story("Skip and speed")
@covers("TC-4.1", "TC-4.2", "TC-4.3", "TC-4.11", "TC-4.12")
@pytest.mark.regression
@pytest.mark.playback
def test_skip_clamp_and_playback_speed(pages: Pages, probe: PlaybackProbe):
    """+15/-15 move exactly 15s, skipping past zero clamps, and 2x really doubles the rate."""
    pages.discover.open_show(catalog.DAILY_BYTE)
    pages.show.play(catalog.LONG)
    pages.show.open_now_playing()
    now = pages.now
    now.wait_for_position(3, timeout=25)
    now.pause()

    # The app carries a playback position between episodes (BUG-003), so the
    # starting point is not reliably 0:00. Clamp down first, which also proves
    # skip-back does not run past the start of the track.
    with allure.step("clamp at the start of the track"):
        for _ in range(6):
            now.skip_back()
        time.sleep(1.5)
        assert probe.position() < 2, f"expected clamp to 0:00, player is at {probe.position():.0f}s"
        assert now.position() == 0, f"label shows {now.position()}s after clamping"

    # Forward skip is covered separately - it is broken (BUG-005). The label can lag a
    # tap by a frame, so arithmetic is done against the player and the label is then
    # checked for agreement.
    with allure.step("skip back moves exactly 15s"):
        now.skip_forward()          # get off the floor so there is room to go back
        time.sleep(1.5)
        before = probe.position()
        now.skip_back()
        time.sleep(1.5)
        assert probe.position() == pytest.approx(before - 15, abs=2), (
            f"-15s went {before:.0f}s -> {probe.position():.0f}s")
        assert now.position() == pytest.approx(probe.position(), abs=2), "label disagrees with the player"

    with allure.step("2x doubles the rate, measured against wall clock"):
        assert now.set_speed("2x") == "2x"
        assert probe.speed() == pytest.approx(2.0, abs=0.01), (
            f"label says 2x but the player is at {probe.speed()}")
        # Pausing and reading take time, so the window is measured, not assumed.
        before = probe.position()
        started = time.monotonic()
        now.resume()
        time.sleep(12)
        now.pause()
        elapsed = time.monotonic() - started
        advanced = probe.position() - before
        assert advanced == pytest.approx(2 * elapsed, rel=0.25), (
            f"{elapsed:.0f}s of wall clock advanced {advanced:.0f}s of media; "
            f"expected ~{2 * elapsed:.0f}s at 2x")


@allure.feature("Transport")
@allure.story("Skip")
@covers("TC-4.1", "TC-4.5")
@pytest.mark.regression
@pytest.mark.playback
@pytest.mark.known_bug
@pytest.mark.xfail(strict=True, reason="BUG-005: the +15s control advances 30 seconds")
def test_skip_forward_moves_fifteen_seconds(pages: Pages, probe: PlaybackProbe):
    """The control is labelled +15s and should move 15s. It moves 30s.

    Skip back is correct, so the two controls are asymmetric - you cannot undo a
    forward skip with a back skip.
    """
    pages.discover.open_show(catalog.DAILY_BYTE)
    pages.show.play(catalog.LONG)
    pages.show.open_now_playing()
    now = pages.now
    now.wait_for_position(3, timeout=25)
    now.pause()

    for _ in range(6):
        now.skip_back()
    time.sleep(1.5)
    assert probe.position() < 2, "could not get to the start of the track"

    now.skip_forward()
    time.sleep(1.5)
    assert probe.position() == pytest.approx(15, abs=2), (
        f"+15s from 0:00 landed on {probe.position():.0f}s")
