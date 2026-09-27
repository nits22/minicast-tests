# MiniCast — Defects

Build: `minicast-release.apk` v1.0 · Device: CPH2491, Android 16 · Tester: Nitish Bector

| ID | Title | Sev | Case |
|---|---|---|---|
| BUG-001 | Pausing in the app leaves the notification showing Pause | 2 | TC-3.2, TC-7.2 |
| BUG-002 | Position runs past the end of the episode | 3 | TC-3.4, TC-4.2 |
| BUG-003 | Playback position carries over to episodes never played | 2 | TC-5.4 |
| BUG-004 | Resume OFF does not stop the carry-over | 3 | TC-5.3 |
| BUG-005 | +15s skips 30 seconds | 1 | TC-4.1, TC-4.10 |
| BUG-006 | Rotating resets the timer and seek bar to 0:00 | 2 | TC-9.1, TC-9.2 |
| BUG-007 | Settings is cut off in landscape and will not scroll | 2 | TC-9.4 |
| BUG-008 | With Don't Keep Activities, returning to the app restarts playback from 0:00 | 2 | TC-9.7 |
| BUG-009 | Notification keeps advancing after pause, with no audio | 2 | TC-9.7 |
| BUG-010 | Losing network: audio stops but the player keeps running, and never recovers | 2 | TC-10.4, TC-10.5 |
| BUG-011 | Position is lost when the app is killed in the background, even with Resume on | 2 | TC-9.6, TC-5.2 |
| TEST-ENV-001 | `pm clear` refused on this device (not an app bug) | – | TC-5.9 |

---

## BUG-001 — Pausing in the app leaves the notification showing Pause

**Severity** 2 · **Case** TC-3.2, TC-7.2 · **Automated** `test_pause_is_reported_to_the_system` (xfail)

Pausing with the app's own controls stops playback on screen but the media session keeps reporting PLAYING.
The notification and lock screen still show a Pause button on audio that is already paused.

**Steps**
1. Play *AI Writes Our Show Notes Now*. Let it reach ~0:35.
2. Tap pause in Now Playing. Audio stops, button changes to Play.
3. Pull down the notification shade.

**Expected** Notification and lock screen show Play. Session reports PAUSED.

**Actual** Notification shows Pause. Session reports PLAYING indefinitely.

**Evidence** Three readings over 12 seconds after tapping pause:

| | On screen | Player position | Player reports |
|---|---|---|---|
| straight after pausing | Play button, 0:37 | 37.6s | **PLAYING** |
| 9s later | Play button, 0:37 | 37.6s | **PLAYING** |
| 18s later | Play button, 0:37 | 37.6s | **PLAYING** |

The position never moves, so playback really is paused — only the state the app publishes is wrong.
The notification meanwhile still offers a **Pause** button.

**Scope** Now Playing and mini-player are both affected. Pausing from the notification or a media key
reports PAUSED correctly.

---

## BUG-002 — Position runs past the end of the episode

**Severity** 3 · **Case** TC-3.4, TC-4.2

**Steps**
1. Play any episode to the end without touching the controls.
2. Check the reported position.

**Expected** Position ≤ duration.

**Actual** Position exceeds the episode duration at the end of playback.

**Evidence** Position reported by the player once playback had stopped:

| Episode length | Player reported | Over by |
|---|---|---|
| 30s | 30.009s | 9 ms |
| 30s (separate run) | 30.052s | 52 ms |
| 10s | 10.084s | 84 ms |

**Note** Invisible to a listener — the on-screen timer still reads 0:30. It matters because any automated
check of "position never exceeds duration" will fail intermittently, and a progress bar calculated from it
can exceed 100%.

---

## BUG-003 — Playback position carries over to episodes never played

**Severity** 2 · **Case** TC-5.4 · **Automated** `test_resume_position_is_kept_per_episode` (xfail)

Saved position is not per episode. Opening a different episode starts it partway through, including
episodes never played.

**Steps**
1. Install fresh.
2. Play *AI Writes Our Show Notes Now* (1:00) for ~25s, pause.
3. Open *The Great Password Purge* (0:30) — not played since installing.

**Expected** Starts at 0:00.

**Actual** Episodes never played open partway through.

**Evidence** Clean install (uninstall + reinstall), positions read from the media session:

| Episode | Played before | Opens at |
|---|---|---|
| AI Writes Our Show Notes Now (1:00) | yes, paused at 27s | 27s |
| The Great Password Purge (0:30) | no | **30s — the end** |
| The Pivot That Wasn't (0:30) | no | 13s |

The 0:30 episode opens at its end and plays nothing until you seek back.

**Impact** Every episode's saved place is overwritten by whatever was played last. Blocks TC-5.1, TC-5.2,
TC-5.8 — none can be judged until this is fixed.

---

## BUG-004 — Resume OFF does not stop the carry-over

**Severity** 3 · **Case** TC-5.3

**Steps**
1. Settings → turn *Resume where I left off* OFF. Confirm it reads off.
2. Play an episode ~20s, pause.
3. Open a different episode.

**Expected** Starts at 0:00.

**Actual** Opened at 5s rather than 0:00.

**Evidence**

| Step | Observed |
|---|---|
| Resume setting | confirmed OFF on screen |
| Played AI Writes Our Show Notes Now to | 20s |
| Opened The Great Password Purge (never played), it started at | **5s** |

The setting does not govern this path, so opting out still gets BUG-003.

---

## BUG-005 — +15s skips 30 seconds

**Severity** 1 · **Case** TC-4.1, TC-4.5, TC-4.10 · **Automated** `test_skip_forward_moves_fifteen_seconds` (xfail)

The skip-forward button moves playback 30 seconds instead of 15. Skip back is correct, so the two controls
are asymmetric - a forward skip cannot be undone with a back skip.

**Steps**
1. Play *AI Writes Our Show Notes Now* (1:00).
2. Pause at a known position, e.g. 0:25.
3. Tap **+15s** once.
4. Read the position.

**Expected** 0:40.

**Actual** 0:55 — a 30-second jump.

**Evidence** Measured from a paused state proven stable (position read twice, two seconds apart, matching),
one tap, then re-verified:

```
1x     +15s: 25.6 -> 55.6 (+30.0)   -15s: 37.0 -> 22.0 (-15.0)
1.5x   +15s: 27.6 -> 57.6 (+30.0)   -15s: 37.1 -> 22.1 (-15.0)
2x     +15s: 31.0 -> 60.0 (+29.0)   -15s: 38.5 -> 23.5 (-15.0)
```

Same at every playback speed. The 2x reading is short only because it hit the 60s duration cap.

**Impact** The button says 15s and does 30s. A listener skipping past an ad or a section overshoots every
time. It also masked itself in other cases: on a 0:30 episode a +15s from 0:05 lands on the duration cap, so
it looks like correct clamping.

**Note** Able to reporduce this by the automated suite and manually also - the overshoot is easy to miss while listening, but obvious the moment the position is asserted.

---

## BUG-006 — Rotating resets the timer and seek bar to 0:00

**Severity** 2 · **Case** TC-9.1, TC-9.2

Rotating the phone resets the position shown in Now Playing to 0:00 and starts it counting again from
there. The audio carries on from the real position, so the screen and the audio disagree from then on.

**Steps**
1. Play *AI Writes Our Show Notes Now* and let it reach about 0:30.
2. Rotate the phone to landscape.
3. Compare the timer with what you hear.

**Expected** Timer and seek bar keep showing the real position, around 0:30.

**Actual** Timer resets to 0:00 and counts up from there while the audio continues from 0:30.

**Evidence** Two readings taken at the same moment: the timer shown on screen, and the real playback
position reported by the player.

| Moment | Timer on screen | Player actually at | |
|---|---|---|---|
| Portrait, playing | 0:32 | 32s | agree |
| After rotating to landscape | **0:09** | 44s | timer restarted from zero |
| After rotating back | **0:09** | 58s | restarted again |
| Portrait, paused | 1:00 | 60s | agree |
| After rotating to landscape | **0:00** | 60s | timer reset |

Watched by eye, the timer snaps to **0:00** the moment the screen rotates and then counts up again from
there. The 0:09 above is simply where it had got to by the time the automated reading was taken, about nine
seconds after the rotation. In that second row the audio was speaking "forty-four" while the screen read
nine seconds. The audio itself is unaffected throughout.

Happens while playing and while paused, and in both directions. Also reported independently by a second
tester.

**Impact** The seek bar sits at the wrong place, so dragging it or using -15s / +15s works from a position
the user can see is wrong. The only way back to a correct display is to leave the screen and return.

---

## BUG-007 — Settings is cut off in landscape and will not scroll

**Severity** 2 · **Case** TC-9.4

In landscape, the Settings screen is taller than the window and does not scroll, so the last setting cannot
be reached at all.

**Steps**
1. Open Settings.
2. Rotate the phone to landscape.
3. Try to reach *Notify when sleep timer ends*.

**Expected** All four settings reachable, scrolling if the screen is too short.

**Actual** *Notify when sleep timer ends* is off screen and the screen will not scroll. The setting cannot
be changed at all in landscape.

**Impact** A setting is unreachable in a supported orientation. Users who keep their phone in landscape, or
have rotation locked that way, cannot turn the sleep-timer notification on or off.

---

## BUG-008 — With Don't Keep Activities, returning to the app restarts playback from 0:00

**Severity** 2 · **Case** TC-9.7

**Steps**
1. Turn on *Don't keep activities* in Developer options.
2. Play an episode and let it run.
3. Send the app to the background, then bring it back.

**Expected** Playback continues from where it was.

**Actual** Playback restarts from 0:00.

**Evidence** Does not happen with *Don't keep activities* off, so it is specific to the screen being
destroyed and rebuilt rather than to backgrounding.

**Impact** Don't Keep Activities simulates what Android does to a backgrounded app under memory pressure.
Losing your place whenever the system reclaims the screen is the same user-visible failure as BUG-003,
reached by a different route.

---

## BUG-009 — Notification keeps advancing after pause, with no audio

**Severity** 2 · **Case** TC-9.7

**Steps**
1. Play an episode, then pause it.
2. Leave Now Playing - go to Search or the catalogue.
3. Send the app to the background.
4. Open the notification shade.

**Expected** The notification shows a paused episode, position static.

**Actual** The notification shows the episode as playing and the position keeps counting up, while no audio
is playing.

**Evidence** Reproducible with *Don't keep activities* both on and off, so it is not caused by that setting.

**Note** Probably the same underlying cause as BUG-001 - the app publishes a playing state while paused, and
here the system extrapolates a position from it. Filed separately because the symptom, the steps and the
surface are different; worth checking whether one fix closes both.

---

## BUG-010 — Losing network: audio stops but the player keeps running, and never recovers

**Severity** 2 · **Case** TC-10.4, TC-10.5

**Steps**
1. Play an episode.
2. Turn on airplane mode and keep watching.
3. Turn airplane mode off again and wait.

**Expected** Audio plays out the buffer, then the player pauses with a clear message. When the network comes
back, playback resumes or offers a working retry.

**Actual**
- Audio stops when the buffer runs out, but the timer and seek bar carry on as if it were still playing. No
  error is shown.
- Restoring the network changes nothing. Audio does not restart, no retry appears, and the timer is still
  advancing.

**Impact** A listener on a train sees a player that looks like it is working, with no sound and no
indication anything is wrong. Nothing tells them what to do, and coming back into signal does not fix it -
the only way out is to interact with the player directly.

**Note** Recorded as one defect in two parts. The app never registers that the stream failed, which is why
the timer keeps running; and because no failure was registered there is nothing to recover from when the
network returns. The recovery half may still need separate work once detection is fixed, so it is worth
re-testing both halves after a fix.

This is the same theme as BUG-001 and BUG-009 - the player's reported state drifting away from what is
actually happening to the audio.

---

## BUG-011 — Position is lost when the app is killed in the background, even with Resume on

**Severity** 2 · **Case** TC-9.6, TC-5.2

**Steps**
1. Confirm *Resume where I left off* is on.
2. Play an episode part way through and pause.
3. Send the app to the background and let the system kill it (or kill it from Developer options).
4. Reopen the app and play the same episode.

**Expected** Playback resumes from where it was left.

**Actual** It does not resume - the saved position is gone.

**Impact** Android kills backgrounded apps routinely, so this is not an edge case. The resume feature works
only while the app stays alive, which is the situation in which a listener least needs it.

**Note** Likely the same root cause as BUG-003. Both are explained by the app holding a single playback
position in memory rather than a per-episode value written to storage: one value explains the carry-over
between episodes, and being in memory only explains why it disappears when the process ends. Filed
separately because the symptom and the repro are different; worth checking whether one fix closes both.

---

## TEST-ENV-001 — `pm clear` refused on this device

Not an app defect, but it invalidates results if missed.

```
SecurityException: PID does not have permission android.permission.CLEAR_APP_USER_DATA
```

The command prints an exception rather than failing loudly, and the app keeps all data. An early S5 run
produced misleading results because of this. Wipe by uninstalling and reinstalling instead; the device shows
an install prompt that must be accepted by hand.

---

## Open observations (not filed)

**OBS-1** — Sleep timer arms and counts down with nothing playing. Covered by TC-6.8, pending a product
decision on whether the control should be disabled.

**Genre search** — `technology`, `travel`, `business` return "No shows found". Title and author both match, so
this looks deliberate. Raised with the PO in TC-1.3 rather than filed.
