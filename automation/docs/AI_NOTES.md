# How I used AI on this exercise

Claude, throughout. Mostly for structure, review, and the fiddly parts of Appium and CI. The
decisions about what to test — and every claim about how the app behaves — I checked myself.

## Where it was strongest

- **Scaffolding** — page objects, fixtures, the Allure hook, CI boilerplate. Tedious, not interesting.
- **Knowing what makes emulator jobs flaky** — the KVM rule, boot-completed waits, the AVD cache.
- **Arguing a design decision to a conclusion.** Two that changed the outcome: `xfail(strict=True)`
  for a build with known defects, and keeping waveform analysis out of the CI gate.
- **Doing refactors properly when pushed** — locators into their pages, the device factory.

## Where I found problems in its code

| What was wrong | How it surfaced |
|---|---|
| `PlaybackProbe` was decoration — three references, nothing enforcing it | Asked whether it was *used*. Added an `isinstance` check plus mypy; mypy then found a real bug on its first run (`timeout: int`, caller passing `0.5`) |
| mypy itself was checking almost nothing — `tests/` excluded, untyped bodies skipped, fixtures typed `Any` | Misspelled a method on purpose and it passed clean |
| `audio_active()` parsed **the wrong command's output**, then fell back to "is anything on this phone playing?" | A test failed; the raw `dumpsys audio` section it claimed to read didn't exist |
| `is_paused()` read `content-desc` from the button container, where it's always empty | Always False, so `resume()` never fired — test died 40 lines later with "position never reached 21s" |
| Assertion messages **re-queried** the values, so failures reported numbers that were never compared | `UI says 58s, system says 59s` for a failure that can't fail at a 3s tolerance |
| A regex rewrite mangled one locator: `accessibility_id("Back")` became `resourceId("Back")` | A whole run lost to a missing back button |
| Its CI workflow had a multi-line `for` loop inside the emulator action's `script:` | The provided starter's own comment warns about this — it would have failed on the first run |
| A fixture woke "the device" before one had been resolved | Fine with one device; `adb: more than one device` the moment a second appeared |

## The prompts

**1 — Plan first, no code.** *"5-8 Android E2E tests, 1.5-2 hours, emulator in GitHub Actions.
I'm leaning Python + Appium + pytest + uv. Compare against Maestro for this exercise. Don't
write test code yet — tell me if you disagree with the stack."*
Told me Appium is the flakier choice and Maestro would be greener for less code — it just isn't
Python. Kept Appium and spent the budget on wait-hardening rather than test count.

**2 — How far to take audio.** *"Explain waveform capture and STT end to end. Can I verify the
exact number being spoken, or only that audio is playing? What's overengineering here?"*
Best conversation of the exercise. The counting track makes a transcript an assertable timeline.
Also the most fragile thing I could put in a gate — so: media session + `dumpsys audio` in CI,
waveform designed but not implemented.

**3 — Minimum skeleton.** *"Give me the smallest sensible project structure. Industry standard,
but don't over-engineer and use existing libraries."*
Used as a starting point; the structure changed as the app taught me things.

**4 — Locators and Page Factory.** *"Why are locators in one file when they could live in their
page classes? And can we follow Page Factory?"*
Locators moved onto the pages. On Page Factory I got a straight no rather than a yes-man
answer — `@FindBy` is a Java/C# feature, and imitating it here would be the over-engineering I'd
just ruled out.

**5 — Probes.** *"What is PlaybackProbe? Is it actually being used?"*
Asking whether something was *used* was more productive than asking how it worked. See the table
above.

**6 — Device factory.** *"If multiple devices are attached and I want a specific one, that should
be handled better — driver and capabilities too."*
It was, and it exposed a silent hazard: Appium took the device from a capability while the probe
shelled out to adb, with nothing keeping them in sync. I also pushed back on being told iOS
simulator discovery "couldn't be implemented without an iOS build" — wrong, `simctl` needs Xcode,
not an app.

**7 — Parallel runs.** *"Can it support xdist across multiple devices of the same platform?"*
4m42s to 2m43s on a phone plus an emulator, and it immediately exposed three things one device
hides — including the emulator's audio running seconds behind its own UI, which is the CI timing
risk found before CI.

**8 — CI.** *"There's a starter workflow with the assignment. Can it be extended?"*
Building on the starter caught the multi-line shell bug above. The run moved into
`ci/run_e2e.sh`, and I deferred the AVD cache deliberately — green first, fast second.

## The rule

Reliable on syntax and shape. Unreliable the moment it reports what the app *did*. Every probe
run now opens with a control query — `history` must return History Rewind, or the harness is
broken rather than the app. Everything in the bug reports I reproduced by hand, most of it
outside the test framework entirely.
