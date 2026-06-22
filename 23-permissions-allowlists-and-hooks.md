# 23 — Permissions, allowlists & hooks: guardrails for an AI agent

> **TL;DR** By default the agent asks before each tool runs. You shape that with an
> **allowlist** — `allow` rules that run silently, `ask` rules that still prompt, `deny` rules
> that block outright (precedence: **deny > ask > allow**). **Hooks** are a separate,
> programmable gate that inspects a command and can block it *regardless* of the allowlist. The
> goal: zero friction on the routine-and-reversible, a hard stop on the destructive.

## Plain idea

An agent that can run shell commands and edit files needs a leash, but a leash that prompts
you for *everything* trains you to click "approve" without reading — which is worse than no
leash. The fix is to be precise about what runs unattended:

- **`allow`** — pre-approved patterns (e.g. `Read`, `Edit`, `Bash(git commit:*)`). These run
  silently.
- **`ask`** — still prompt, even though something broader would allow them. This is how you
  carve a dangerous *exception* out of a permissive rule.
- **`deny`** — never run, no prompt.

When rules overlap, **deny beats ask beats allow**, so a narrow `ask` for `git push --force`
overrides a broad `allow` for `git push`.

**Hooks** are a different mechanism. A hook is a script the agent runs *before* (or after) a
tool call; it sees the command and can veto it. Because it's code, it can enforce things a
static allowlist can't express — "block any test run that isn't measuring coverage."

## Analogy

A building access badge. Most doors open with a tap (allow). A couple of sensitive rooms need
a second sign-off even though you have a badge (ask). The vault is off-limits to everyone
(deny). The **hook** is the metal detector at the entrance — an automated check everyone walks
through regardless of which badge they hold. Badge rules are about *who you are*; the detector
is about *what you're carrying*.

## In my project

My global `~/.claude/settings.json` allowlists the routine, reversible work — `Read`, `Edit`,
`Write`, and everyday `git` / `python` / `uv` / `gh pr` commands — so the day-to-day stops
prompting. `git push --force` sits in the `ask` list, so it still stops me even though plain
`git push` is allowed. Genuinely destructive commands (`rm`, `git reset --hard`, `git clean`)
are deliberately *left off* the allowlist, so they fall through to a prompt by default.

Separately, a **PreToolUse hook** enforces test coverage: it denies a `pytest` run that
doesn't pass `--cov`, *even though* `pytest` is allowlisted. That's the division of labor —
the allowlist decided "pytest is fine to run unattended," and the hook adds "…but only if it's
measuring coverage" (note 20). Instructions in `CLAUDE.md` (note 22) *tell* the agent to
measure coverage; the hook makes it so the agent *can't* skip it. Guidance versus guardrail.

## Why it matters

- **It removes friction without removing the safety net.** The 95% that's safe runs silently;
  the 5% that's irreversible or outward-facing still stops you. Approval fatigue — rubber-
  stamping every prompt — is itself a security risk, and a good allowlist cures it.
- **Hooks turn a best practice into a guarantee.** "Always measure coverage" or "never read
  `.env`" (note 10) stops being a thing you *hope* gets followed and becomes something that
  *can't* be skipped, by a human or an agent.
- **Precedence makes exceptions cheap.** You can allow a whole family of commands and still
  surgically force-prompt the one dangerous variant, without hand-listing every safe case.

## Go deeper

- A `deny` rule that blocks reading secrets (`.env`, key files) — defense in depth on top of
  note 10's "never hardcode keys."
- Scope: global vs project vs personal-local settings — where should an allowlist live so a
  teammate's machine isn't loosened by your preferences?
- The blunt "bypass everything" mode — when (if ever) is turning the leash off entirely the
  right call, and what do you give up?
