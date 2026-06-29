# 02 — Eval-driven development

> **TL;DR** Before trusting any AI change, run a test set with known answers and compare
> the score before vs after — a change that *reads* better can quietly make the model
> worse.

## Plain idea

An **eval** is a test set: a pile of examples where I already know the right answer.
"Eval-driven" means that before I trust *any* change to the AI, I run the whole eval
and compare the score **before** vs **after**. If the score didn't go up, the change
didn't help — no matter how clever or clean it looked.

This matters more with AI than with normal code, because AI changes are *persuasive*.
A reworded prompt can read smarter to a human while quietly nudging the model's
behavior the wrong way. You cannot feel a 3-point accuracy drop by skimming a few
outputs. The number catches what your eyes flatter.

## Analogy

A blood test before and after a diet change, instead of going by how you feel.
You can feel fine, even great, while your cholesterol quietly climbs; the lab
number doesn't care how good the plan sounded.

## In my project

This isn't hypothetical — it's the best lesson in the whole repo.

The classifier confused two labels, `industry` and `procurement` (both involve defense
companies and money). The "obvious" fix: spell the distinction out more sharply in the
prompt — *"a firm winning a contract is procurement; a firm reporting earnings is
industry."* It read better. I ran the eval. It got **worse**: category accuracy fell
79.0% → 76.7%, and `industry` recall dropped from 0.22 to 0.10 (it caught even fewer
of them). The sharper wording gave the model a cleaner rule for dumping borderline
stories into the wrong bin. I reverted and kept the original.

The machinery: `src/eval.py` runs the classifier on all 300 articles and writes the
score, a confusion matrix (which labels get mistaken for which), and a log of every
wrong answer. The failed experiment is recorded in `CHANGELOG.md` so I don't repeat it.

## Why it matters

- It's the only thing that reliably separates a **real** improvement from a
  **plausible-sounding** one.
- It makes prompt-tweaking a *measured* activity, not a vibes activity.
- The misclassification log turns failures into a to-do list — I can read the exact
  cases the model blows and look for patterns.

## Go deeper

- What makes a *good* eval set? (Big one: my labels were made by the same AI that I'm
  grading — see note 08 on the "circular eval" trap.)
- How do I read a confusion matrix at a glance?
- When is a score difference real vs just random run-to-run noise? (I built a
  `stability.py` to measure that wobble — worth a note of its own.)
- Precision vs recall vs F1 — what each one actually means (note 03).
