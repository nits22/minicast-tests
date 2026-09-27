# MiniCast — Manual Test Plan

> Release qualification for the MiniCast Android app

| | |
|---|---|
| **Prepared by** | Nitish Bector |
| **Date** | 23 September 2026 |
| **Version** | 1.0 |
| **Build under test** | `minicast-release.apk` |
| **Test device** | CPH2491 handset, Android 16 |

## 1. Overview

MiniCast is a podcast player with a fixed sample catalog. This plan covers what I would test to sign the build off for release, in what order, and why.

I spent the first half hour simply using the app the way a listener would — browsing, searching, playing episodes, changing settings — before writing any cases. Most of what shaped this plan came out of that session, and it is summarised in section 2.

The audio is spoken counting, and the number you hear always matches the playback position in seconds. That is a gift for a tester: it means I can check the audio against the screen on every case, rather than trusting the progress bar. I lean on it heavily in suites S3 and S4.

Alongside this document, `TEST_CASES.csv` holds the same 144 cases as a tracking sheet, with Status, Actual Result and Defect ID columns ready to fill in during execution.

## 2. What I found getting to know the app

A few things are worth stating up front, because they either differ from what the brief implies or they shaped which cases I wrote.

| What I found | Why it matters |
|---|---|
| The speed control is a cycling button — tap it and it steps 1x, 1.5x, 2x, back to 1x. It is not a picker. | Changes how the speed cases are written, and means there is no way to see all three options at once. |
| The sleep timer button is an on/off toggle, not a duration picker. It takes its duration from Settings and the label counts down as “Sleep 9:58”. | The duration and the timer live on two different screens, which is where TC-6.10 comes from. |
| Search matches the show title **and** the author. “media” finds The Daily Byte, “wander” finds True North Tales. Genre is not matched — “technology” and “travel” return “No shows found”. | Good: searching by publisher is what listeners actually do. The genre gap is worth a note rather than a defect, and TC-1.7 pins both halves down. |
| Every 0:10 episode plays an identical clip, and the same is true at 0:30 and at 1:00. The app reuses a handful of audio tracks across all 26 episodes. | If the app saves your place against the audio rather than the episode, one episode will quietly overwrite another. This is **TC-5.4**, and it is the case I would most want run. |
| Rotating the phone visibly rebuilds the screen rather than just re-laying it out. | Anything held by the screen rather than the player is at risk on every rotation, theme change and font change. This is why suite S9 is as large as it is. |
| When an episode finishes, playback stops and nothing else starts. There is no auto-advance. | Reasonable, but it needs confirming as intentional and it must leave clean state behind (TC-3.4). |
| Factory defaults are: resume ON, speed 1x, sleep timer 10 min, sleep notification ON. | The baseline every persistence case in S5 is measured against. |

### 2.1  Two things I noted but have not filed

Both are carried into a case for a proper verdict rather than reported on first sight.

| Ref | Observation | Followed up in |
|---|---|---|
| OBS-1 | The sleep timer will arm and count down even when nothing is playing. It may be harmless, but a timer running against silence is odd and the control could simply be unavailable. | TC-6.11 |
| OBS-2 | At the end of a 0:30 episode the reported position ran slightly past the duration. Invisible to a listener, but it is the sort of off-by-one that breaks an automated check later. | TC-3.4, TC-4.4 |

### 2.2  Controls and their test identifiers

Most controls carry a stable identifier, which I confirmed against the running app. These are the hooks the automated suite will use.

| Screen | Identifiers |
|---|---|
| Discover | `searchField` · `featuredList` · `settingsButton` · `emptySearchResults` |
| Show detail | `episodeList` · `backButton` |
| Mini player | `miniPlayerBar` · `miniPlayerTitle` · `miniPlayerPlayPause` |
| Now Playing | `episodeTitle` · `showTitle` · `seekBar` · `positionLabel` · `durationLabel` · `skipBackButton` · `playPauseButton` · `skipForwardButton` · `speedButton` · `sleepTimerButton` |
| Settings | `resumeToggle` · `speedOption_1x` · `speedOption_1.5x` · `speedOption_2x` · `sleepDuration_1` · `sleepDuration_5` · `sleepDuration_10` · `sleepDuration_15` · `sleepNotificationToggle` |

> **One gap worth raising with the developers:** show cards and episode rows have no identifier at all, so they can only be found by their visible text. Adding one per show and per episode is a small change for them and would make the automated suite considerably steadier.

> **And a caution on how they add them.** The transport buttons are found today by their spoken label — the description a screen reader reads out. That works, but it is the accessibility label doing a test's job, and it breaks the moment the wording changes. Better to keep the two apart: a test tag on Android and a matching accessibility identifier on iOS, both set from the same constant, leaving the spoken label free to say whatever reads best.

## 3. How I prioritised

This is a media player, so I ranked risk by what actually makes someone uninstall a podcast app — not by how much of the feature list each area covers.

|  | Risk | Why it sits here | Suite |
|---|---|---|---|
| 1 | Audio plays when it should not, or stops when it should not | Playing over a phone call, or going quiet in your pocket mid-run, is the kind of thing people do not forgive | S8 |
| 2 | What you hear and what the screen says disagree | The label reads 0:20 but the audio says “five”. Quietly destroys trust in the app | S3, S4 |
| 3 | Losing your place in an episode | Resume is the whole point of a podcast app | S5 |
| 4 | Rotation or being killed in the background loses state | The screen visibly rebuilds on rotation, so this is likely rather than merely possible | S9 |
| 5 | Offline is a dead end with no way back | Commuters are the target user and tunnels are the target environment | S10 |
| 6 | Notification controls out of step with the app | The lock screen is where most listening is actually controlled | S7 |
| 7 | Browsing and search problems | Irritating, but there is always a way round them | S1, S2 |

Execution follows that order, with one exception: a short smoke pass (S0) runs first. There is no point testing interruption handling if the build cannot play a file.

### 3.1  What I am not testing

- The fixed catalog and the counting audio. Both are stated design decisions, not defects.
- The simulated network delay as a number. How the app behaves during that delay is very much in scope.
- **No backend testing.** The app serves its own content and makes no real network requests, so there is no API to intercept, mock or fault-inject. What the app does *around* its simulated calls — loading states, error handling, retry and recovery — is very much in scope and is covered in suite S10.
- Security, beyond a sanity check that launching the app from outside exposes nothing unexpected (TC-11.8).

### 3.2  Entry and exit criteria

**Entry:** the app installs on a clean profile, opens to Discover, and plays at least one episode audibly.

**Exit** — how I would frame a release recommendation:

| Severity | What it means | Release gate |
|---|---|---|
| 1  Critical | Crash, freeze, lost data, or audio playing when the phone must be silent | None open. Hard block. |
| 2  Major | A main journey is broken, or state is wrong with no way for the user to recover | None open. Hard block. |
| 3  Minor | Wrong but recoverable, and there is a workaround | Up to three, each with a written reason |
| 4  Cosmetic | Visual or wording issue with no functional impact | Not a gate |

## 4. Environment and setup

| Tier | Device | Android | Why |
|---|---|---|---|
| Primary | CPH2491 (physical handset) | 16 | The full plan. Real speakers, real calls, real power management — none of which an emulator reproduces honestly. |
| Secondary | Emulator, Pixel profile | 8.0 | The oldest version the app supports. Notification behaviour differs here. |
| Secondary | Emulator, Pixel profile | 13 | The first version where the user can refuse notifications outright. |

**A note on the device.** The handset is a personal phone, so every command is pinned to its serial. Setting it once per terminal session means a stray command cannot reach another device:

```bash
export ANDROID_SERIAL=8TUSGEXOQWQSQ4WS
```

### 4.1  Resetting between suites

A full data wipe is the only reliable reset. Force-stopping the app leaves both the settings and the saved positions behind, which quietly invalidates the next persistence case.

```bash
adb shell pm clear com.audiomob.minicast
adb shell am start -W -n com.audiomob.minicast/.MainActivity
```

> **Check that the wipe actually happened.** On the CPH2491 handset used here, `pm clear` is refused outright with a SecurityException - the shell user has no CLEAR_APP_USER_DATA permission on this manufacturer build. The command prints an exception and the app keeps all of its data, so any case that assumes a clean start silently runs against the previous state. Where that happens, wipe by reinstalling instead, and accept the on-device install prompt:

```bash
adb uninstall com.audiomob.minicast
adb install -r minicast-release.apk
```

Confirm the reset worked by opening Settings and checking the four factory defaults before continuing.

### 4.2  What I use to check behaviour

Beyond watching and listening, these give me a second opinion that does not depend on the app’s own UI.

| What it tells me | Command |
|---|---|
| Real playback state, position and speed | `adb shell dumpsys media_session | grep -A2 PlaybackState` |
| Whether sound is genuinely being produced | `adb shell dumpsys audio | grep -A3 AudioPlaybackConfiguration` |
| Crashes, freezes and exceptions | `adb logcat -v time -s AndroidRuntime:E ActivityManager:E *:F` |
| On-screen controls and their identifiers | `adb shell uiautomator dump /sdcard/ui.xml && adb shell cat /sdcard/ui.xml` |
| Whether background playback is still alive | `adb shell dumpsys activity services com.audiomob.minicast` |
| Taking the phone offline and back | `adb shell cmd connectivity airplane-mode enable | disable` |
| Killing the app the way Android would | `adb shell am kill com.audiomob.minicast` |

A log capture runs for the whole session and gets attached to any bug I raise.

### 4.3  A note on timing

The position the system reports is a snapshot with a timestamp, not a live reading, so I work from the timestamp rather than the raw number. Every timing expectation in this plan allows one to two seconds either way. The speed checks (TC-4.10, TC-4.11) use a twenty-second window, which is long enough that tap delay does not matter.

## 5. Order of execution and time budget

Suites run in risk order rather than document order. The right-hand column is the reason each slot sits where it does.

|  | Suites | Budget | Reason |
|---|---|---|---|
| 1 | S0 | 15 min | The gate. If something here fails I stop, raise it, and rethink the plan rather than testing on top of a broken build. |
| 2 | S3 + S4 | 30 min | Sets up the audio check. Everything later depends on being able to trust position and speed. |
| 3 | S8 + S9 | 30 min | The two riskiest areas, run while concentration is best. Both need careful timing. |
| 4 | S10 | 20 min | Needs uninterrupted control of the phone’s radios, so it runs as one block. |
| 5 | S5 + S6 | 20 min | Persistence and timers involve real waiting, so they are batched late where the waiting overlaps. |
| 6 | S7 | 15 min | Notification behaviour, much of which I will already have seen during S8 and S9. |
| 7 | S1 + S2 | 15 min | Lowest impact on the listener, and the easiest to automate later — so the cheapest to defer. |
| 8 | S11 | remainder | Time-boxed sweep of accessibility, themes and resource handling. |

That comes to roughly two and a half hours against a two-hour budget. If I run short I cut S11 first, then S1 and S2, then the lower-priority rows of S5 to S7. **I would not cut a P0.**

## 6. Execution summary

Run on the CPH2491 handset, Android 16. S1 to S4 were executed in full; elsewhere only P0 cases were run. P1 and P2 cases outside S1-S4 are in the suite but were not executed this session.

**Blocked** means the behaviour cannot be judged until the linked defect is fixed. Recording those as failures would imply separate defects when there is one root cause.

**Not Run** means exactly that - the case was not completed in this session. Nothing is recorded as a defect unless it was observed directly.

## 7. Test cases

96 cases. **P0** blocks the release · **P1** must pass · **P2** should pass.

### Suite notes

- **S6 - Sleep Timer** — The timer is an on/off toggle that takes its duration from Settings. TC-6.4 is the one to watch: the shortest timer and the longest episode are both exactly one minute, so two separate stop paths can be made to fire at the same instant.

<!-- CASES -->
*The 96 cases are maintained in [`../TEST_CASES.csv`](../TEST_CASES.csv) and rendered here by `tools/render_report.py`. Edit the CSV to record execution results.*

## 8. What I would test with more time

In the order I would pick them up.

1. **A long listening session** — An hour of continuous playback across screen-off, network changes and several interruptions. Media problems tend to build up over time, and a few hours of testing cannot surface them.
2. **Older Android versions** — Everything here ran on one recent handset. The oldest supported version, and the first version where notifications can be refused, are both untested.
3. **Other manufacturers** — OnePlus, Xiaomi and Samsung each shut down background apps differently. Media apps fail in the wild for this far more often than for anything in the code.
4. **Bluetooth and car head units** — Route changes, metadata on the car display, and steering-wheel controls. A big real-world surface that this plan only samples.
5. **Random-input testing** — Seeded Monkey runs plus deliberate sequences aimed at the moment just after a tap, which is where the races in this app seem to live.
6. **Accessibility properly** — A full journey with a screen-reader user rather than my own traversal, plus Switch Access and very large text.
7. **Performance measurement** — Start-up time, dropped frames while scrolling the episode list, and traces around seeking and speed changes.
8. **Server-side failure modes** — The only failure this build can produce is offline. With a real backend I would also cover 5xx responses, request timeouts, malformed payloads and slow trickling responses — a client that survives an abrupt disconnect can still fall over on a 500 that returns an HTML error page.
9. **Other languages** — Checking whether the app is genuinely translated, and pseudo-localising to find text that will not fit.
10. **Upgrading from an older build** — Saved positions are the user’s data. Losing them on an update is silent and expensive.
11. **A security pass** — Confirming the playback service cannot be driven by another app or made to give up session information.

## 9. Assumptions and limitations

- **One device.** Everything is executed on a single physical handset. The two emulator tiers in section 4 are planned but will not fit inside the time budget.
- **Personal handset.** Commands are pinned to its serial, and the call-based cases in S8 are run with the owner’s agreement.
- **Settings are checked through the app.** I confirm a setting persisted by restarting and looking, which is slower and slightly coarser than reading it directly.
- **Timing tolerance.** Position checks allow one to two seconds either way, for the reasons in section 4.3.
- **List items have no identifiers.** Show cards and episode rows are found by their visible text, which is fine manually but will make the automated suite more fragile than it needs to be.

## Appendix A · Test data

The full catalog, as it appears in the app. The **Clip** column records which of the three audio tracks you actually hear — episodes of the same length play an identical clip. That is what makes TC-5.4 possible.

| Show | Author | Episode | Length | Clip | Released |
|---|---|---|---|---|---|
| The Daily Byte | Byte Media | Zero-Day in the Coffee Machine | 0:10 | c10 | 2026-08-18 |
|  |  | The Great Password Purge | 0:30 | c30 | 2026-08-11 |
|  |  | AI Writes Our Show Notes Now | 1:00 | c60 | 2026-08-04 |
|  |  | Quantum Bugs and Where to Find Them | 0:30 | c30 | 2026-07-28 |
|  |  | The Off-By-One Episode | 0:10 | c10 | 2026-07-21 |
| History Rewind | Rewind Studios | The Shortest War in History | 0:10 | c10 | 2026-08-15 |
|  |  | Rome Wasn't Debugged in a Day | 0:30 | c30 | 2026-08-08 |
|  |  | The Library of Alexandria Incident | 1:00 | c60 | 2026-08-01 |
|  |  | Napoleon's Lost Playlist | 0:30 | c30 | 2026-07-25 |
| Mindful Minutes | Calm Collective | One Breath at a Time | 0:10 | c10 | 2026-08-19 |
|  |  | The Thirty-Second Reset | 0:30 | c30 | 2026-08-12 |
|  |  | A Minute of Stillness | 1:00 | c60 | 2026-08-05 |
|  |  | Counting Down to Calm | 0:30 | c30 | 2026-07-29 |
| Startup Stories | Founder Radio | The Pivot That Wasn't | 0:30 | c30 | 2026-08-17 |
|  |  | Burn Rate Blues | 0:10 | c10 | 2026-08-10 |
|  |  | Series A, B, and Sea | 1:00 | c60 | 2026-08-03 |
|  |  | The MVP Was a Spreadsheet | 0:30 | c30 | 2026-07-27 |
|  |  | Exit Strategy | 0:10 | c10 | 2026-07-20 |
| Science Weekly | Lab Notes | Why the Sky Isn't Actually Blue | 0:30 | c30 | 2026-08-14 |
|  |  | The Ten-Second Universe | 0:10 | c10 | 2026-08-07 |
|  |  | Sixty Seconds of Gravity | 1:00 | c60 | 2026-07-31 |
|  |  | Peer Review Under Pressure | 0:30 | c30 | 2026-07-24 |
| True North Tales | Wander Audio | Lost in Reykjavik | 0:30 | c30 | 2026-08-16 |
|  |  | The Ten-Second Layover | 0:10 | c10 | 2026-08-09 |
|  |  | A Minute in Marrakesh | 1:00 | c60 | 2026-08-02 |
|  |  | Trains, Fjords, and Podcasts | 0:30 | c30 | 2026-07-26 |

### Episodes used most in these cases

|  |  |
|---|---|
| AI Writes Our Show Notes Now — The Daily Byte, 1:00 | The default for seeking, speed and interruption cases - long enough to work in. |
| The Great Password Purge — The Daily Byte, 0:30 | General playback and resume cases. |
| The Off-By-One Episode — The Daily Byte, 0:10 | End-of-track and boundary cases. |
| Zero-Day in the Coffee Machine — The Daily Byte, 0:10 | Paired with The Off-By-One Episode in TC-5.4: two different episodes in the same show that play an identical clip. |
| One Breath at a Time — Mindful Minutes, 0:10 | The same clip again in a different show, for the cross-show half of TC-5.4. |

### Search terms and what they should return

Verified against the app. Note that a partially cleared search field silently invalidates the next query, so clear it fully and confirm the placeholder has returned before typing again.

| Search for | Should return | Checks |
|---|---|---|
| t | Nothing happens; the Featured list stays | Below the two-character minimum |
| th | The Daily Byte, True North Tales | The two-character boundary |
| mi | Mindful Minutes | A single match |
| byte | The Daily Byte | Matching part-way through the title |
| rewind | History Rewind | Matching on the second word |
| MINDFUL | Mindful Minutes | Capitals should not matter |
| zz | “No shows found” | The empty state |
| media | The Daily Byte | Matching on the author, Byte Media |
| radio | Startup Stories | Matching on the author, Founder Radio |
| wander | True North Tales | Matching on the author, Wander Audio |
| byte media | The Daily Byte | A phrase spanning the title and the author |
| technology | “No shows found” | Genre is not matched — see TC-1.7 |

## Appendix B · ADB / automation reference

The cases are written for a human tester. These are the commands used for setup, debugging and automation.

> `pm clear` is refused on the CPH2491 handset used here - it returns a SecurityException and the app keeps its data. Wipe by uninstalling and reinstalling instead, and accept the install prompt on the device.

## Appendix C · Coverage

| Suite | Cases | P0 | P1 | P2 | P3 |
|---|---|---|---|---|---|
| S0 - Smoke | 5 | 5 | 0 | 0 | 0 |
| S1 - Discover & Search | 9 | 0 | 5 | 4 | 0 |
| S2 - Show Detail | 6 | 0 | 5 | 1 | 0 |
| S3 - Playback | 10 | 3 | 4 | 3 | 0 |
| S4 - Player Controls | 10 | 4 | 6 | 0 | 0 |
| S5 - Settings & Resume | 9 | 4 | 3 | 2 | 0 |
| S6 - Sleep Timer | 8 | 1 | 5 | 2 | 0 |
| S7 - Background & Notification | 9 | 5 | 2 | 2 | 0 |
| S8 - Interruptions | 8 | 4 | 2 | 2 | 0 |
| S9 - Lifecycle | 9 | 5 | 4 | 0 | 0 |
| S10 - Network | 9 | 4 | 3 | 2 | 0 |
| S11 - Cross-cutting | 4 | 0 | 2 | 2 | 0 |
| **Total** | **96** | **35** | **41** | **20** | **0** |

The same cases are in `TEST_CASES.csv` with columns for status, actual result, defect reference and notes.
