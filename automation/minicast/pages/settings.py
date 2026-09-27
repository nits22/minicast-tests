from __future__ import annotations

from typing import ClassVar

from minicast.pages.base import BasePage, accessibility_id, test_tag


class Settings(BasePage):
    LOCATORS: ClassVar[dict[str, dict[str, tuple[str, str]]]] = {
        "android": {
            "resume_toggle": test_tag("resumeToggle"),
            "speed_1x": test_tag("speedOption_1x"),
            "speed_15x": test_tag("speedOption_1.5x"),
            "speed_2x": test_tag("speedOption_2x"),
            "sleep_1": test_tag("sleepDuration_1"),
            "sleep_5": test_tag("sleepDuration_5"),
            "sleep_10": test_tag("sleepDuration_10"),
            "sleep_15": test_tag("sleepDuration_15"),
            "sleep_notification": test_tag("sleepNotificationToggle"),
        },
        "ios": {
            "resume_toggle": accessibility_id("resumeToggle"),
            "speed_1x": accessibility_id("speedOption_1x"),
            "speed_15x": accessibility_id("speedOption_1.5x"),
            "speed_2x": accessibility_id("speedOption_2x"),
            "sleep_1": accessibility_id("sleepDuration_1"),
            "sleep_5": accessibility_id("sleepDuration_5"),
            "sleep_10": accessibility_id("sleepDuration_10"),
            "sleep_15": accessibility_id("sleepDuration_15"),
            "sleep_notification": accessibility_id("sleepNotificationToggle"),
        },
    }

    def is_open(self) -> bool:
        return self.exists("resume_toggle")

    def _checked(self, name: str) -> bool:
        return self.find(name).get_attribute("checked") == "true"

    def resume_enabled(self) -> bool:
        return self._checked("resume_toggle")

    def set_resume(self, on: bool):
        if self.resume_enabled() != on:
            self.tap("resume_toggle")

    def default_speed(self) -> str:
        for name, label in (("speed_1x", "1x"), ("speed_15x", "1.5x"), ("speed_2x", "2x")):
            if self._checked(name):
                return label
        return "?"

    def sleep_minutes(self) -> int | None:
        for name, minutes in (("sleep_1", 1), ("sleep_5", 5), ("sleep_10", 10), ("sleep_15", 15)):
            if self.exists(name, 2) and self._checked(name):
                return minutes
        return None

    def notifications_enabled(self) -> bool:
        return self._checked("sleep_notification")

    def set_speed_2x_sleep_1_notifications_off(self):
        self.tap("speed_2x")
        self.tap("sleep_1")
        if self.notifications_enabled():
            self.tap("sleep_notification")

    def back(self):
        self.tap("back_button")
