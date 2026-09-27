from __future__ import annotations

import time
from typing import ClassVar

from minicast.pages.base import BasePage, accessibility_id, test_tag
from minicast.support.catalog import SHOW_NAMES


class Discover(BasePage):
    LOCATORS: ClassVar[dict[str, dict[str, tuple[str, str]]]] = {
        "android": {
            "search_field": test_tag("searchField"),
            "featured_list": test_tag("featuredList"),
            "settings_button": test_tag("settingsButton"),
            "empty_search": test_tag("emptySearchResults"),
        },
        "ios": {
            "search_field": accessibility_id("searchField"),
            "featured_list": accessibility_id("featuredList"),
            "settings_button": accessibility_id("settingsButton"),
            "empty_search": accessibility_id("emptySearchResults"),
        },
    }

    def is_open(self) -> bool:
        return self.exists("search_field")

    def wait_open(self, timeout: int = 12):
        self.wait_until(lambda: self.exists("search_field", timeout=1), timeout,
                        "did not return to Discover")

    def search(self, query: str, settle: float = 3.0) -> Discover:
        field = self.find("search_field")
        field.click()
        field.clear()
        field.send_keys(query)
        time.sleep(settle)          # fixed simulated API latency, ~1.5s
        return self

    def clear_search(self) -> Discover:
        self.find("search_field").clear()
        time.sleep(2.0)
        return self

    def results(self) -> list[str]:
        """Show names currently on screen, in catalog order."""
        return [name for name in SHOW_NAMES if self.has_text(name, timeout=0.5)]

    def shows_empty_state(self) -> bool:
        return self.exists("empty_search", timeout=2)

    def featured_visible(self) -> bool:
        return self.has_text("Featured shows", timeout=2)

    def open_show(self, name: str):
        self.tap_row(name)

    def open_settings(self):
        self.tap("settings_button")
