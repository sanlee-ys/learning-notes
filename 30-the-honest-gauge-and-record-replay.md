# 30 — The honest gauge: every rendered value traces to a measurement

> **TL;DR** telltale is a terminal harness that shows what several AI coding
> tools do and spend. It has one rule: a rendered value must come from a
> measured tool output. A value the program inferred is omitted or marked as an
> estimate. Zero and absent are different values, and a test fails the build
> if a render shows them the same way. The test fixture for a UI that talks to
> live vendors is a recording of a real run, played back through the same
> renderer. The shipped copy of that fixture is scrubbed: the shape is real,
> and the words are synthesized.

## Plain idea

A dashboard is a set of claims. Each number on it says "somebody measured
this." Most dashboards break that promise in a quiet way. They fill a gap with
a guess. They show `0` when a source was not read. They compute a figure from
two other figures and show it in the same font as a measured one. The reader
cannot tell the three cases apart.

The honest-gauge rule removes the guess. A cell may show only a value that came
from the tool's own output. If the tool did not say it, the cell shows nothing.
If the program computed it, the cell says so with a mark.

That rule forces one distinction that most schemas skip. "Zero" and "absent"
are two different facts, and "absent" itself splits in two:

- **Zero.** The vendor reported zero. The gauge draws a full empty track.
- **Absent now.** The vendor can report this field, but it has no value at this
  moment. The gauge draws a dash.
- **Cannot know.** The vendor never exposes this field. The gauge drops the
  column for that vendor.

A gauge that shows all three as `0%` tells the reader that three sessions are
in the same state. Two of them were not measured at all.

## Analogy

A fuel gauge with a broken sender wire must not read "empty". A needle at
"empty" is a claim about the tank. A dark gauge is a claim about the wire. A
driver who sees the needle at "empty" refuels. A driver who sees a dark gauge
repairs the wire. The two readings cause different actions, so the dashboard
must keep them different. A dashboard that moves the needle to "empty" when the
wire breaks sends the driver to the wrong repair.

## In my project

**telltale** (`github.com/sanlee-ys/telltale`) is a Go binary with three
surfaces: a statusline segment, a watch TUI (`telltale hud`), and a room
(`telltale council`) that sends one brief to several vendor CLIs side by side.
The rule is stated in `README.md` under "The honest-gauge rule", and it is the
first design decision in `docs/design.md` (ADR-001, with §4a.1 "Absence is two
different things").

Three mechanisms hold the rule in place:

1. **Every optional field is a pointer, and there is no sentinel number.** In
   `internal/model/session.go`, a nil pointer means "no value". The value `0`
   always means the vendor said zero. An adapter that cannot source a field
   declares that fact (`CapNone`) instead of a plausible guess.
2. **A golden test pins the render.** `internal/hud` renders one session at 0%
   context and one session with no context source, and the test asserts that
   the two rows differ (`internal/hud/testdata/golden/zero-vs-absent.txt`). If
   a change makes the rows equal, the build fails.
3. **An estimate carries a mark.** A value the adapter computed, such as a
   context percentage, renders with a leading `~`. The `telltale snapshot` JSON
   document says the same thing in fields: `0` is a measured zero, `null` is no
   reading now, `"unsupported"` lists the fields this vendor never exposes, and
   `"estimated"` lists the fields the adapter computed.

The CI workflow (`.github/workflows/ci.yml`) runs the built binary against
fixtures and asserts on stdout. One assertion fails the run if a quota window
renders with no rate-limit data behind it. Another fails it if a dollar sign
renders for a vendor that reports no cost. The repo tests the rendered string,
not only that the code ran (note 20).

The rule reaches past the code. `docs/design.md` §1 lists the three gates for
the v1 tag. One gate says the README must be verified against the tip of the
code: every claim, keybinding, and badge checked. A comment in the README badge
slot applies the same rule to badges: a badge states a fact somebody measured,
and it names who measured it. A star count or a download count is a number
telltale does not measure, so no badge shows one.

### The second idea: record and replay as the test fixture

The room talks to live vendor CLIs. Each seat costs money per turn, needs a
login, and answers differently every time. That is the worst possible test
dependency. A test that spawns a real vendor is slow, non-deterministic, and
billed to the operator's account. Note 26 keeps a real dependency short. Here
the dependency cannot run in a test at all. So the suite for the room never
starts a vendor, and a guard in `internal/council/main_test.go` panics if a
test reaches a spawn with a binary the machine can resolve.

Then how do you test what the room draws over a real run? You record one.
`telltale council --record <file>` writes the room's event stream as JSON
lines: the room line, each dispatch, each event from each seat, and each gate
decision, with millisecond offsets (`internal/council/recording.go`).
`--replay <file>` opens a room over the file and puts the same records through
the same code path a live room uses. The clock is the recording's clock, so
`Render` stays pure over its state, and two plays of one file produce one
frame. Every replayed frame says `REPLAY` in words, and `enter` refuses to
dispatch: "nothing here is live".

The recording is the fixture. The replay is the test. `docs/design.md` §9.56
records the design, and its measurement section records what the first replay
of a real file found: a defect in how the room attributed the exit of a seat's
old process. The synthesized fixtures in the suite had not caught it. A real
recording did.

**Why the shipped fixture is scrubbed.** A recording holds content: the
operator's brief, each vendor's reply, session ids, and the workspace path.
telltale is a public repository, and its fixture rule says fixtures are
synthesized and hold no real session content. The two rules meet in
`telltale council replay-scrub <in> <out>` (`internal/council/scrub.go`). It
reads one recording and writes a second file with the same shape and every
word replaced. `examples/demo.jsonl` is a real room of 2026-09-03 after that
pass. Its room line says `scrubbed: true`, and both `--replay` and
`telltale council replay-check <file>` repeat the claim. A stranger can play a
real room on a machine with no vendor installed, and the real recording stays
with its operator.

`replay-check` is the honest-gauge rule turned on the recording itself. It
lists what the file carries (the workspace, the seats, the session ids, the
tool lines, the gate cards, and the size of the prose), and it says that it
did not read the prose. You know what you are about to share before you share
it.

## Why it matters

- **A rendered guess looks the same as a measured value.** The reader cannot
  correct for a difference they cannot see. The only fix is at the render: omit
  the guess, or mark it.
- **Zero-versus-absent is a bug class, not a bug.** It is the same class as a
  test suite that passes because it asserts nothing (note 20), and as a check
  that cannot fail (the "false green" entry in the glossary). The diagnostic
  question is the same each time: can this surface tell "measured zero" from
  "never measured"?
- **A real recording finds what a synthesized fixture cannot.** Synthesized
  fixtures pin the shape of a render. A recording pins the truth of one run,
  and the first real one found a defect on its first play.
- **Scrub, do not redact.** A redacted recording is a second truth that
  differs from the run. A scrubbed copy keeps the shape, replaces every word,
  and says so on its first line. Note 03 makes the same point about numbers: a
  figure you cannot trace is a figure you cannot read.

## Go deeper

- Where else does the zero-versus-absent collapse hide? A `0` default in a JSON
  schema, a `COUNT(*)` over a table that was never loaded, a chart library that
  draws a missing point on the axis. Each one turns "not measured" into
  "measured zero".
- How much of a UI's test suite can be a replay? The replay covers what the
  room draws. It cannot cover a vendor's live handshake, a resume across a
  respawn, or a real gate on a real write. `docs/design.md` §9.56 keeps a list
  under the heading "Not verified here". What list does your project keep?
- Note 28 records spans; the room records events. Both are a timed stream that
  a viewer plays back. Which parts of one format would serve the other?
- "Verified against tip" is a v1 gate for the README, and a person applies it.
  What would that gate look like as a CI check?
