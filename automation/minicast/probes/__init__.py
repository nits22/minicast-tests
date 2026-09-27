"""Playback probes: what the platform says is happening, not what the app claims."""
from __future__ import annotations

from minicast.probes.android import AndroidProbe
from minicast.probes.base import PlaybackProbe
from minicast.probes.ios import IOSProbe

_IMPLEMENTATIONS: dict[str, type] = {"android": AndroidProbe, "ios": IOSProbe}


def probe_for(platform: str) -> PlaybackProbe:
    try:
        impl = _IMPLEMENTATIONS[platform.lower()]
    except KeyError:
        raise ValueError(f"no playback probe for platform {platform!r}") from None

    probe = impl()
    # isinstance against a runtime_checkable Protocol checks the method *names*
    # exist, not their signatures - mypy covers signatures. Cheap guard against
    # an implementation quietly losing a method the tests rely on.
    if not isinstance(probe, PlaybackProbe):
        required = [n for n in vars(PlaybackProbe) if not n.startswith("_")]
        missing = [n for n in required if not hasattr(probe, n)]
        raise TypeError(f"{impl.__name__} does not satisfy PlaybackProbe; missing: {missing}")
    return probe


__all__ = ["AndroidProbe", "IOSProbe", "PlaybackProbe", "probe_for"]
