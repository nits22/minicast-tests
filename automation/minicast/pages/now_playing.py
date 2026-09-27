from __future__ import annotations

import time
from typing import ClassVar

from minicast.pages.base import BasePage, accessibility_id, test_tag


def to_seconds(label: str) -> int:
    m, s = label.split(":")
    return int(m) * 60 + int(s)


class NowPlaying(BasePage):
    LOCATORS: ClassVar[dict[str, dict[str, tuple[str, str]]]] = {
        "android": {
            "episode_title": test_tag("episodeTitle"),
            "show_title": test_tag("showTitle"),
            "seek_bar": test_tag("seekBar"),
            "position_label": test_tag("positionLabel"),
            "duration_label": test_tag("durationLabel"),
            "play_pause": test_tag("playPauseButton"),
            "skip_back": test_tag("skipBackButton"),
            "skip_forward": test_tag("skipForwardButton"),
            "speed_button": test_tag("speedButton"),
            "sleep_timer": test_tag("sleepTimerButton"),
            # The transport buttons carry no text or description themselves - the
            # label sits on a child node, so these resolve that child directly.
            "state_play": accessibility_id("Play"),
            "state_paused": accessibility_id("Pause"),
        },
        "ios": {
            "episode_title": accessibility_id("episodeTitle"),
            "show_title": accessibility_id("showTitle"),
            "seek_bar": accessibility_id("seekBar"),
            "position_label": accessibility_id("positionLabel"),
            "duration_label": accessibility_id("durationLabel"),
            "play_pause": accessibility_id("playPauseButton"),
            "skip_back": accessibility_id("skipBackButton"),
            "skip_forward": accessibility_id("skipForwardButton"),
            "speed_button": accessibility_id("speedButton"),
            "sleep_timer": accessibility_id("sleepTimerButton"),
            "state_play": accessibility_id("Play"),
            "state_paused": accessibility_id("Pause"),
        },
    }

    SPEEDS: ClassVar[tuple[str, ...]] = ("1x", "1.5x", "2x")

    # ---- readings -------------------------------------------------------
    def is_open(self) -> bool:
        return self.exists("position_label")

    def position(self) -> int:
        return to_seconds(self.text("position_label"))

    def duration(self) -> int:
        return to_seconds(self.text("duration_label"))

    def episode_title(self) -> str:
        return self.text("episode_title")

    def show_title(self) -> str:
        return self.text("show_title")

    def speed_label(self) -> str:
        """speedButton has no text of its own - the value is on a child node."""
        for value in self.SPEEDS:
            if self.has_text(value, timeout=1):
                return value
        raise AssertionError("no speed value visible on Now Playing")

    def is_paused(self) -> bool:
        """The control is described as 'Play' when paused and 'Pause' when playing."""
        return self.exists("state_play", timeout=2)

    # ---- actions --------------------------------------------------------
    def play_pause(self):
        self.tap("play_pause")
        time.sleep(1.0)

    def pause(self):
        if not self.is_paused():
            self.play_pause()

    def resume(self):
        if self.is_paused():
            self.play_pause()

    def skip_forward(self):
        self.tap("skip_forward")
        time.sleep(0.8)

    def skip_back(self):
        self.tap("skip_back")
        time.sleep(0.8)

    def cycle_speed(self) -> str:
        self.tap("speed_button")
        time.sleep(0.8)
        return self.speed_label()

    def set_speed(self, wanted: str, attempts: int = 4) -> str:
        for _ in range(attempts):
            if self.speed_label() == wanted:
                return wanted
            self.cycle_speed()
        raise AssertionError(f"speed never reached {wanted}, stuck at {self.speed_label()}")

    def back(self):
        self.tap("back_button")

    def wait_until_agrees(self, probe, tolerance: int = 3,
                          timeout: float = 20) -> tuple[int, float]:
        """Wait for the label and the player to report the same position.

        They are read one after the other, and on an emulator the software audio
        pipeline can leave the player several seconds behind the label. A
        transient gap is not a defect; one that never closes is.
        """
        deadline = time.time() + timeout
        ui: int = 0
        sys_pos: float = 0.0
        while time.time() < deadline:
            ui, sys_pos = self.position(), probe.position()
            if abs(sys_pos - ui) <= tolerance:
                return ui, sys_pos
            time.sleep(1.0)
        raise AssertionError(
            f"UI and player never agreed within {tolerance}s over {timeout}s "
            f"(last: UI {ui}s, player {sys_pos:.0f}s)")

    def wait_for_position(self, at_least: int, timeout: int = 30):
        self.wait_until(lambda: self.position() >= at_least, timeout,
                        f"position never reached {at_least}s")
