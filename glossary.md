# Glossary

Personal reference for terms I keep using across notes and projects.
Not exhaustive — just the ones I've had to think through carefully enough to write down.

---

## contract

An explicit, agreed-on interface between two pieces of a system — what one side
promises to produce and what the other side is allowed to assume.

In practice: a function signature, a JSON schema, an API endpoint shape, a Kafka
message format. The value isn't the document — it's that both sides can evolve
independently as long as the contract holds.

**In my projects:** the ADR system uses contracts to separate concerns across repos.
`notes-api` calls the classifier's HTTP `/classify` seam (SYS-004) and writes the labels
back to its own store as namespaced tags (SYS-005); the classifier just promises the
`/classify` shape and knows nothing about notes. Neither side needs to know how the other
works internally — they only need the contract.

**Related:** idempotency (what the contract can safely promise about repeated calls)

---

## eval

A test set of examples where I already know the right answer, used to measure
whether an AI model or prompt is actually doing what I think it is.

An eval is scored — you get a number (accuracy, F1, precision/recall) that lets you
compare "before" vs "after" a change. That's what makes it different from eyeballing
a few outputs.

**See note:** [02 — Eval-driven development](02-eval-driven-development.md)

---

## eval-as-a-harness

Promoting an eval from a one-off script into a repeatable test that runs in CI,
guarding against regressions the same way a unit test does.

The upgrade path: you have a CSV of examples → you write a script that scores them →
you wire that script into GitHub Actions → a PR that quietly drops accuracy from 0.91
to 0.85 gets caught before it merges.

**In my projects:** the classifier eval (see metrics below) is the target for this
treatment (SYS-007 / evals-as-CI gate).

---

## idempotency

A property of an operation: running it once produces the same result as running it
N times. Safe to retry; no side effects accumulate.

The classic example: `PUT /notes/{id}/tags` on the notes-api. The enrichment task writes
the classifier's labels back as tags and may reprocess the same note (a retry, a re-run).
The endpoint *replaces* the classifier-owned tags rather than appending, so applying it once
or five times lands the same note — 200, no duplicates.

Contrast with a non-idempotent operation like `POST /tags/add`, which would append
a duplicate tag on every call.

**Why it matters:** idempotency is what makes *at-least-once* delivery safe. Whether the
trigger is a retried background task or a message queue that re-delivers (Kafka guarantees
at-least-once), a handler that isn't idempotent turns a harmless duplicate into a bug. The
notes-api writeback is built to replace, so reprocessing converges instead of accumulating.

---

## classifier metrics

The numbers used to evaluate how well the classifier labels notes.

| Metric | What it measures |
|---|---|
| **Accuracy** | Share of all predictions that were correct. Good baseline, misleading on imbalanced classes. |
| **Precision** | Of everything I labeled X, how many were actually X? (Correctness of positive calls.) |
| **Recall** | Of everything that was actually X, how many did I catch? (Coverage.) |
| **F1** | Harmonic mean of precision and recall. The go-to single number when classes are imbalanced. |
| **Confusion matrix** | Full breakdown: what got confused with what. This is where you see the `industry` vs `procurement` mix-up, for example. |

**In my project:** the eval CSV lives in the classifier repo. The current reported score
is F1 ≈ 0.91 on the held-out set (as of the last eval run). Confusion matrix revealed
the defense-company label overlap that drove the first prompt revision.

**See note:** [03 — Reading the numbers](03-reading-the-numbers.md)
