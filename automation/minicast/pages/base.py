from __future__ import annotations

import time
from typing import ClassVar

from appium.webdriver.common.appiumby import AppiumBy as By
from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException,
    WebDriverException,
)
from selenium.webdriver.support.ui import WebDriverWait

TIMEOUT = 15
POLL = 0.3


# --- locator builders -------------------------------------------------------
# Android: Compose test tags surface as *bare* resource-ids, which AppiumBy.ID
# cannot match (it qualifies the name with the package first). UiSelector does a
# plain string match and is cheaper than the XPath equivalent.
def test_tag(name: str) -> tuple[str, str]:
    return (By.ANDROID_UIAUTOMATOR, f'new UiSelector().resourceId("{name}")')


def accessibility_id(name: str) -> tuple[str, str]:
    """contentDescription on Android, accessibilityIdentifier on iOS."""
    return (By.ACCESSIBILITY_ID, name)


class BasePage:
    """Locators live on the page that owns them.

    Each page declares LOCATORS as {platform: {logical name: locator}}. Anything
    every screen shares sits in COMMON. `check_locator_parity` fails the run if a
    page defines a name on one platform and not the other.
    """

    COMMON: ClassVar[dict[str, dict[str, tuple[str, str]]]] = {
        "android": {"back_button": test_tag("backButton")},
        "ios": {"back_button": accessibility_id("backButton")},
    }
    LOCATORS: ClassVar[dict[str, dict[str, tuple[str, str]]]] = {"android": {}, "ios": {}}

    def __init__(self, driver, platform: str = "android"):
        self.driver = driver
        self.platform = platform
        self.loc = {**self.COMMON.get(platform, {}), **self.LOCATORS.get(platform, {})}

    # ---- element access -------------------------------------------------
    def _by(self, name: str):
        try:
            return self.loc[name]
        except KeyError:
            raise KeyError(f"{type(self).__name__} has no locator {name!r} for {self.platform}") from None

    def find(self, name: str, timeout: float = TIMEOUT):
        by, value = self._by(name)
        return WebDriverWait(self.driver, timeout, POLL).until(
            lambda d: d.find_element(by, value), f"{name} not present within {timeout}s"
        )

    def exists(self, name: str, timeout: float = 3) -> bool:
        try:
            self.find(name, timeout)
            return True
        except (TimeoutException, WebDriverException):
            return False

    def tap(self, name: str, timeout: float = TIMEOUT):
        self.find(name, timeout).click()

    def text(self, name: str, timeout: float = TIMEOUT) -> str:
        return self.find(name, timeout).text

    # ---- text-based access ----------------------------------------------
    def has_text(self, value: str, timeout: float = 3) -> bool:
        end = time.time() + timeout
        while time.time() < end:
            if self._text_element(value) is not None:
                return True
            time.sleep(POLL)
        return False

    def _text_element(self, value: str):
        by, sel = (
            (By.ANDROID_UIAUTOMATOR, f'new UiSelector().text("{value}")')
            if self.platform == "android"
            else (By.ACCESSIBILITY_ID, value)
        )
        try:
            return self.driver.find_element(by, sel)
        except (NoSuchElementException, StaleElementReferenceException):
            return None

    def tap_row(self, value: str, timeout: float = TIMEOUT):
        """Tap a list row identified only by its visible text.

        Show cards and episode rows carry no test id, and the text sits in a
        non-clickable child, so we climb to the nearest clickable ancestor.
        """
        end = time.time() + timeout
        xpath = f'//*[@text="{value}"]/ancestor::*[@clickable="true"][1]'
        last = None
        while time.time() < end:
            try:
                if self.platform == "android":
                    return self.driver.find_element(By.XPATH, xpath).click()
                return self.driver.find_element(By.ACCESSIBILITY_ID, value).click()
            except WebDriverException as exc:  # not there yet, or the list is settling
                last = exc
                time.sleep(POLL)
        raise AssertionError(f"could not tap row {value!r} within {timeout}s ({last})")

    def wait_until(self, predicate, timeout: float = TIMEOUT, message: str = ""):
        return WebDriverWait(self.driver, timeout, POLL).until(lambda d: predicate(), message)

    # ---- scrolling ------------------------------------------------------
    # Finger swipe on the current window. "down"/"left" are content directions:
    # scroll down to see what is below (finger moves up); scroll left to see
    # what is to the right (finger moves left). Same helper on Android and iOS.
    def scroll_vertical(self, direction: str = "down", percent: float = 0.5,
                        duration_ms: int = 400) -> None:
        direction = direction.lower()
        if direction not in ("down", "up"):
            raise ValueError(f"direction must be 'down' or 'up', got {direction!r}")
        width, height = self._window()
        travel = int(height * percent)
        mid_x = width // 2
        mid_y = height // 2
        if direction == "down":
            self.driver.swipe(mid_x, mid_y + travel // 2, mid_x, mid_y - travel // 2, duration_ms)
        else:
            self.driver.swipe(mid_x, mid_y - travel // 2, mid_x, mid_y + travel // 2, duration_ms)

    def scroll_horizontal(self, direction: str = "left", percent: float = 0.5,
                          duration_ms: int = 400) -> None:
        direction = direction.lower()
        if direction not in ("left", "right"):
            raise ValueError(f"direction must be 'left' or 'right', got {direction!r}")
        width, height = self._window()
        travel = int(width * percent)
        mid_x = width // 2
        mid_y = height // 2
        if direction == "left":
            self.driver.swipe(mid_x + travel // 2, mid_y, mid_x - travel // 2, mid_y, duration_ms)
        else:
            self.driver.swipe(mid_x - travel // 2, mid_y, mid_x + travel // 2, mid_y, duration_ms)

    def _window(self) -> tuple[int, int]:
        size = self.driver.get_window_size()
        return int(size["width"]), int(size["height"])
