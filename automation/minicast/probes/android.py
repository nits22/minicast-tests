"""Android playback probe: media session, audio HAL and media metrics.

Three independent signals:
  media_session  what the app claims
  dumpsys audio  whether a player is actually writing to the audio output
  media.metrics  how many frames reached the sink
"""
from __future__ import annotations

import re

from minicast.support import adb

_STATE = re.compile(r"state=([A-Z]+)\(\d\), position=(\d+), buffered position=(\d+), speed=([\d.]+)")


class AndroidProbe:
    def _session(self) -> dict:
        m = _STATE.search(adb.shell("dumpsys", "media_session"))
        if not m:
            return {"state": "NONE", "position": 0.0, "speed": 0.0}
        return {
            "state": m.group(1),
            "position": int(m.group(2)) / 1000.0,
            "buffered": int(m.group(3)) / 1000.0,
            "speed": float(m.group(4)),
        }

    def state(self) -> str:
        return self._session()["state"]

    def position(self) -> float:
        return self._session()["position"]

    def speed(self) -> float:
        return self._session()["speed"]

    def _app_uid(self) -> str | None:
        if self.__dict__.get("_uid_cache") is None:
            out = adb.shell("dumpsys", "package", adb.PACKAGE)
            # appId on recent Android, userId on older builds.
            m = re.search(r"\bappId=(\d+)", out) or re.search(r"\buserId=(\d+)", out)
            self.__dict__["_uid_cache"] = m.group(1) if m else ""
        return self.__dict__["_uid_cache"] or None

    def audio_active(self) -> bool:
        """Is this app writing media audio to the output right now?

        Each player is one line of `dumpsys audio`:

            AudioPlaybackConfiguration piid:9471 ... u/pid:10183/3083 state:started
            attr:AudioAttributes: usage=USAGE_MEDIA ...

        Matching is scoped to our uid on purpose - a looser check passes whenever
        anything on the phone happens to be playing.
        """
        uid = self._app_uid()
        for line in adb.shell("dumpsys", "audio").splitlines():
            if "AudioPlaybackConfiguration" not in line:
                continue
            if "state:started" not in line or "usage=USAGE_MEDIA" not in line:
                continue
            if uid and f"u/pid:{uid}/" not in line:
                continue
            return True
        return False

    def frames_written(self) -> int | None:
        out = adb.shell("dumpsys", "media.metrics")
        hits = [int(m.group(1)) for m in re.finditer(r"frameCount=(\d+)", out)]
        return max(hits) if hits else None
