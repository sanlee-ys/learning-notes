# 09 — Tiered model routing: pay for the big model only when it pays

> **TL;DR** Don't run the expensive model on every request. Use a cheap, fast model as the
> default and **escalate to the premium one only for the hard cases** the eval says it can't
> handle.

## Plain idea

There's a menu of models: smaller = cheaper and faster, bigger = smarter and pricier. The
lazy choice is "use one model for everything." **Tiered routing** says: choose the tier
*per task*, guided by what the numbers actually show you need.

The eval already told me where money should and shouldn't go:

- **Operational domain is at 97.3%** — the cheap model nails it. Spending more buys nothing.
- **Category is stuck at ~79%**, but the ceiling is **label ambiguity** (industry vs
  procurement is genuinely fuzzy — note 03), *not* the model being too weak. A bigger model
  won't un-blur a fuzzy definition across the board.

So the v2 plan: keep `claude-sonnet-4-6` as the workhorse on every article, and escalate to
a top-tier model (e.g. Opus) **only** on the low-confidence boundary cases — running the
premium model on ~15% of articles instead of 100%. Most of the quality, a fraction of the
cost.

A second use of the same idea: once v2 uses **real** data, I can't auto-grade against an
AI-made answer key anymore (note 08). There I'd reserve the top tier as an **LLM judge** —
the expensive model grades, the cheap model does the everyday work.

## Analogy

A hospital triage desk. A nurse handles the routine cases fast and cheap; only the
complicated ones get escalated to the specialist. You don't send every sniffle to the
senior surgeon.

```
article ─▶ sonnet-4-6  (cheap, fast)
              │
        confident? ──yes──▶ done            (~85% of articles)
              │
              no ──▶ Opus  (premium)         (~15%, the fuzzy ones)
```

## In my project

This lives in `CLAUDE.md` as a v2 idea — not built yet. The guiding principle is written
there in one line:

> model tier is a per-task cost/quality knob decided by the eval, not a default — measure
> first, escalate only where it pays.

## Why it matters

It's the same discipline as note 02: let the measurement drive the decision. The eval
doesn't just tell you *if* you're good — it tells you *where to spend*.

## Go deeper

- How do you measure "confidence" to decide who gets escalated? (The model doesn't hand you
  a clean confidence number for free.)
- The cost / latency / quality triangle — you usually optimize two at the expense of the third.
- **LLM-as-judge** — using a strong model to grade outputs, and where *that* can mislead.
- Break-even math — escalating costs more per call, but only on a slice; does it net out?
