# 07 — Embeddings & vector stores: search by meaning

> **TL;DR** An *embedding* turns text into a list of numbers that captures its meaning, so
> you can find related text by **closeness in meaning** rather than matching exact
> keywords. A *vector store* holds those numbers and finds the nearest ones fast.

## Plain idea

Keyword search breaks the moment the words don't match. Ask *"how do I keep secrets
safe?"* but the note says *"API key management"* — zero shared words, zero results, even
though it's the perfect note.

An **embedding** fixes this. It converts a piece of text into a long list of numbers (a
**vector**) arranged so that texts with **similar meaning** land near each other in that
number-space. To search, you embed the *question* into the same space and grab the
nearest note-vectors. "Secrets" and "API key management" end up close, so it just works.

A **vector store** (a database like ChromaDB) is what holds all those vectors and answers
"find me the nearest ones" quickly, even over thousands of chunks.

```
"API key management"  ─embed─▶  [0.12, -0.88, 0.05, ... ]  ┐
"keeping secrets safe" ─embed─▶ [0.14, -0.85, 0.07, ... ]  ├─ near each other
"pandas dataframes"   ─embed─▶  [0.91,  0.10, -0.4, ... ]  ┘  far away
```

## Analogy

A library where books are shelved by **topic-closeness**, not alphabetically — cooking
next to nutrition next to gardening. To find a book you walk to the right *neighborhood*,
even if you never knew the exact title.

## In my project

kb-agent, `scripts/index.py`. It chops the Markdown KB into chunks and embeds each one
into **ChromaDB** using a small model, `all-MiniLM-L6-v2`. The notable design choice:

> The embedding model runs **locally** — no API key, no per-call cost, and nothing leaves
> the machine.

At query time, `search_kb` embeds the question with the same model and asks Chroma for the
nearest chunks. That nearest-neighbor lookup is the **Retrieve** step that powers the RAG
in note 06.

## Why it matters

Embeddings are the engine under RAG *and* under "semantic search" in general. And the
local-vs-API choice here is a real trade-off worth naming: local is **private and free**
but a paid embedding model might retrieve a bit more accurately. For a personal KB, free +
private wins.

## Mini-glossary

- **Vector** — the list of numbers representing one piece of text.
- **Dimension** — how many numbers are in that list (MiniLM uses 384).
- **Similarity** — how "close" two vectors are; usually *cosine similarity* (angle
  between them), not literal distance.
- **Chunk** — one slice of a document that gets embedded as a unit.

## Go deeper

- *Why* chunk at all, and how chunk size changes what gets retrieved.
- **Cosine similarity** intuition — why angle, not raw distance.
- Local vs API embedding models — quality, cost, and privacy trade-offs.
- The individual numbers in a vector don't "mean" anything on their own — only their
  *pattern* does. Worth sitting with that.
