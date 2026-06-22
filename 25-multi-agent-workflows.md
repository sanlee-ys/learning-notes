# 25 — Multi-agent workflows: fan-out, and the collision boundary

> **TL;DR** Instead of one agent grinding through everything in sequence, spin up several
> focused agents that work in **parallel**. The catch is the same one from note 24:
> parallelizing by *task* when the tasks touch the same file or repo causes git races and
> merge conflicts. The rule is **parallelize by independent file/repo, not by task**. Four
> patterns keep it coherent: *read-only fan-out*, *by-repo write fan-out*, *freeze shared
> specs first*, and the *integrator* who owns the aggregate and runs last.

## Plain idea

A single agent doing a big job works through it one step at a time — read this repo, then
that one, then write the change, then update the index. A lot of that is *independent* and
doesn't need to be serial. Multi-agent (or "subagent") orchestration spins up several
focused agents at once, each owning a slice, and lets them run in parallel. You get the
slices back faster, and each agent keeps a tight, single-purpose context instead of one
agent juggling everything.

**When to use it:**

- **Genuinely independent work** — slices that don't depend on each other's output.
- **Broad fan-out search or audit** — "check all six repos for X"; each agent reads one.
- **Parallel execution across separate repos or files** — one lane per repo/file that
  nothing else in the batch touches.

When the work is actually sequential (step B needs step A's result), or when every slice
edits the same file, the parallelism is fake and you're better off with one agent.

## The failure mode

This is the heart of the note. The tempting mistake is to split the work **by task** —
"agent 1 does the rename, agent 2 adds the test, agent 3 updates the docs" — when those
tasks all land in the *same file or repo*. The agents can't see each other's uncommitted
work (note 24): they each branch off the same `main`, each edit the shared file blind, and
when their branches come back you get git races and merge conflicts. Nothing was wrong with
any one agent; the *partition* was wrong.

The rule is the fix: **parallelize by independent file/repo, not by task.** Cut the work
along boundaries where the slices physically cannot touch the same bytes. If two "separate"
tasks both write `README.md` or both regenerate an index, they are not independent and must
not be two parallel lanes.

## The patterns that work

Four named shapes, ordered from "nothing to merge" to "merging is the whole job":

1. **Read-only fan-out** — one agent per repo for an *audit*. Every agent only reads and
   reports; nobody writes. Fully independent, nothing to merge, so you can fan out as wide
   as you have repos. The cheapest and safest parallelism there is.
2. **By-repo write fan-out** — one agent per repo, each making isolated commits on its own
   branch. Because the unit of parallelism is a whole repo, two agents never share a file.
   Safe to run wide; each lane lands on its own.
3. **Freeze shared specs first** ("define once, implement many") — when several agents must
   *agree* on a contract (an API shape, a label schema, a data format), don't let each
   agent invent its own version in parallel — they'll drift. Pin the spec centrally **first**,
   then hand that one frozen spec to each agent so their independent implementations can't
   disagree.
4. **Integrator pattern** — one agent owns the *aggregate*: the generated/registry files, or
   the final consistency sweep. It runs **after** the parallel content lands, never beside
   it. This is note 24's content-vs-wiring split as an orchestration rule: **never
   parallelize edits to a generated file** — registries, indexes, built HTML/SVG can't be
   merged, so a single hand updates them once, last.

## In my project

All four showed up in real batches across my three repos (`defense-news-classifier`,
`kb-agent`, `notes-api`) and this notes hub:

- **Read-only fan-out:** a six-repo audit — one agent per repo, each reading its tree and
  reporting findings, none of them writing. Fully independent, so it ran as wide as the repo
  count with nothing to reconcile at the end.
- **By-repo write fan-out:** a "quick wins" pass — one agent per repo applying small,
  isolated fixes on its own branch. Because each lane was a whole repo, no two agents ever
  reached for the same file.
- **Freeze shared specs first + integrator:** a cross-repo contract-hardening batch around
  the `/classify` seam. `kb-agent`'s `classify_snippet` tool POSTs to
  `defense-news-classifier`'s `/classify` endpoint, so the request/response contract is
  shared between repos. We **froze that contract spec centrally first**, then four
  repo-agents implemented their own side against the frozen spec in parallel — so their
  independent changes couldn't drift apart — and a final **integrator** did a consistency
  sweep once everything had landed.

This very note was written as **one lane of that batch**: the note files are independent
content, drafted in parallel, while the README registry, the `mkdocs.yml` nav, and the
regenerated `index.html` / `concept-map.html` / category-map SVG are shared wiring the
integrator rebuilds once, after the files exist (note 24).

## Why it matters

- **Speed from parallelism** — independent slices finish concurrently instead of one long
  serial crawl, and each agent keeps a smaller, sharper context.
- **…but only if you respect the collision boundary.** Partition by file/repo, not by task,
  or the parallelism you bought back gets spent resolving merge conflicts (note 24).
- **Freeze-specs keeps parallel work *consistent*** — pinning the contract first stops N
  independent implementations from quietly disagreeing.
- **The integrator keeps it *coherent*** — generated and aggregated files get updated once,
  by one hand, after the content lands, so nothing collides on the un-mergeable artifacts.

## Go deeper

- How wide is too wide? At some point coordinating N agents (and reading N reports) costs
  more than doing the work in one — where's that line for an audit vs. a write batch?
- Detecting collisions *before* you fan out: how do you tell two slices secretly share a
  file or a generated artifact, so you don't discover it at merge time?
- The orchestrator's own role — does the parent agent stay a pure dispatcher, or can it also
  be the integrator? When does "one agent owns the merge" (note 24) beat a separate
  integrator lane?
- Passing context between agents cheaply: how much does each subagent really need handed to
  it, versus re-deriving, to keep the fan-out fast?
