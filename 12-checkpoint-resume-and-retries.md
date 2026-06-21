# 12 — Checkpoint/resume and retries: surviving flaky API runs

> **TL;DR** A 300-call job *will* hit a hiccup. Save progress after every call (so a crash
> costs one item, not the whole run) and auto-retry the transient errors (so a blip doesn't
> kill the job).

## Plain idea

The eval makes ~300 API calls and takes a few minutes. Over that many network calls,
*something* eventually fails — a dropped connection, a momentary server error, a rate-limit
bump. Two cheap habits make the job robust:

1. **Checkpoint / resume.** Write each prediction to disk *immediately* after its call. On
   restart, skip any article that already has one. A crash at call 250 costs you call 250 —
   not calls 1 through 249.

2. **Retry with backoff.** Wrap the call so that on a *transient* error (a 500 server blip, a
   429 rate-limit) it waits and tries again — and the wait **grows** each time (e.g. 2s, then
   4s). That "exponential backoff" gives an overloaded server room to recover instead of you
   hammering it.

## Analogy

Checkpointing is **saving your game after every level** instead of only at the end — die on
level 9 and you respawn at 9, not level 1. Backoff is **knocking on a busy door**: no answer,
so you wait a little longer each time instead of pounding nonstop.

## In my project

`src/eval.py`:

```python
# Resume: skip articles that already have a saved prediction. Each prediction
# is written right after its API call, so a crash never loses more than one call.

def classify_with_retry(...):     # exponential backoff: 2s → 4s
    # retry transient 500 / 429 errors, then give up
```

The generator also drops a `0.5s` sleep between calls to stay comfortably under the rate
limit in the first place — avoiding the error beats retrying it.

## Why it matters

Without these, one network blink at minute 4 means redoing everything — and re-paying for
it. Resumable, retry-tolerant jobs are a habit that scales far past this project: any long
batch over a flaky network wants both.

## Go deeper

- **Idempotency** — designing a job so that re-running it is safe and never double-works.
- Which errors are safe to retry (transient: 429 / 500 / timeout) vs which aren't (400 bad
  request — retrying won't help).
- **Jitter** — adding randomness to the backoff so many clients don't all retry in lockstep.
- Where the checkpoint should live — a CSV here; a database or queue for bigger jobs.
