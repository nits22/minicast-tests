"""Playback outside the app: backgrounding and the media notification."""
from __future__ import annotations

import time

import allure
import pytest
from appium.webdriver.webdriver import WebDriver
from selenium.common.exceptions import WebDriverException

from minicast.pages import Pages
from minicast.probes import PlaybackProbe
from minicast.support import catalog
from tests.conftest import covers


@allure.feature("Background playback")
@allure.story("Backgrounding and notification")
@covers("TC-0.4", "TC-7.1", "TC-7.2", "TC-7.3")
@pytest.mark.android_only
@pytest.mark.smoke
@pytest.mark.regression
@pytest.mark.playback
def test_playback_survives_backgrounding_and_the_notification_controls_it(pages: Pages, driver: WebDriver, probe: PlaybackProbe):
    """Background the app - audio keeps going - then pause from the shade and check the app agrees."""
    pages.discover.open_show(catalog.DAILY_BYTE)
    pages.show.play(catalog.LONG)
    pages.show.open_now_playing()
    now = pages.now
    now.wait_for_position(3, timeout=20)

    with allure.step("audio continues while backgrounded"):
        before = probe.position()
        driver.background_app(8)        # cross-platform: home, wait, foreground
        after = probe.position()
        assert probe.state() == "PLAYING", f"playback stopped in the background ({probe.state()})"
        assert after > before + 4, f"position only moved {after - before:.0f}s while backgrounded"
        assert probe.audio_active(), "no active audio player while backgrounded"
        assert now.position() >= int(after) - 2, "UI did not resync to the current position"

    with allure.step("pause from the notification"):
        driver.open_notifications()
        time.sleep(2)
        try:
            control = driver.find_element("accessibility id", "Pause")
        except WebDriverException:
            pytest.fail("no Pause control in the media notification")
        control.click()
        time.sleep(2)
        driver.press_keycode(4)         # back, closes the shade
        time.sleep(1.5)

    assert probe.state() != "PLAYING", "notification pause did not stop playback"
    assert now.is_paused(), "in-app control still shows Pause after a notification pause"
