"""Discover: search behaviour and catalog content."""
from __future__ import annotations

import allure
import pytest

from minicast.pages import Pages
from minicast.support import catalog
from tests.conftest import covers


@allure.feature("Discover")
@allure.story("Search")
@covers("TC-1.3", "TC-1.4", "TC-1.6", "TC-1.7", "TC-1.8")
@pytest.mark.smoke
@pytest.mark.regression
def test_search_matching_and_minimum_length(pages: Pages):
    """Search needs 2 characters, matches title and author, and has an empty state."""
    d = pages.discover
    assert d.is_open()

    with allure.step("one character does not search"):
        d.search("t", settle=3.0)
        assert d.featured_visible(), "a 1-char query should leave the featured list alone"
        assert not d.shows_empty_state()

    with allure.step("two characters match on title"):
        d.search("th")
        assert d.results() == ["The Daily Byte", "True North Tales"]

    with allure.step("author is searchable too"):
        d.search("wander")
        assert d.results() == ["True North Tales"]

    with allure.step("no match shows the empty state"):
        d.search("zz")
        assert d.shows_empty_state()
        assert d.results() == []

    with allure.step("clearing restores the featured list"):
        d.clear_search()
        assert d.featured_visible()


@allure.feature("Discover")
@allure.story("Catalog content")
@covers("TC-0.2", "TC-1.2", "TC-2.1", "TC-2.2", "TC-2.3")
@pytest.mark.regression
def test_catalog_and_episode_lists_match_the_bundle(pages: Pages):
    """All 6 shows and all 26 episodes render with the right duration and date."""
    d, show = pages.discover, pages.show

    assert d.results() == catalog.SHOW_NAMES, "featured list does not match the bundled catalog"

    problems: list[str] = []
    for entry in catalog.SHOWS:
        with allure.step(entry["show"]):
            d.open_show(entry["show"])
            show.wait_open(entry["author"])
            for ep in entry["episodes"]:
                if not show.has_episode(ep["title"]):
                    problems.append(f"{entry['show']}: missing {ep['title']!r}")
                elif not show.has_text(ep["duration"], timeout=1):
                    problems.append(f"{ep['title']}: duration {ep['duration']} not shown")
                elif not show.has_text(ep["released"], timeout=1):
                    problems.append(f"{ep['title']}: date {ep['released']} not shown")
            show.back()
            d.wait_open()
    assert not problems, "catalog mismatches: " + "; ".join(problems[:6])
