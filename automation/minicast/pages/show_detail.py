from __future__ import annotations

from typing import ClassVar

from minicast.pages.base import BasePage, accessibility_id, test_tag


class ShowDetail(BasePage):
    LOCATORS: ClassVar[dict[str, dict[str, tuple[str, str]]]] = {
        "android": {
            "episode_list": test_tag("episodeList"),
            "mini_player": test_tag("miniPlayerBar"),
            "mini_player_title": test_tag("miniPlayerTitle"),
            "mini_play_pause": test_tag("miniPlayerPlayPause"),
        },
        "ios": {
            "episode_list": accessibility_id("episodeList"),
            "mini_player": accessibility_id("miniPlayerBar"),
            "mini_player_title": accessibility_id("miniPlayerTitle"),
            "mini_play_pause": accessibility_id("miniPlayerPlayPause"),
        },
    }

    def is_open(self) -> bool:
        """Both must be present: episodeList can linger for a frame during the transition."""
        return self.exists("episode_list") and self.exists("back_button", timeout=4)

    def wait_open(self, author: str, timeout: int = 12):
        """Confirm the screen settled on the show we asked for, not the previous one."""
        self.wait_until(lambda: self.is_open() and self.has_text(author, timeout=1),
                        timeout, f"show detail for {author!r} did not open")

    def has_episode(self, title: str) -> bool:
        return self.has_text(title, timeout=2)

    def play(self, title: str):
        self.tap_row(title)

    def open_now_playing(self):
        self.tap("mini_player")

    def back(self):
        self.tap("back_button")
