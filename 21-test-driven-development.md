# 21 — Test-driven development: red, green, refactor

> **TL;DR** Write a failing test *first* (red), write the smallest code that makes it pass
> (green), then clean up with the test holding your work in place (refactor). The test describes
> the behavior before the behavior exists, so the code is built to a spec instead of measured
> against one after the fact.

## Plain idea

Most people write the code, then write a test that agrees with whatever the code already does.
TDD flips the order. First you write a test for behavior that doesn't exist yet, and you run it
and watch it **fail** — that's *red*. Then you write the *minimum* code to make it pass — that's
*green*. Then, with a passing test guarding you, you tidy the code — that's *refactor*. Repeat in
tiny loops.

The failing step isn't a formality. A test that's never seen red might be testing nothing — maybe
it passes because of a typo, or because it asserts something always true. Watching it fail *for
the right reason* proves the test can actually catch the bug it's meant to catch.

Writing the test first also forces a design question before you've sunk effort into an answer:
*what should this thing do, and how would I even call it?* You feel an awkward API while it's
still cheap to change.

## Analogy

It's writing the answer key before you write the exam. If you decide what "correct" looks like up
front, you can't quietly redefine "correct" to match whatever you happened to produce. Tests
written *after* the code grade the student who also wrote the answer key — they tend to confirm
what's there, not catch what's missing.

## In my project

I've leaned on this loop professionally, and both repos are shaped the way TDD leaves things —
small tests that pin one behavior each.

In `notes-api`, `NoteServiceTest` is a clean red-green target. Take a test like
`delete_throws_andSkipsDelete_whenMissing`: red is writing it against a `delete()` that doesn't
yet check existence — it fails because nothing throws. Green is adding the `existsById` guard and
the `NoteNotFoundException`. The test also asserts `verify(repository, never()).deleteById(...)` —
so the *refactor* step (reordering the guard, renaming things) is safe, because that line locks in
"must not delete when missing." The service takes its repository through the constructor (note 14),
so the test hands it a `@Mock` with no database — fast enough to run on every tiny loop.

`NoteControllerTest` shows the same loop at the HTTP edge: a test like
`create_withBlankTitle_returns400_andSkipsService` states the rule first — a blank title is a 400
and the service is never touched — and you build validation until it goes green.

On the Python side, `defense-news-classifier/tests` mirrors it: `test_classify.py`,
`test_retrieve.py`, `test_eval.py`, each pinning one piece, with a `conftest.py` of shared fakes so
a test never needs a real API call.

## Why it matters

- **The test can actually fail.** Seeing red first proves the test isn't a green-painted no-op
  that would miss the real regression.
- **It's a design tool, not just a safety net.** Writing the call before the code surfaces an
  awkward interface while it's still cheap to fix.
- **Refactoring stops being scary.** Green tests are permission to clean up — if you break
  something, a test goes red the same second.
- **Coverage comes out honest.** The lines exist *because* a test demanded them, not the other way
  round (note 20 on testing & coverage).

## Go deeper

- The model-world cousin: **eval-driven development** (note 02) — write the eval first, then
  improve the model toward it. Same "define correct before you change anything" instinct, applied
  to behavior you can't unit-test.
- When does TDD *not* pay? (Throwaway spikes, exploratory code where you don't yet know the shape.)
- "Test behavior, not implementation" — why over-specific tests (asserting *how*, not *what*) make
  refactoring harder, not easier.
- Outside-in vs inside-out TDD — start from the HTTP test and drive inward, or from the unit and
  build out?
