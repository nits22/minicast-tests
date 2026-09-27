"""Page objects, and the factory that builds them for a session.

Python's Selenium has no PageFactory (the @FindBy proxies are a Java/C# feature),
so the equivalent here is the conventional one: each page declares its own
locators, and a small factory wires them to a driver and platform.
"""
from __future__ import annotations

from dataclasses import dataclass

from minicast.pages.base import BasePage
from minicast.pages.discover import Discover
from minicast.pages.now_playing import NowPlaying
from minicast.pages.settings import Settings
from minicast.pages.show_detail import ShowDetail

PAGE_CLASSES: tuple[type[BasePage], ...] = (Discover, ShowDetail, NowPlaying, Settings)


@dataclass(frozen=True)
class Pages:
    """Every page for one session. Tests take this, not a dict."""

    discover: Discover
    show: ShowDetail
    now: NowPlaying
    settings: Settings


def build_pages(driver, platform: str = "android") -> Pages:
    return Pages(
        discover=Discover(driver, platform),
        show=ShowDetail(driver, platform),
        now=NowPlaying(driver, platform),
        settings=Settings(driver, platform),
    )


def check_locator_parity() -> None:
    """Every page must define the same logical names on both platforms."""
    problems = []
    for page in PAGE_CLASSES:
        android = set(page.LOCATORS.get("android", {}))
        ios = set(page.LOCATORS.get("ios", {}))
        if android != ios:
            problems.append(
                f"{page.__name__}: android-only={sorted(android - ios)} "
                f"ios-only={sorted(ios - android)}"
            )
    common_a = set(BasePage.COMMON.get("android", {}))
    common_i = set(BasePage.COMMON.get("ios", {}))
    if common_a != common_i:
        problems.append(f"COMMON: android-only={sorted(common_a - common_i)} "
                        f"ios-only={sorted(common_i - common_a)}")
    if problems:
        raise AssertionError("locator drift:\n  " + "\n  ".join(problems))


__all__ = ["Discover", "NowPlaying", "Pages", "Settings", "ShowDetail",
           "build_pages", "check_locator_parity"]
