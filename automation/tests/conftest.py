"""Helpers shared by the test modules."""
from __future__ import annotations

import allure


def covers(*test_case_ids: str):
    """Tie an automated test back to the manual cases it replaces.

    Keeps the mapping visible in the Allure report rather than only in the plan.
    """
    def wrapper(fn):
        fn = allure.label("covers", ",".join(test_case_ids))(fn)
        for tc in test_case_ids:
            fn = allure.tag(tc)(fn)
        return fn
    return wrapper
