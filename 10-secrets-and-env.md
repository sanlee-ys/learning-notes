# 10 — Secrets and the `.env` pattern

> **TL;DR** Your API key is a password. Keep it in an untracked `.env` file and load it at
> runtime — never typed into the code, never committed to git.

## Plain idea

The Anthropic key bills to your account, so it's a secret like a password. Two hard rules:
(1) it must **not** live in your source code, and (2) it must **not** be committed to git
(where it'd sit in the history forever — and be public the moment you push). The standard
solution is the **`.env` pattern**, which is just two files with two jobs:

- **`.env`** — holds the *real* key. Listed in `.gitignore`, so git ignores it. Lives only
  on your machine.
- **`.env.example`** — a committed, **secret-free** template (`ANTHROPIC_API_KEY=`) that
  documents *what* keys the project needs without revealing them.

At runtime the key is loaded from `.env` into an environment variable, and the code reads it
from there — never hardcoded.

## Analogy

`.env.example` is the *labeled empty key hook by the door* — it tells everyone "a house key
goes here." `.env` is the *actual key*, which you keep in your pocket, not hanging where
anyone walking past could grab it.

## In my project

The classifier reads `ANTHROPIC_API_KEY` from the environment, and the README documents the
workflow:

```bash
cp .env.example .env        # then paste your real key into .env
uv run --env-file .env python src/eval.py   # inject the key for this run
```

There's an honest caveat written down too: because `.env` is gitignored, it's
**machine-local by design**. A fresh clone or a new laptop has no `.env`, so you recreate it
(copy the template, paste the key). That's not a bug — it's the *entire point* of keeping
secrets out of git.

## Why it matters

A key committed to a public repo gets scraped by bots within minutes and runs up your bill.
The `.env` split — real secret ignored, empty template committed — is the simplest pattern
that keeps the secret *out* while still telling the next person *what's needed*.

## Go deeper

- If a key ever *does* land in a commit, deleting the line isn't enough — it's in the
  history. The fix is to **rotate** (revoke + reissue) the key.
- Environment variables vs dedicated **secret managers** (Vault, cloud secret stores) for
  larger setups.
- How `.gitignore` decides what git skips — and the habit of running `git status` before
  every commit to catch a stray `.env`.
- Why even `export KEY=...` in your shell beats hardcoding (it just vanishes when the shell
  closes).
