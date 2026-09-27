"""Turning run options into a running Appium session.

Everything about capabilities lives here rather than in conftest, so the fixture
stays a fixture and this stays testable without a device.
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path

import yaml
from appium import webdriver
from appium.options.common import AppiumOptions
from appium.webdriver.webdriver import WebDriver
from selenium.common.exceptions import WebDriverException

from minicast.devices import Device, for_worker
from minicast.support import adb

log = logging.getLogger(__name__)
CONFIG_DIR = Path(__file__).parent.parent / "config"


@dataclass(frozen=True)
class SessionConfig:
    platform: str = "android"
    appium_url: str = "http://127.0.0.1:4723"
    app: str | None = None
    device: str | None = None      # serial, model substring, "virtual" or "real"
    no_install: bool = False
    worker: int = 0                # xdist worker index; offsets the helper ports


def _base_capabilities(platform: str) -> dict:
    path = CONFIG_DIR / f"{platform}.yaml"
    if not path.exists():
        raise ValueError(f"no capability file for platform {platform!r} at {path}")
    return yaml.safe_load(path.read_text())


def build_capabilities(cfg: SessionConfig, device: Device | None,
                       worker: int = 0) -> dict:
    """The full capability set, with nothing decided later.

    `worker` offsets the helper ports so parallel sessions do not collide.
    """
    caps = _base_capabilities(cfg.platform)

    if device is not None:
        caps["appium:udid"] = device.serial
        if device.release:
            caps["appium:platformVersion"] = device.release
        if device.model:
            caps["appium:deviceName"] = device.model

    if cfg.no_install:
        caps["appium:noReset"] = True          # reuse whatever is installed
    elif cfg.app:
        caps["appium:app"] = cfg.app           # .apk, or .app / .ipa on iOS

    # Each concurrent session needs its own helper ports, or the second one
    # fails to start on a port the first is already holding.
    if cfg.platform == "android":
        caps["appium:systemPort"] = 8200 + worker
        caps["appium:mjpegServerPort"] = 7810 + worker
    else:
        caps["appium:wdaLocalPort"] = 8100 + worker

    return caps


def create_driver(cfg: SessionConfig) -> tuple[WebDriver, Device]:
    """Resolve the device and open a session.

    Resolving here rather than letting Appium choose means the run says which
    device it used, and on Android that adb and Appium cannot drift apart.
    """
    device = for_worker(cfg.device, cfg.platform, cfg.worker)
    log.info("worker %s targeting %s", cfg.worker, device)
    if cfg.platform == "android":
        # Appium takes the device from a capability while the probe shells out to
        # adb. Exporting the resolved serial keeps both on the same handset - and
        # with more than one device attached, an unpinned `adb shell` is ambiguous,
        # so this has to happen before anything else touches adb.
        os.environ["ANDROID_SERIAL"] = device.serial
        adb.keep_awake(True)
        adb.wake()

    caps = build_capabilities(cfg, device, cfg.worker)

    def connect(capabilities: dict) -> WebDriver:
        return webdriver.Remote(cfg.appium_url,
                                options=AppiumOptions().load_capabilities(capabilities))

    try:
        driver = connect(caps)
    except WebDriverException as exc:
        # Some manufacturer builds refuse `pm clear`, which Appium runs as part of
        # its reset, and the session then cannot start at all. Reuse the installed
        # build rather than letting every test error at setup.
        if "CLEAR_APP_USER_DATA" not in str(exc):
            raise
        log.warning("device refuses `pm clear`; retrying with noReset "
                    "(state is not wiped between runs - see TEST-ENV-001)")
        caps.pop("appium:app", None)
        caps["appium:noReset"] = True
        driver = connect(caps)

    driver.implicitly_wait(0)      # explicit waits only
    return driver, device
