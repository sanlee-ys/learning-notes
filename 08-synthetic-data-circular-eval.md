# 08 — Synthetic data and the "circular eval" trap

> **TL;DR** I made the test data with the *same* AI that takes the test. That's cheap and
> perfectly balanced — but the score measures whether the model **agrees with itself**, not
> whether it'd handle real, human-written news.

## Plain idea

To measure a classifier you need examples with known-correct answers. I had three options:

- **Scrape real news** — needs a scraper, licensing review, and humans to label each article.
- **Find an existing labeled dataset** — none matched my two-label scheme.
- **Generate labeled examples with the AI** — one API call per `category × domain` combo
  (30 combos × 10 = 300 articles), each one born with its label already attached.

I picked generate. The upside is real: no scraping, no licensing, no human labeling, and
every label gets exactly 10 examples — *perfectly balanced* (note 03 on why balance helps).

The catch is in the name: **circular**. The same model wrote the data *and* grades it. So a
high score really means *"the classifier agrees with the labels the generator chose"* — the
model is consistent with itself. It does **not** prove it would do well on messy,
human-written news it's never seen. I'm measuring **consistency**, not **generalization**.

There's a subtler bias too: AI-written snippets are more uniform in style and vocabulary
than real news, so a model tuned on them would overfit to that tidy style and stumble on
the real thing.

## Analogy

Writing your own exam questions *and* the answer key, then acing the exam. Impressive-
looking, but it only proves you're consistent with yourself — not that you've learned the
subject. The real test is questions **someone else** wrote.

## In my project

The README and `decisions/003-synthetic-data-only.md` call this out *loudly* — it's listed
as the project's #1 limitation, not buried:

> the same model generates and classifies the data. Numbers measure in-distribution
> consistency, not generalization to real-world news.

The honest v2 move is written down: re-run the eval against a small set of **human-labeled
real** articles.

**Update (v2):** *that move has since shipped. The classifier was graded on a 54-snippet
human-labeled gold set of real news — the non-circular answer key v1 couldn't produce —
scoring category accuracy 88.9% (macro-F1 0.906) and operational-domain accuracy 88.9%
(macro-F1 0.894), with the once-weak `industry` label now at F1 1.000. The 79% / 97%
figures below are the historical synthetic baseline; the circular-eval lesson is exactly
why they couldn't be trusted on their own.*

## Why it matters

Every eval has a quiet question behind it: *do I trust this number?* (ties to note 02).
Naming the circularity is what keeps the 79% / 97% figures honest. A number you *can't*
trust is worse than no number — it feels like progress while telling you nothing.

## Go deeper

- What would a *real* eval set need? (Real sources + human labels + a check that labelers
  agree with each other.)
- **In-distribution** vs **out-of-distribution** — the idea underneath the whole trap.
- Could I keep synthetic data for prompt development but switch to real data for the *final*
  eval only?
- **Data leakage** in general — any time the answer sneaks into the question.
