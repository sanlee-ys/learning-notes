# 22 — Steering an AI agent with CLAUDE.md

> **TL;DR** `CLAUDE.md` is a file the agent reads at the *start of every session*, so you
> state your standing instructions once instead of re-explaining them each time. Two layers:
> a **global** file (`~/.claude/CLAUDE.md`) that applies to every project, and a **project**
> file checked into the repo. Global holds the durable *principles*; the project file holds
> the *specifics*. It's the difference between an assistant that forgets every morning and one
> that remembers the house rules.

## Plain idea

Left alone, an AI coding agent starts each session as a blank slate — it doesn't know your
label definitions, your stack, or how you like to work, so you end up re-typing the same
context. `CLAUDE.md` fixes that: it's a plain Markdown file the agent loads automatically and
treats as instructions that *override its defaults*.

There are two layers, and the split matters:

- **Global** (`~/.claude/CLAUDE.md`) — applies to *every* repo you touch. Put the things that
  are true regardless of project: how you want decisions explained, your working cadence, the
  general rules you follow everywhere.
- **Project** (`<repo>/CLAUDE.md`, committed) — applies to *this* repo. Put the specifics: the
  label schema, the tech stack, the build commands, the project's own conventions.

The rule of thumb is *principle goes global, instantiation goes local*. A principle stated
once at the top doesn't get duplicated into every repo, where copies drift out of sync.

## Analogy

It's the onboarding handbook you hand every new contractor on day one. The company-wide
handbook (global) covers "how we work here" — it's the same for everyone. The project binder
(local) covers "here's what *this* job needs." You don't re-explain the company dress code on
every project; you write it once, up top, and point new people at it.

## In my project

`defense-news-classifier/CLAUDE.md` carries the project specifics: the `{category,
operational_domain}` label definitions, the uv-based stack, the multi-session git rules, and
the semantic-versioning roadmap (note 15). My global `~/.claude/CLAUDE.md` carries the
durable working style — small steps with checkpoints, "explain the why," surface design
choices rather than silently deciding.

The layering earned its keep recently: the "parallelize by file, not by task" rule (note 24)
started life only in the project file, but it's true for *every* repo I run parallel sessions
in — so it moved up to global, while the project kept its own concrete collision-hotspot list
as the local instantiation. Same idea, stated once at the principle level and once at the
specific level, instead of copy-pasted. The file also encodes hard constraints the agent must
honor — e.g. "read the API key from an environment variable, never hardcode it" (note 10).

## Why it matters

- **It stops the re-deriving.** Context you'd otherwise repeat every session is read once, up
  front. Decisions you've made stay made.
- **It's version-controlled.** The project file lives in the repo, so every session — and every
  teammate — shares one source of truth, and changes to "how we work" show up in code review
  like anything else.
- **It scales with layering.** Global principles don't get duplicated into N repos where they'd
  drift; specifics stay where they're relevant. Guidance lives here; the *enforcement* of it
  lives in permissions and hooks (note 23) — telling the agent what to do is separate from
  constraining what it's allowed to do unsupervised.

## Go deeper

- Precedence when global, project, and a personal local file all say something — which wins?
- What belongs in `CLAUDE.md` versus the agent's persistent *memory*? (Instructions you author
  vs. facts the agent records as it learns how you work.)
- When does a `CLAUDE.md` get too long to be useful — and how do you keep it from becoming a
  wall of rules the agent (or you) stops actually reading?
