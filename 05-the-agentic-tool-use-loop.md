# 05 — The agentic tool-use loop

> **TL;DR** An "AI agent" is just a loop: ask the model → run any tool it requests → feed
> the result back → repeat until it answers. About 15 lines of code. That's the whole
> trick.

## Plain idea

In the classifier I force *exactly one* tool call and I'm done. An **agent** is the
open-ended version: I don't know in advance how many steps it'll take to answer. So I run
a loop:

```
┌─────────────────────────────────────────────┐
│ 1. send the conversation to the model        │
│ 2. did it ask for a tool?                     │
│      • no  → it gave a final answer → STOP    │
│      • yes → run the tool(s), append results  │
│             → go back to step 1               │
└─────────────────────────────────────────────┘
   (plus a safety cap so it can't loop forever)
```

The model is the decision-maker; the loop is the engine; the tools are the hands. "Agent"
= model + loop + tools. Nothing more mystical than that.

## Analogy

A research assistant you email a question. They reply either with an answer, or with
"please look up X for me." You look up X, email it back. They might ask for one more
thing, then answer. You repeat until they're done — and you'd cut them off after, say,
10 round-trips so they don't spiral.

## In my project

`kb-agent/agent/agent.py`, the `ask()` method — a *manual* loop (I didn't use the SDK's
auto-runner, so the control flow is visible and easy to follow):

```python
for _ in range(MAX_TOOL_ITERATIONS):                 # safety cap (10)
    resp = client.messages.create(..., tools=TOOLS, messages=self.messages)
    self.messages.append({"role": "assistant", "content": resp.content})

    if resp.stop_reason != "tool_use":               # model gave a real answer
        return final_text(resp)                       # → done

    for block in resp.content:                        # else: run what it asked for
        if block.type == "tool_use":
            result = execute_tool(block.name, block.input)
            tool_results.append({"type": "tool_result",
                                 "tool_use_id": block.id, "content": result})
    self.messages.append({"role": "user", "content": tool_results})
```

Two things that are easy to get wrong: you **must** append the assistant turn (it carries
the tool *request*) and you **must** send each tool result back with the matching
`tool_use_id`. Mismatch those and the conversation breaks.

## Why it matters

This little loop *is* what people mean by "AI agent." Seeing it written out demystifies
the whole category. It also makes the failure modes obvious: runaway loops (hence the
cap), and cost — every trip through the loop is another paid API call.

## Go deeper

- How does the model "know" it's done? (It stops asking for tools.)
- **Memory**: kb-agent keeps `self.messages` across turns so it remembers the chat — what
  changes if you reset it each question?
- When to hand-roll the loop vs use the SDK's built-in tool runner.
- Guardrails: capping iterations, capping spend, and what to do when the cap is hit.
