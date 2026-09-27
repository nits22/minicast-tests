"""Settings and resume behaviour."""
from __future__ import annotations

import time

import allure
import pytest
from appium.webdriver.webdriver import WebDriver

from minicast.pages import Pages
from minicast.probes import PlaybackProbe
from minicast.support import catalog
from tests.conftest import covers


@allure.feature("Settings")
@allure.story("Persistence")
@covers("TC-0.5", "TC-5.7", "TC-5.8", "TC-5.9")
@pytest.mark.regression
def test_settings_survive_a_restart(pages: Pages, driver: WebDriver):
    """Change the three stored settings, restart, and check they held."""
    s = pages.settings
    pages.discover.open_settings()
    assert s.is_open()

    # Deliberately not asserting factory defaults here: `pm clear` is refused on the
    # test handset, so a guaranteed-clean profile is not available locally. Defaults
    # are covered by TC-0.5 after a reinstall. This test owns persistence.
    with allure.step("change all three stored settings"):
        before = (s.default_speed(), s.sleep_minutes(), s.notifications_enabled())
        s.set_speed_2x_sleep_1_notifications_off()
        changed = (s.default_speed(), s.sleep_minutes(), s.notifications_enabled())
        assert changed == ("2x", 1, False), f"settings did not apply: {changed} (was {before})"

    pkg = "com.audiomob.minicast"
    driver.terminate_app(pkg)
    driver.activate_app(pkg)
    pages.discover.open_settings()

    assert (s.default_speed(), s.sleep_minutes(), s.notifications_enabled()) == changed, \
        "settings were lost across a restart"


@allure.feature("Settings")
@allure.story("Resume")
@covers("TC-5.4", "TC-5.5")
@pytest.mark.xfail(strict=True,
                   reason="BUG-003: one global position is applied to whatever episode you open next")
@pytest.mark.regression
@pytest.mark.playback
@pytest.mark.known_bug
def test_resume_position_is_kept_per_episode(pages: Pages, probe: PlaybackProbe):
    """An episode you have never played should start at 0:00.

    Fails today: the position from the last episode is carried over, so a
    never-played 0:30 episode can open at its end. Strict, so it goes red when fixed.
    """
    pages.discover.open_show(catalog.DAILY_BYTE)
    pages.show.play(catalog.LONG)
    pages.show.open_now_playing()
    now = pages.now
    now.wait_for_position(12, timeout=35)
    now.pause()

    now.back()
    pages.show.play(catalog.MID)      # not played in this session
    pages.show.open_now_playing()
    time.sleep(2.5)                      # the label initialises at 0:00 before it syncs

    assert probe.position() <= 2, (
        f"a never-played episode opened at {probe.position():.0f}s instead of 0:00")
