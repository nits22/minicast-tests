"""Finding and choosing the device a run targets.

Appium is told which device to drive through a capability, while the Android
playback probe shells out to adb. If those two disagree the suite drives one
phone and reads another, which is not a failure that announces itself. Resolving
the device once, here, keeps them pointed at the same place.
"""
from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass

_ADB_LINE = re.compile(r"^(\S+)\s+device\b(.*)$")
# xctrace prints "Name (os version) (udid)" for a real device; the host Mac has
# no version group, which is how we tell them apart.
_XCTRACE_LINE = re.compile(r"^(.+?)\s+\(([\d.]+)\)\s+\(([0-9A-Fa-f-]{25,})\)\s*$")


@dataclass(frozen=True)
class Device:
    serial: str                 # adb serial, or iOS UDID
    model: str = ""
    release: str = ""
    platform: str = "android"
    state: str = ""             # iOS simulators: Booted / Shutdown
    virtual: bool = False       # emulator or simulator

    def __str__(self) -> str:
        kind = ("simulator" if self.platform == "ios" else "emulator") if self.virtual else "device"
        bits = [b for b in (self.model, f"{'iOS' if self.platform == 'ios' else 'Android'} {self.release}"
                            if self.release else "", self.state) if b]
        return f"{self.serial} ({kind}: {', '.join(bits)})" if bits else f"{self.serial} ({kind})"


def _run(*cmd: str, timeout: int = 25) -> str:
    try:
        return subprocess.run(cmd, capture_output=True, text=True,
                              timeout=timeout, check=False).stdout
    except (OSError, subprocess.SubprocessError):
        return ""


# ---------------------------------------------------------------- android
def _prop(serial: str, name: str) -> str:
    return _run("adb", "-s", serial, "shell", "getprop", name, timeout=10).strip()


def list_android() -> list[Device]:
    """Every adb device in the `device` state. Offline and unauthorised ones are skipped."""
    found = []
    for line in _run("adb", "devices", "-l").splitlines()[1:]:
        m = _ADB_LINE.match(line.strip())
        if not m:
            continue
        serial = m.group(1)
        model = re.search(r"model:(\S+)", m.group(2))
        found.append(Device(
            serial=serial,
            model=model.group(1) if model else _prop(serial, "ro.product.model"),
            release=_prop(serial, "ro.build.version.release"),
            platform="android",
            virtual=serial.startswith("emulator-"),
        ))
    return found


# ---------------------------------------------------------------- ios
def list_ios() -> list[Device]:
    """Booted simulators first, then physical devices.

    Shutdown simulators are listed too - Appium boots one on demand - but a booted
    one is preferred when no selector is given, because booting costs a minute.
    """
    found: list[Device] = []

    raw = _run("xcrun", "simctl", "list", "devices", "available", "--json")
    if raw:
        try:
            for runtime, sims in json.loads(raw).get("devices", {}).items():
                version = runtime.split(".")[-1].replace("iOS-", "").replace("-", ".")
                for sim in sims:
                    if not sim.get("isAvailable", True):
                        continue
                    found.append(Device(serial=sim["udid"], model=sim.get("name", ""),
                                        release=version, platform="ios",
                                        state=sim.get("state", ""), virtual=True))
        except (ValueError, KeyError):
            pass

    section = _run("xcrun", "xctrace", "list", "devices").split("== Simulators ==")[0]
    for line in section.splitlines():
        m = _XCTRACE_LINE.match(line.strip())
        if m:
            found.append(Device(serial=m.group(3), model=m.group(1).strip(),
                                release=m.group(2), platform="ios", virtual=False))

    found.sort(key=lambda d: (d.state != "Booted", d.virtual))
    return found


# ---------------------------------------------------------------- resolution
def list_devices(platform: str = "android") -> list[Device]:
    return list_ios() if platform.lower() == "ios" else list_android()


def resolve(selector: str | None = None, platform: str = "android") -> Device:
    """Pick the device this run targets.

    `selector` may be an exact serial/UDID, a case-insensitive substring of the
    model, or "virtual"/"real". With no selector a single connected device is
    used; on iOS a booted simulator wins, since several are always "available".
    """
    devices = list_devices(platform)
    if not devices:
        raise RuntimeError(f"no {platform} devices found; connect one or start a simulator")

    if selector:
        key = selector.lower()
        if key in ("emulator", "simulator", "virtual"):
            matches = [d for d in devices if d.virtual]
        elif key == "real":
            matches = [d for d in devices if not d.virtual]
        else:
            # Exact serial, then exact model, then substring. Without the middle
            # step "iPhone 15" would happily resolve to "iPhone 15 Pro Max".
            matches = ([d for d in devices if d.serial == selector]
                       or [d for d in devices if d.model.lower() == key]
                       or [d for d in devices if key in d.model.lower()])
        if not matches:
            raise RuntimeError(f"no {platform} device matches {selector!r}. Found:\n  "
                               + "\n  ".join(str(d) for d in devices))
        booted = [d for d in matches if d.state == "Booted"]
        if len(matches) > 1 and len(booted) != 1:
            raise RuntimeError(f"{selector!r} matches more than one device:\n  "
                               + "\n  ".join(str(d) for d in matches))
        return booted[0] if booted else matches[0]

    if len(devices) == 1:
        return devices[0]
    booted = [d for d in devices if d.state == "Booted"]
    if len(booted) == 1:
        return booted[0]
    raise RuntimeError(
        f"{len(devices)} {platform} devices found, so the target is ambiguous. "
        "Pass --device <serial|model|virtual|real>:\n  "
        + "\n  ".join(str(d) for d in devices)
    )


def pool(selector: str | None, platform: str = "android") -> list[Device]:
    """The devices a parallel run may spread across.

    A comma-separated selector names them explicitly; otherwise every connected
    device of that platform is fair game. Simulators that are not booted are left
    out - booting several at once to run tests on them is not something to do by
    accident.
    """
    if selector and "," in selector:
        return [resolve(part.strip(), platform) for part in selector.split(",") if part.strip()]
    if selector:
        return [resolve(selector, platform)]
    found = list_devices(platform)
    if platform.lower() == "ios":
        booted = [d for d in found if d.state == "Booted" or not d.virtual]
        return booted or found[:1]
    return found


def for_worker(selector: str | None, platform: str, worker: int) -> Device:
    """Hand worker N its device, round-robin if there are fewer devices than workers."""
    available = pool(selector, platform)
    if not available:
        raise RuntimeError(f"no {platform} devices available")
    return available[worker % len(available)]
