# 20 — Testing & coverage: knowing what's exercised

> **TL;DR** Tests catch a change that quietly broke something. **Coverage** measures how much of
> your code the tests actually ran — but "ran" isn't "checked," so high coverage of weak tests is
> still weak.

## Plain idea

A **test** is a small program that runs your real code with a known input and asserts the answer
is what you expect. Run them after every change: if one goes red, you broke something you can
*see*, before it ships. Tests are to code what evals are to the model (note 02): an automatic
check that a change didn't break things.

But a green test suite has a blind spot — it only tells you the tests you *wrote* passed. It says
nothing about the code you forgot to test. **Coverage** fills that gap by recording which lines
and branches actually executed during the run. It turns "I think that's tested" into a number.

The catch worth tattooing on your hand: coverage measures what code was *exercised*, not that it's
*correct*. A test with no real assertions still lights up coverage. High coverage of weak checks
is still weak.

## Analogy

Coverage is the *checklist* of rooms the cleaner walked through; it is not proof any room is
actually clean. Walking into the kitchen counts as "covered" even if you never wiped a counter.
The checklist finds the rooms nobody entered — a real blind spot — but it can't tell you whether
the work inside was any good.

## In my project

The `notes-api` repo makes both halves concrete. Its tests sit at a few levels (a *test pyramid*):
fast pure-logic unit tests with no framework, API tests that drive real HTTP routes against a
throwaway database, and a thin full-boot check. The lesson baked in: push most testing down to the
fast unit level and use the slow, realistic tests sparingly.

Coverage taught me the line-vs-branch lesson firsthand. Back when notes-api was Java it reported
**~97% line but only ~69% branch** under **JaCoCo** — and that gap *is* the point. "Did this line
run" is easy to max out; "did we test *both* sides of each `if`" is the stricter, more honest
number. The remaining branch gaps were deliberately-skipped defensive paths, because coverage is a
**guide, not a target** — chasing 100% just breeds low-value tests. Its real win was finding
PUT/DELETE endpoints that no test touched at all.

The defense-news-classifier enforces the same discipline as a gate — and since the port, notes-api
(now Python too) runs the same way, both on `pytest-cov`:

```bash
uv run pytest --cov=src --cov-report=term-missing
```

so every run prints exactly which lines weren't exercised. Untested code can't hide. The kind of
fragile, real-world machinery worth wrapping in tests — checkpoint/resume and retries (note 12) —
is exactly where an untested branch bites you later.

## Why it matters

- Tests turn "I changed something, hope it's fine" into a button you press that says yes or no.
- Coverage finds the **holes** — code no test runs at all — which is a genuine, fixable blind spot.
- But it stops there: it can't judge whether your assertions mean anything. Use it to find
  untested code, then make sure the tests filling those holes actually *check* something.

## Go deeper

- **Line vs. branch coverage** — why branch is the honest one, and why a high line number can
  flatter you.
- What does a **good assertion** look like, versus one that just executes code for the metric?
- The **test pyramid**: why lots of fast unit tests plus a few slow integration tests beats the
  reverse.
- How a coverage **gate** in CI keeps a number from quietly sliding down over time.
- Mocks and fakes — testing one layer without booting the whole app.
