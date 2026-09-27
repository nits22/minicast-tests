from __future__ import annotations

import logging
import os
import subprocess
import time
from pathlib import Path

import allure
import pytest
from selenium.common.exceptions import WebDriverException

from minicast.driver import SessionConfig, create_driver
from minicast.pages import Pages, build_pages, check_locator_parity
from minicast.probes import probe_for
from minicast.support import adb

ROOT = Path(__file__).parent
log = logging.getLogger(__name__)


def pytest_addoption(parser):
    parser.addoption("--platform", default=os.getenv("PLATFORM", "android"),
                     help="android | ios")
    parser.addoption("--appium", default=os.getenv("APPIUM_URL", "http://127.0.0.1:4723"))
    parser.addoption("--app", default=os.getenv("MINICAST_APK", str(ROOT / "app" / "minicast-release.apk")))
    parser.addoption("--device", default=os.getenv("ANDROID_SERIAL"),
                     help="serial, model substring, 'virtual' or 'real'. "
                          "Comma-separate several to spread a -n run across them. "
                          "With one device connected it can be omitted.")
    parser.addoption("--no-install", action="store_true",
                     help="use the build already on the device instead of reinstalling "
                          "(faster locally; CI always installs)")


@pytest.fixture(scope="session")
def platform(request) -> str:
    return request.config.getoption("--platform").lower()


@pytest.fixture(scope="session", autouse=True)
def _locator_parity():
    """Fail fast if a page defines a locator on one platform but not the other."""
    check_locator_parity()


@pytest.fixture(scope="session")
def worker_index(request) -> int:
    """0 for a serial run, 0..n-1 under xdist (gw0, gw1, ...)."""
    wid = getattr(request.config, "workerinput", {}).get("workerid", "gw0")
    digits = "".join(c for c in wid if c.isdigit())
    return int(digits or 0)


@pytest.fixture(scope="session")
def driver(request, platform, worker_index):
    cfg = SessionConfig(
        platform=platform,
        appium_url=request.config.getoption("--appium"),
        app=request.config.getoption("--app"),
        device=request.config.getoption("--device"),
        no_install=request.config.getoption("--no-install"),
        worker=worker_index,
    )
    drv, device = create_driver(cfg)
    request.session.minicast_device = device
    yield drv
    drv.quit()
    if platform == "android":
        adb.keep_awake(False)


@pytest.fixture(scope="session")
def target_device(request, driver):
    """The device this worker resolved. Depends on driver so resolution happened."""
    return request.session.minicast_device


@pytest.fixture(autouse=True)
def _label_device(request):
    """Put the device on every Allure result.

    xdist captures worker logs, so a parallel run otherwise gives no clue which
    device a given test ran on.
    """
    device = getattr(request.session, "minicast_device", None)
    if device is not None:
        # Not `host`: Allure sets that to the machine name and overwrites ours.
        allure.dynamic.label("device", device.model or device.serial)
        allure.dynamic.label("serial", device.serial)


@pytest.fixture
def app(driver, platform):
    """Restart the app between tests so no test inherits the last one's state.

    terminate/activate is used rather than adb so the same fixture works on iOS.
    """
    pkg = "com.audiomob.minicast"
    driver.terminate_app(pkg)
    time.sleep(0.8)
    driver.activate_app(pkg)
    time.sleep(2.5)
    yield driver


def _reset_to_discover(discover, driver, attempts: int = 5) -> None:
    """Land every test on Discover.

    Relaunching does not guarantee it: the app restores the screen it was last on,
    and on this handset `pm clear` is refused by the OS so Appium cannot wipe state
    between sessions either. Walk back instead.
    """
    for _ in range(attempts):
        if discover.exists("search_field", timeout=4):
            return
        try:
            driver.back()
        except WebDriverException:          # no back stack left
            break
        time.sleep(0.6)
    raise AssertionError("could not get back to Discover before the test started")


@pytest.fixture
def pages(app, platform) -> Pages:
    built = build_pages(app, platform)
    _reset_to_discover(built.discover, app)
    return built


@pytest.fixture(scope="session")
def probe(platform):
    return probe_for(platform)


# ---------------------------------------------------------------- reporting
@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if report.when != "call" or not report.failed:
        return
    drv = item.funcargs.get("driver")
    if drv is None:
        return
    try:
        allure.attach(drv.get_screenshot_as_png(), "screenshot", allure.attachment_type.PNG)
        allure.attach(drv.page_source, "page-source", allure.attachment_type.XML)
    except WebDriverException as exc:          # a dead session still leaves a useful report
        log.warning("could not attach screenshot/page source: %s", exc)
    if item.config.getoption("--platform").lower() == "android":
        try:
            allure.attach(adb.logcat_dump()[-40000:], "logcat", allure.attachment_type.TEXT)
        except (OSError, subprocess.SubprocessError) as exc:
            log.warning("could not attach logcat: %s", exc)
