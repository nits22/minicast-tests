# Reflection

## With another week

**Long-soak playback** — an hour of continuous audio across screen-off, Doze, network changes
and interruptions. Everything here is minutes long; media apps break over time.

**Audio content, not just presence** — the suite proves sound reaches the output, not that you'd
hear *"fifteen"* at 0:15. Capturing the emulator's audio and transcribing the counting track with
a number-word grammar makes the transcript assertable: consecutive numbers prove no dropout, a
jump of exactly 15 proves a skip moved the audio and not the label, two numbers a second proves
2x is real. Left out on purpose — it needs a PulseAudio sink on the runner and is the most
fragile thing in the suite, so it belongs in a non-blocking job, not the gate.

**Wider device coverage** — one handset and one emulator, both recent. The minimum supported
version is untested, so is the first version where notifications can be refused. Manufacturer
power management deserves its own pass; that's where media apps die in the field.

**Test infrastructure** — device grid or cloud lab, an API-level matrix in CI, trend data so
flakiness is visible over time, the AVD snapshot cache I deferred to get a first green run, and
Macrobenchmark for start-up and scroll jank.

**Interruptions** — real calls, audio focus loss, Bluetooth handover. Manual for now; a few are
automatable by forcing focus loss with a second media app.

## AI: where it helped, where it didn't

**Good at** structure, CI boilerplate, and arguing a design decision to a conclusion. The
`xfail(strict=True)` approach to a build with known defects came out of one of those, and so did
the decision to keep waveform analysis out of the gate.

**Unreliable whenever it reported what the app did.**

| Claim | Reality | How I caught it |
|---|---|---|
| Search matches show title only | Matches title **and** author | Searched "Media" by hand, got The Daily Byte |
| `pm clear` gives a clean state | My handset refuses it; errors are printed, not raised | Checked factory defaults after a "wipe" — my own settings were still there |
| Resume leaks between episodes sharing a clip | One global position, any episode | Added the missing control: an episode with a *different* clip |
| mypy is type-checking the suite | Three settings meant it checked almost nothing | Misspelled a method on purpose; it passed |

**The rule that came out of it:** trust it on syntax and shape, verify anything it says about
behaviour. Every probe run now opens with a control query — `history` must return History
Rewind, or the harness is broken rather than the app.

## For the developers

**Two pause paths, one complete.** Pausing from the notification or a media key updates the
media session; pausing in the app doesn't. Several separate reports trace back to that split —
one fix may close more than one.

**Testability is cheap here and pays well.** Show cards and episode rows have no identifier, so
tests find them by visible text and climb to the nearest clickable ancestor. Brittle, and it
breaks entirely under localisation. One tag per row removes the largest source of flakiness in
the suite.

**Keep test ids and accessibility labels separate.** The transport buttons are currently found by
their spoken label — the screen-reader description doing a test's job. A test tag on Android and
a matching accessibility identifier on iOS, set from one constant, leaves the spoken label free
to read well.

**Resume may never have been per-episode.** Everything observed fits a single position held in
memory: it carries between unrelated episodes, dies with the process, and the settings toggle
doesn't govern it. Worth confirming before treating any of it as a regression.

**The emulator's audio lags its own UI by seconds.** Not an app defect, but it broke a test that
passed on hardware — worth knowing before tuning timings against CI.
