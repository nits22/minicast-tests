#!/usr/bin/env bash
# Everything the emulator job does, in one file.
#
# The android-emulator-runner action runs each line of an inline `script:` in its
# own shell, so loops and if-blocks silently break. Keeping it here means normal
# bash, and it can be run locally against an emulator too.
set -euo pipefail

APK="${APK:-app/minicast-release.apk}"
APPIUM_URL="${APPIUM_URL:-http://127.0.0.1:4723}"

echo "::group::Wait for the device"
adb wait-for-device
until [[ "$(adb shell getprop sys.boot_completed 2>/dev/null | tr -d '\r')" == "1" ]]; do sleep 2; done
until adb shell pm path android >/dev/null 2>&1; do sleep 2; done
adb shell settings put global hide_error_dialogs 1
adb shell settings put global window_animation_scale 0
adb shell settings put global transition_animation_scale 0
adb shell settings put global animator_duration_scale 0
adb shell input keyevent KEYCODE_WAKEUP || true
echo "device ready: $(adb shell getprop ro.build.version.release | tr -d '\r')"
echo "::endgroup::"

echo "::group::Install the app"
adb install -r -g "$APK"
adb shell pm list packages | grep -q com.audiomob.minicast
echo "::endgroup::"

echo "::group::Start Appium"
adb logcat -c || true
appium --log-timestamp --log appium.log --log-level info &
APPIUM_PID=$!
for _ in $(seq 1 40); do
  if curl -sf "$APPIUM_URL/status" >/dev/null; then break; fi
  sleep 2
done
if ! curl -sf "$APPIUM_URL/status" >/dev/null; then
  echo "Appium did not come up within 80s"; tail -50 appium.log || true; exit 1
fi
echo "Appium ready (pid $APPIUM_PID)"
echo "::endgroup::"

echo "::group::Run the suite"
set +e
# The APK is already installed above, so Appium reuses it rather than installing twice.
uv run pytest -v --no-install --reruns 1 --reruns-delay 3
STATUS=$?
set -e
echo "::endgroup::"

adb logcat -d > logcat.txt 2>/dev/null || true
kill "$APPIUM_PID" 2>/dev/null || true
exit "$STATUS"
