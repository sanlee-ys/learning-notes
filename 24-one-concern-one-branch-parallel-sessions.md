# 24 — One concern, one branch: working in parallel agent sessions

> **TL;DR** You can run several agent sessions at once, but they **can't see each other's
> uncommitted work** — the only shared coordination point is the repo's `main`. So: one
> concern per session → one short-lived branch → one PR → merge fast → delete. And
> **parallelize by independent *file*, not by *task***, because generated/aggregated files
> (indexes, registries, build outputs) can't be merged and must be updated by a single hand.

## Plain idea

Running multiple sessions in parallel is tempting — more hands, more throughput. But each
session is in its own sandbox and is *blind* to what the others are doing until their work
lands on `main`. That blindness is the whole constraint, and a few rules fall straight out of
it:

- **One concern per session.** If the deliverable doesn't fit in a sentence, it's two sessions.
- **Branch from fresh `main`, merge fast, delete the branch.** The longer a branch lives, the
  more it drifts from a `main` that other sessions are moving.
- **Parallelize by file, not by task.** Cut the work along files nothing else touches. Two
  sessions editing the same file will collide — and *generated or aggregated* files (a README
  index, a nav config, a built HTML/SVG) are the worst case, because there's no sensible way to
  merge two independently-regenerated copies.

That last point has a name worth internalizing: the **content-vs-wiring split**. The
independent *content* can be written in parallel; the shared *wiring* that stitches it together
must be done once, by a single integrator, after the content lands.

## Analogy

Several cooks in one kitchen sharing a single pantry (`main`). They can work different dishes
at once with no problem — until two reach for the same ingredient (the same file). And the one
shared shopping list taped to the fridge (an index or registry) has to be updated by *one*
person; if three cooks each rewrite the whole list from memory, you don't get a merged list,
you get three conflicting ones.

## In my project

This rule exists because it was learned the hard way: parallel sessions once built the *same*
CI workflow three times (PRs #4 / #5 / #6), each forking off a stale `main` and blind to the
others. Nothing was wrong with any one session — the coordination was missing.

The fix showed its worth when this notes hub gained a batch of new notes at once. The note
*files* are independent content, so they were drafted in parallel — but the README registry,
the nav config, and the regenerated `index.html` / `concept-map.html` / category-map SVG are
shared **wiring**, so a single integrator did that registration-and-rebuild pass *once*, after
the files existed. Generated files especially can't be merged, so keeping that wiring in one
hand is what stops the duplicate-CI disaster from repeating. These rules are written down in
`CLAUDE.md` (note 22) so every session starts already knowing them. Coordination on `main` is
also where releases live — every milestone is a tag on `main` (note 15).

## Why it matters

- **Short-lived branches barely drift,** so merges stay clean and you skip most conflicts
  instead of resolving them.
- **By-file parallelism avoids the collisions** that by-task parallelism quietly creates — two
  "separate" tasks that both touch `README.md` are not actually independent.
- **Serializing the wiring** keeps generated/aggregated files coherent. The content scales out;
  the integration stays singular.
- It's a genuinely *different* discipline from normal solo git flow — the new constraint is the
  blindness between sessions, and every rule here is just a response to it.

## Go deeper

- The **integrator** role when many sessions run at once: one session owns merging to `main`
  and keeping it green; the others stay feature-scoped and rebase on its merges.
- How do you *detect* that another session is mid-flight on a file before you start — branch
  names, open PRs, an unpushed commit on a shared checkout?
- Where's the line where parallelism stops paying — when does coordinating N sessions cost more
  than just doing the work in one?
