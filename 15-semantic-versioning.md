# 15 — Semantic versioning: a version number is a promise

> **TL;DR** `MAJOR.MINOR.PATCH` isn't a counter — each digit is a promise about *what kind*
> of change happened. PATCH = a fix (same behaviour, more correct), MINOR = a new
> backward-compatible capability, MAJOR = a breaking change. Bump a digit and every digit to
> its right resets to 0.

## Plain idea

A version like `2.1.0` has three parts, and each one means something specific:

- **PATCH** (the last digit) — a **fix**. Behaviour is the same, just more correct. No new
  feature, and nothing a caller relies on changes.
- **MINOR** (the middle digit) — a **new, backward-compatible capability**. You *added*
  something; you didn't change what already worked. Bumping MINOR resets PATCH to 0.
- **MAJOR** (the first digit) — a **breaking change**. The contract callers depend on changed,
  so old assumptions no longer hold. Bumping MAJOR resets *both* MINOR and PATCH to 0.

The reset is the whole trick. Read straight down the last digit and it climbs *within* a line
(`2.0.1` → `2.0.2`) but snaps back to 0 the moment a digit to its left moves (`2.1.0`,
`3.0.0`). So the number isn't a tally of how many releases you've shipped — it's a claim about
*what this release did* to the people depending on you.

## Analogy

Think of book editions, not a page counter. Fixing typos and reprinting is a **patch** — same
book, fewer errors. Adding an appendix that doesn't touch the existing chapters is a **minor**
edition — extra value, and your old page references still work. Rewriting and renumbering the
chapters is a **new (major) edition** — anyone's notes against the old one are now wrong. The
edition number tells a returning reader, at a glance, whether their bookmarks still hold.

## In my project

`defense-news-classifier` is versioned this way (the plan lives in its `CLAUDE.md`). The
**output contract** — the `{category, operational_domain}` JSON the classifier returns — is the
thing each version makes promises about; that contract *is* the schema from note 01.

- `v1` → `v2.0.0` was a **MAJOR** bump: the whole methodology changed (synthetic self-grading
  → real text + human-labeled gold + retrieval), so prior results no longer compare.
- Planned `v2.1.0` (**MINOR**): scale the eval with the validated judge — a new capability, same
  output contract. Then `v2.1.1` (**PATCH**): fix whatever that larger run exposes.
- Planned `v2.2.0` (**MINOR**): tiered model routing — that's note 09, and it's additive, so
  callers are unaffected.
- Planned `v3.0.0` (**MAJOR**): add a `region` field. That changes `{category,
  operational_domain}` itself → it breaks the contract, so MINOR and PATCH reset to 0.

Each bump is **decided by the eval, not by default** (note 02): you measure first and only
spend a digit — or a premium model — where the numbers say it pays. That's why *scaling the
eval* (`2.1.0`) comes before *paying for routing* (`2.2.0`). The version itself is pinned in
`pyproject.toml` / `uv.lock` (note 11), and each milestone gets a git tag + a CHANGELOG entry.

## Why it matters

- **It's a promise, not a counter.** Someone depending on your output reads `2.1.0` → `2.1.1`
  and knows it's safe to take; `2.x` → `3.0.0` warns them to expect breakage. That's
  information they get for free, from the number alone.
- **It forces you to name the change.** Choosing patch-vs-minor-vs-major makes you say out loud
  whether you broke the contract — exactly the discipline note 01 (the schema *is* the
  contract) is about.
- **It pairs with measure-first.** Additive work (note 09) earns a MINOR; changing the contract
  earns a MAJOR; a fix earns a PATCH — and the eval (note 02) is what tells you which one you
  actually did.

## Go deeper

- For an ML system, what *exactly* is the "public contract"? Just the output schema, or also a
  quality bar ("accuracy won't regress")? Is a big accuracy drop a breaking change even when the
  JSON shape is identical?
- What are `0.x` versions and pre-release tags (`3.0.0-rc1`) for, and when do you graduate off
  `0.x`?
- How does [Keep a Changelog](https://keepachangelog.com/) map onto these bumps?
- Where's the line between MINOR and MAJOR when a change is *technically* compatible but shifts
  outputs enough that downstream results move?
