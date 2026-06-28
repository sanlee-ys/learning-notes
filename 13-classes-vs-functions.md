# 13 — Classes vs functions: when to reach for a class

> **TL;DR** Use a plain function when you just transform input to output and forget it.
> Reach for a class only when you have state worth keeping, rules about what "valid" means,
> and behavior glued to that state. Most code is functions; a class has to earn its keep.

## Plain idea

A function is a verb: data goes in, a result comes out, nothing is remembered. A class is a
noun: a *thing* that holds some state and owns the behavior that acts on it. The beginner
trap is reaching for a class by reflex. The rule I actually use: only make a class when I have
all three of —

1. state that lives longer than one call,
2. invariants (rules about what a valid instance looks like), and
3. behavior that only makes sense paired with that state.

No three? A function is the simpler, truer tool.

## Analogy

A blender vs a recipe card. A **recipe** (function) takes ingredients and returns a smoothie;
it doesn't *remember* yesterday's smoothie. A **blender** (object) has state — on or off, full
or empty — and its "blend" button only makes sense given what's inside. You buy a blender when
you have something to keep and buttons bound to it; you don't buy a blender to add two numbers.

## In my project

The contrast shows up across two of my repos:

- **classifier — functions.** `defense-news-classifier/src/generate.py` is just constants and
  two functions (`generate_combo`, `main`). It's a stateless pipeline: hand it a
  (category, domain) pair, get back a list of articles. Nothing to hold, no invariant to
  guard — so wrapping it in a class would be a function wearing a costume.
- **notes-api — classes.** The notes API is all classes, because it has long-lived things
  with rules: a `Note` (must always have a title), a `NoteService` (owns the business rules).
  Each class is one *responsibility*.

The tell that a `dict` secretly wants to be a class: in `generate.py` I rebuild
`{"id": ..., "text": ..., "category": ..., "operational_domain": ...}` by hand every loop.
That fixed shape with nothing enforcing it is exactly what a Python `@dataclass` (or a Java
`record`) formalizes — see note 14.

## Why it matters

- **Simplicity by default.** Functions are easier to read, test, and move around. Classes add
  ceremony; only pay it when state/invariants/behavior justify it.
- **A class names a responsibility.** When one *is* warranted (the notes-api layers), the class
  boundary becomes the design — one place per rule.
- **It tells you when to refactor.** The moment a function grows a pile of config it keeps
  passing around (a client, a model name, retry settings), that's the signal to bundle them
  into an object — see note 14.

## Go deeper

- Where exactly is the line? Could `generate.py` legitimately become a `DatasetGenerator`
  class, and what would tip it over?
- Python dataclasses vs Java records vs a hand-written class — when is each the right amount of
  structure?
- "Composition over inheritance" — once I do have classes, how do I avoid deep class trees?
