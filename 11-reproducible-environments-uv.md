# 11 — Reproducible environments: uv and lockfiles

> **TL;DR** "Works on my machine" usually means mismatched library versions. A **lockfile**
> pins the exact version of everything, so every machine — yours, a teammate's, CI —
> installs the identical environment.

## Plain idea

Your code depends on libraries, and libraries have versions that change behavior over time.
If all you write down is "I need `anthropic`," two people can install two different versions
and get two different results. The fix is two files with two distinct jobs:

- **`pyproject.toml`** — what you *want*, usually a flexible range: `anthropic>=0.40.0`.
  Human-edited.
- **`uv.lock`** — what you *actually got*: the one exact version that range resolved to,
  plus every sub-dependency, frozen. Machine-generated.

`uv sync` reads the lockfile and builds a local `.venv` with *exactly* those versions.
`uv run <cmd>` runs a command inside that env — no manual "activate the virtualenv" step.
Because the lockfile is committed, anyone who runs `uv sync` gets a matching setup.

## Analogy

`pyproject.toml` is a recipe that says *"some flour."* `uv.lock` is the note that says *"King
Arthur bread flour, this exact bag"* — so the cake comes out the same in every kitchen.

## In my project

Both repos use uv. The classifier README spells out the loop:

```bash
uv sync --group dev          # build .venv from uv.lock (exact pinned versions)
uv run python src/eval.py    # run inside that env — no activation needed
```

A `requirements.txt` is kept in sync as a **pip fallback** for anyone who isn't using uv.

## Why it matters

Reproducibility is the difference between a bug you can recreate and a ghost you can't.
Pinned versions also mean a dependency can't silently update overnight and break you — you
upgrade *on purpose* by re-locking, never by surprise.

## Go deeper

- "Abstract" deps (ranges, in `pyproject.toml`) vs "pinned" deps (exact, in the lockfile) —
  why you need both.
- How and when to **update** the lockfile deliberately (re-resolve → test → commit).
- Why `.venv` is gitignored but `uv.lock` is committed.
- How CI uses the same lockfile to test in a clean environment every run.
