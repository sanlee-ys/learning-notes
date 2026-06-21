# 01 — Structured output via tool use

> **TL;DR** Hand the AI a form with fixed allowed answers (a "tool") and make it fill
> that out instead of writing prose — the API rejects off-menu answers *before* they
> reach your code.

## Plain idea

Normally an AI answers with a paragraph of text. Often I don't want a paragraph — I
want it to **fill in a form**: exact fields, and for some fields, only a fixed set of
allowed answers. "Tool use" (also called *function calling*) is the feature that lets
me hand the AI a form and make it fill *that* out instead of writing prose.

The catch it solves: if I just *ask* "reply in JSON with `category` and
`operational_domain`," the model usually does — but sometimes it writes `"aerial"`
instead of `"air"`, adds a chatty sentence before the JSON, or misspells a key. Then
my code has to detect and clean up the mess. With tool use, I define the form's rules
up front (including the exact allowed values, called an **enum**), and the API checks
the model's answer against those rules *before* handing it back to me. Off-menu
answers get rejected on their end, not mine.

## Analogy

The difference between asking someone "so, what do you want to order?" (they talk; I
scribble it down and hope I got it right) versus handing them a **checkbox menu**
(they can only tick boxes that exist). The menu makes a wrong answer almost
impossible — and I don't have to interpret handwriting.

## In my project

`defense-news-classifier/src/classify.py`. I define a `classify_article` tool whose
schema says: return `category` (one of 5 listed values) and `operational_domain` (one
of 6). I set `tool_choice` to *force* the model to use it. Because the API guarantees
the shape, the core function is about seven lines — make the call, grab the tool
result, return it. No JSON parsing, no "is this a valid label?" checks. The dataset
generator (`generate.py`) uses the exact same trick to produce correctly labeled
fake articles.

## Why it matters

- **The schema becomes the single source of truth** ("the schema is the contract").
  To add or rename a label, I change one place, not scattered parsing code.
- **My code gets boring** (in a good way) — no defensive cleanup, fewer bugs.
- **The model can't drift** to synonyms, because `"aerial"` isn't on the menu.

The tradeoff I accepted: it costs a few extra tokens (the schema rides along) and the
API call is a bit wordier than a plain "just chat" call. Cheap price for reliability.

## Go deeper

- How does the API actually *enforce* the enum — does the model never generate the bad
  value, or does the API reject it after? (Worth understanding the mechanism.)
- What is JSON Schema, the format these tool definitions are written in?
- What happens when an article genuinely fits two categories? (The form forces one
  answer — is that the right design, or should I allow "uncertain"?)
- How would the same thing look with a different provider (e.g. OpenAI's
  `response_format`)? Same idea, different wiring.
