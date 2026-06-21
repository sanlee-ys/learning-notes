# 04 — Tool use / function calling, the general idea

> **TL;DR** A "tool" is a function you *describe* to the model so it can ask you to run
> it. This is how an AI does things beyond talking — and you stay in control, because the
> model only *requests* the call; your code decides what actually happens.

## Plain idea

By itself, a language model only produces text. It can't search your files, do reliable
math, or call an API. **Tool use** (a.k.a. *function calling*) bridges that gap. You hand
the model a menu of actions — each is a name + a description + an input form (schema).
The model can't run anything itself; instead it *requests* a call: "please run
`search_kb` with `query='pandas'`." Your code runs it and hands the result back.

There are two flavors of the same primitive:

- **(a) Shape the output** — force the model to fill a form so you get clean structured
  data instead of prose. (That's note 01.)
- **(b) Give it abilities** — let it look things up, calculate, hit an API, etc. (That's
  the agent in note 05.)

Both my projects use the same feature for these two different purposes.

## Analogy

The model is a sharp colleague on the phone who **can't touch your computer**. You say:
"Here are buttons I can press for you — SEARCH and LIST. Just tell me which." They say
"press SEARCH for 'pandas'." You press it and read them the result. They keep going.
The model is the brain; *you* are the hands. Nothing happens that you didn't run.

## In my projects

- **Classifier** — flavor (a). One tool, `classify_article`, *forced* every call. Pure
  output-shaping; the model never "decides" anything about tools.
- **kb-agent** — flavor (b). Two tools, `search_kb` and `list_projects`, and the model
  *chooses* when (and whether) to call them.

A detail that matters: the tool's **description** is a prompt. kb-agent's schemas are
deliberately prescriptive about *when* to call each one —

```python
"description": ("Search the personal knowledge base of projects and libraries. "
                "Call this whenever the user asks about a tool, library, design "
                "decision, or how something was used in a project.")
```

Good descriptions visibly improve the model's tool-picking.

## Why it matters

This single primitive is the bridge between "a model that talks" and "software that does
things." Once you see that structured output *and* AI agents are both just tool use, a
lot of the mystery evaporates. And the safety story is built in: the model can only
*ask*; what the tool actually does is ordinary code you wrote and control.

## Go deeper

- Forcing a tool (`tool_choice`) vs letting the model choose — when to do which.
- What happens when the model wants to call **several tools at once** (parallel calls).
- The risk surface: tools with **side effects** (writing files, sending email) — the
  model proposes, but you must decide what's safe to auto-run.
- How tool descriptions act as prompts that steer tool selection.
