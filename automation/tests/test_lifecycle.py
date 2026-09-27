"""Configuration changes. Rotating the app rebuilds the screen from scratch."""
from __future__ import annotations

import time

import allure
import pytest
from appium.webdriver.webdriver import WebDriver

from minicast.pages import Pages
from minicast.probes import PlaybackProbe
from minicast.support import catalog
from tests.conftest import covers


@allure.feature("Lifecycle")
@allure.story("Rotation")
@covers("TC-9.1", "TC-9.2")
@pytest.mark.regression
@pytest.mark.playback
def test_rotation_during_playback_keeps_state_and_audio(pages: Pages, driver: WebDriver, probe: PlaybackProbe):
    """Rotate mid-playback: audio must not stop and the screen must come back intact."""
    pages.discover.open_show(catalog.DAILY_BYTE)
    pages.show.play(catalog.LONG)
    pages.show.open_now_playing()
    now = pages.now

    # The app carries a position between episodes (BUG-003), so an episode can open
    # near its end and finish mid-test. Wind back to the start first.
    now.pause()
    for _ in range(6):
        now.skip_back()
    now.resume()
    now.wait_for_position(5, timeout=25)

    before_state = probe.state()
    before_pos = probe.position()
    original = driver.orientation

    assert now.duration() == 60, "wrong episode before rotating"

    try:
        with allure.step("rotate to landscape"):
            driver.orientation = "LANDSCAPE"
            time.sleep(2.5)
            assert probe.state() == before_state, "playback state changed on rotation"
            assert probe.position() >= before_pos, "playback restarted on rotation"
            assert now.episode_title() == catalog.LONG, "episode metadata lost on rotation"
            # Deliberately not asserting on the lower controls here. Landscape clips
            # them and the screen does not scroll (BUG-012), and how much is lost
            # depends on screen height - so requiring them would make this test a
            # layout test that passes or fails by device. Layout is TC-9.3's job.

        with allure.step("rotate back to portrait"):
            driver.orientation = "PORTRAIT"
            time.sleep(2.5)
            assert now.episode_title() == catalog.LONG
            assert now.duration() == 60, "duration lost after rotating back"
            assert probe.state() == before_state
            assert probe.audio_active(), "audio stopped across the rotation"
    finally:
        driver.orientation = original
