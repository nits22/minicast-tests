"""Thin adb wrapper. Android-only; nothing outside probes/ should import this."""
from __future__ import annotations

import os
import subprocess

PACKAGE = "com.audiomob.minicast"
ACTIVITY = f"{PACKAGE}/.MainActivity"


def _base() -> list[str]:
    serial = os.environ.get("ANDROID_SERIAL")
    return ["adb", "-s", serial] if serial else ["adb"]


def shell(*args: str, timeout: int = 30) -> str:
    out = subprocess.run(_base() + ["shell", *args], capture_output=True, text=True,
                         timeout=timeout, check=False)
    return out.stdout


def force_stop() -> None:
    shell("am", "force-stop", PACKAGE)


def kill() -> None:
    """Simulates the OS reclaiming the process, unlike force-stop."""
    shell("am", "kill", PACKAGE)


def start() -> None:
    shell("am", "start", "-n", ACTIVITY)


def logcat_dump() -> str:
    return subprocess.run(_base() + ["logcat", "-d", "-v", "time"],
                          capture_output=True, text=True, timeout=60, check=False).stdout


def wake() -> None:
    """Wake the screen and dismiss a simple keyguard.

    A handset left alone between runs goes to sleep, and a sleeping screen fails
    every test at setup. Harmless if the device is already awake.
    """
    shell("input", "keyevent", "KEYCODE_WAKEUP")
    shell("input", "swipe", "500", "1800", "500", "700", "200")


def keep_awake(on: bool) -> None:
    shell("svc", "power", "stayon", "true" if on else "false")
