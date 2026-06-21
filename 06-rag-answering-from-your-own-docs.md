# 06 — RAG: answering from your own documents

> **TL;DR** RAG = **fetch the relevant notes first, then let the model answer using
> them.** It makes the AI speak from *your* documents instead of its training memory —
> and lets it admit when it doesn't know.

## Plain idea

A model only knows what it absorbed during training. It doesn't know your private notes,
and it doesn't know what changed last week. **RAG** (Retrieval-Augmented Generation) fixes
this in two steps:

1. **Retrieve** — find the chunks of *your* documents most relevant to the question.
2. **Generate** — hand those chunks to the model along with the question, and let it
   answer *from them*.

Because the answer is grounded in real text you provided, the model makes far less up,
and it can point at *which* document it used.

## Analogy

**Open-book vs closed-book exam.** Closed-book, the model answers from memory and can be
confidently wrong. RAG turns it into an open-book exam where you've already flipped to the
right page — it reads, then answers.

## In my project

kb-agent *is* a RAG system. The "documents" are Markdown files about my projects and
libraries (`kb/`). When I ask a question:

1. `search_kb` finds the most relevant chunks (note 07 explains how "relevant" works).
2. The agent reads them and writes an answer.

The honesty rules live in the system prompt, and they're the important part:

```
Answer questions using the search_kb ... tools rather than your own prior knowledge.
When you state a fact that came from the KB, mention the source file. If the tools
return nothing relevant, say so plainly instead of guessing — do not invent details.
```

So it **cites the source file** and is told to say "I don't know" when the KB is empty on
a topic — instead of confidently inventing project details.

## Why it matters

RAG is how you make an AI useful over **private or fast-changing** information *without*
retraining anything. And the "cite your source / admit when you've got nothing" pattern is
what keeps a RAG assistant trustworthy — grounding plus a way to fail honestly.

## Go deeper

- **Chunking**: documents get split into pieces before retrieval — chunk too big and you
  bury the answer in noise; too small and you lose context. How to size it.
- What to do when retrieval grabs the *wrong* chunk (the model can only be as good as what
  it's handed).
- "Grounding" and citations — tying each claim back to a source.
- How do you even *evaluate* a RAG system? (Did it retrieve the right docs? Did it answer
  faithfully from them? — ties back to note 02.)
