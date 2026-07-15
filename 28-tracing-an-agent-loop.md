# 28 — Tracing an agent loop: seeing where the time and tokens go

> **TL;DR** An agent loop (note 05) is a little distributed system: one question
> fans out into several model calls and tool calls. When it's slow or expensive,
> "which part?" is unanswerable by staring at the code — you need a **trace**: a
> timed, nested record of every step. I added OpenTelemetry to my kb-agent so each
> `ask()` emits a span tree — the turn, each model call, each tool call — carrying
> token counts, per-step latency, and each tool's status. The design trick that
> keeps it from being a tax: instrument against the tracing *API* always, but only
> turn the *recording* on when you ask for it, so it's a genuine no-op by default.

## Plain idea

A single agent turn isn't one thing that happens — it's a loop. The model thinks,
asks for a tool, you run it, feed the result back, it thinks again, maybe asks for
another tool, and eventually answers. Three model calls and two tool calls can hide
behind one `ask("...")`.

So when a turn takes eight seconds, "why?" has many possible answers: a slow tool?
a big model call? too many loop passes? And when a turn costs more than you expected,
"where did the tokens go?" is just as murky. You can't fix what you can't see, and a
`print()` here and there doesn't compose into an answer.

A **trace** does. It's a tree of **spans**, where each span is one operation with a
start time, an end time, and some labelled facts (**attributes**). Nest them and you
get a picture of the whole turn:

```
kb_agent.ask                     (2.9s, 2 passes)
├─ chat sonnet                   (0.8s, in=120 out=8)
├─ execute_tool search_kb        (1.4s, status=success)
└─ chat sonnet                   (0.7s, in=210 cache_read=120)
```

Now the questions answer themselves: the tool was the slow part, and the second
model call read 120 tokens *from cache* instead of paying for them again (note 27's
world — the cost levers you actually have). That last fact is invisible in the code;
the trace surfaces it.

## What to hang on each span

The span *is* the measurement, so put the deciding numbers on it:

- **On each model call:** input / output tokens, and the cache counts if you use
  prompt caching. This is where cost lives (notes 03 and 09 — reading the numbers,
  and paying for the big model only when it pays).
- **On each tool call:** the tool's name and its result status — and you get its
  latency for free, because that's just the span's duration.
- **On the whole turn:** how many loop passes it took. A turn that quietly takes
  nine passes is a different problem from one that takes two.

There's a small standard for these names — OpenTelemetry's **GenAI semantic
conventions** (`gen_ai.usage.input_tokens`, `gen_ai.tool.name`, and so on). Using
the standard names instead of inventing your own means any off-the-shelf viewer
(Jaeger, Tempo, Honeycomb) understands your traces with no configuration.

## The design trick: instrument always, record on demand

The trap with observability is that it becomes a tax — overhead on every run, noise
in every log, a hard dependency the tests have to work around. The fix is a split
that's worth internalising, because it's how mature tracing libraries are built:

- Your code talks to the tracing **API**. Its default implementation is a **no-op** —
  it accepts your spans and throws them away, costing essentially nothing.
- The **SDK** — the part that actually records spans and ships them somewhere — is
  wired up *only when you ask for it*, behind an environment variable.

So the instrumentation lives in the code permanently, but it's inert until you flip
`KB_AGENT_TRACING=1`. A normal run pays nothing. The offline test suite (note 20) is
untouched. And when you *do* want to see inside a turn, you turn it on and the spans
start flowing — to the console while you're poking at it, or to a real collector when
you want to keep them. One more guard: only compute the expensive attributes when a
recording span is actually listening (`if span.is_recording()`), so "off" is truly
free, not just quiet.

## Why this is the same instinct as everything else here

"Build the eval before you trust the model" (note 02). "Read the numbers, don't trust
the vibe" (note 03). "Know the cost before you launch the fan-out" (note 27).
Tracing is that instinct pointed at a running agent: **don't guess where the time and
tokens went — measure it, per step.** The loop in note 05 is where the work happens;
this is how you see it happen.
