# 03 — Reading the numbers: accuracy vs precision/recall/F1

> **TL;DR** Accuracy alone can hide a label that's quietly failing. Precision and recall
> (per label) show you *where* it fails; F1 blends them; macro-F1 stops a small bad label
> from hiding behind big easy ones.

## Plain idea

**Accuracy** is the obvious score: of everything, what fraction did I get right? It's
fine when every label is roughly equal — but it *lies* when one label is rare or hard,
because the easy labels drown out the struggling one in the average.

So for each label separately we ask two sharper questions:

- **Precision** — *when the model says "X", how often is it actually X?*
  Punishes false alarms. `TP / (TP + FP)`
- **Recall** — *of all the real X's out there, how many did the model catch?*
  Punishes misses. `TP / (TP + FN)`

These two pull against each other. Guess "X" for everything and you catch them all
(recall 100%) but cry wolf constantly (precision tanks). Guess "X" only when totally
sure and your guesses are all right (high precision) but you miss most of them (low
recall). **F1** is a single number that balances the two (it's their harmonic mean, so
it stays low unless *both* are decent).

**Macro-F1** averages each label's F1 with *equal weight*. That's the honest headline for
uneven problems: a small, failing label counts just as much as a big, easy one, so it
can't hide.

## Analogy

A metal detector at airport security:

- **Recall** = of everyone actually carrying metal, how many it caught. Misses are a
  recall problem (dangerous).
- **Precision** = when it beeps, how often there's really metal. False alarms are a
  precision problem (annoying, slow).

Crank sensitivity up → it beeps at everyone → recall 100%, precision awful. Crank it
down → rarely beeps → precision high, recall awful. The "right" setting depends on which
mistake costs you more.

## In my project

The counting is just boolean arithmetic over the predictions table — no ML library
needed (`src/eval.py`):

```python
tp = ((df.true == label) & (df.pred == label)).sum()   # said X, was X   ✅
fp = ((df.true != label) & (df.pred == label)).sum()   # said X, wasn't  ❌ false alarm
fn = ((df.true == label) & (df.pred != label)).sum()   # was X, missed   ❌ miss
precision = tp / (tp + fp)
recall    = tp / (tp + fn)
```

The payoff shows up in the `industry` label: **precision 1.000, recall 0.217**. Read
that out loud — *every time it said "industry" it was right, but it only caught 1 in 5
of the real ones* (the rest got mislabeled `procurement`). Plain accuracy would never
have told me that. It's also why my honest headline, macro-F1 (0.765), sits *below*
category accuracy (0.79): that one weak label drags the equal-weighted average down.

## Why it matters

Choosing the metric is itself a decision. Headline accuracy would have let me brag;
macro-F1 kept me honest *and* pointed a finger at the exact label to fix. Pick the
number that exposes your weakness, not the one that flatters it.

## Go deeper

- The precision/recall **trade-off** and "thresholds" — when you'd deliberately favor one.
- When recall matters more (cancer screening: don't miss) vs precision (spam filter:
  don't trash real mail).
- How to read a **confusion matrix** (which label gets mistaken for which) at a glance.
- Macro vs **micro** vs weighted averages — what each one is really measuring.
