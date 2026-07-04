# Glossary

Personal reference for terms I keep using across notes and projects.
Plain language, analogies first. Alphabetical order.

---

## agent

An AI that doesn't just answer questions — it takes actions in a loop until a job is done.

**Analogy:** the difference between asking a friend "what restaurant should I go to?" vs. handing
your friend your phone and saying "book us a table." The first friend talks. The second one looks
things up, makes decisions, and does stuff.

In practice: the agent gets a goal, picks a tool to call, sees the result, picks the next tool,
and keeps going until it has an answer or hits a dead end.

**In my projects:** `kb-agent` is the agent — it can search the knowledge base, look up notes,
and synthesize an answer, rather than just generating text from memory.

**Related:** tool use (how the agent reaches out), LLM (the brain inside the agent)

---

## API / REST API

A menu at a restaurant. You don't go into the kitchen — you look at the menu, place an order
in a specific format, and get a response back. REST is the standard format most web services
use for those orders.

Every service in this system communicates via APIs. `notes-api` is literally named for this —
it's the menu for creating, reading, and tagging notes. `kb-agent` orders from `notes-api`
and from the classifier.

**Related:** contract (what the menu promises it will serve)

---

## BackgroundTask

A way to say "do this after I respond" without needing a separate queue or message broker.

**Analogy:** dropping a letter in your own outbox on your way out the door, instead of calling
a courier service to come pick it up. The letter still gets sent — just by a process running
in the same house, right after you leave, instead of by an outside service you have to set up
and maintain.

In practice: the web framework hands the request back to the caller immediately, then runs a
function afterward, in the same process, no separate infrastructure required.

**In my projects:** `notes-api` uses FastAPI's `BackgroundTask` to call the classifier and
write the labels back as tags after a note is created — the caller gets a fast response, and
the classify-and-tag step happens right after. This replaced an earlier Kafka-based design;
for a single-process, personal-scale system, a broker was infrastructure the problem didn't
need. See `system/SYS-005`.

**Related:** idempotency (why the writeback step is safe even if it runs more than once),
contract (the `/classify` and tags-writeback shapes this task calls)

---

## BM25

A scoring system for keyword search — finds documents that contain the words you asked for,
ranked by how relevant those words are.

**Analogy:** a smart librarian who counts keywords. You ask for "procurement contract" and BM25
scores every document: documents that use those words a lot score higher, but *common* words
("the", "is") count for almost nothing. Rare, specific words count for a lot.

No AI required. Fast, reliable, and great when the user's query uses the same words as the
document. Falls apart when the query and document use *different words for the same idea*
(see: vector search).

**In my projects:** BM25 is one retrieval strategy available to `kb-agent` when searching
the knowledge base.

**Related:** vector search (the meaning-based alternative), RAG (the broader pattern)

---

## classification

Automatically sorting items into labeled bins based on what they are.

**Analogy:** sorting your email into folders — except instead of you doing it manually, you've
trained a system to learn the rules and do it for you. Show it enough examples of "this is
procurement" and "this is geopolitics" and it learns to tell them apart.

**In my projects:** the classifier reads a defense news article and assigns two labels: what
*domain* it belongs to (e.g., land, air, maritime) and what *category* it is (e.g.,
procurement, policy, technology). That's what makes the knowledge base queryable later.

**Related:** eval (how you check if the classifier is doing this well)

---

## classifier metrics

The numbers that tell you how well the classifier is sorting items. See also: **eval**.

| Metric | What it measures | Analogy |
|---|---|---|
| **Accuracy** | Share of all predictions that were correct | Overall grade on a test |
| **Precision** | Of everything I labeled X, how many were actually X? | Don't cry wolf |
| **Recall** | Of everything that *was* X, how many did I catch? | Don't miss anything |
| **F1** | Balance of precision and recall, single number | The composite score when one alone misleads |
| **Confusion matrix** | Full breakdown of what got confused with what | The answer key showing every wrong answer |

**Why F1 instead of accuracy?** If 95% of your articles are "procurement" and you just label
everything "procurement," you get 95% accuracy while being useless. F1 catches this.

**In my projects:** current classifier scores — category F1 ≈ 0.906, operational-domain
F1 ≈ 0.894. The ceiling is label ambiguity (industry vs. procurement both involve defense
companies and money), not model power.

---

## context window

The AI's desk space — everything it can "see" at once.

Your question, the conversation so far, any documents you handed it, the system instructions —
all of it has to fit on the desk. Once the desk is full, old stuff falls off the edge.
A bigger context window means a bigger desk, which means longer conversations and more
documents before things start dropping off.

**Why it matters for RAG:** you can't hand the AI your entire knowledge base — it won't fit
on the desk. RAG solves this by retrieving only the *relevant* pages and handing those over
instead.

**Related:** token (how desk space is measured), RAG

---

## contract

An explicit, agreed-on interface between two pieces of a system — what one side promises to
produce and what the other side is allowed to assume.

**Analogy:** a power outlet. The outlet promises a specific voltage and plug shape. Your lamp
doesn't need to know how the power station works — it just plugs in. And the power station
doesn't need to know it's powering a lamp. Both sides can change their internals as long as
the outlet shape stays the same.

**In my projects:** `notes-api` calls the classifier's `/classify` endpoint and writes labels
back as tags. The classifier promises the `/classify` shape (SYS-004); `notes-api` promises
the tags writeback shape (SYS-005). Neither service knows how the other works internally.

**Related:** idempotency (what a contract can safely promise about repeated calls),
API (the technical form a contract takes)

---

## embeddings

Turning words and documents into coordinates on a map, where things that *mean* similar
things end up near each other.

**Analogy:** imagine a map where "army" and "military" are two blocks apart, but "army" and
"soufflé" are on opposite sides of the country. Once everything has a location on this map,
you can search by *proximity* — find me everything near "defense procurement" — instead of
by exact word match.

Embeddings are what make vector search possible. An AI model creates the coordinates;
the search engine finds the nearest neighbors.

**Related:** vector search (uses embeddings to find similar documents), BM25 (the keyword
alternative that doesn't use embeddings)

---

## eval

A test set of examples where you already know the right answer, used to measure whether
your AI is actually doing what you think it is.

**Analogy:** a spell-checker test. You give it 100 misspelled words you know the answer to,
run it, and count how many it got right. You don't just read a few outputs and say "looks
good" — you get a number. The number is what lets you compare before vs. after a change.

**Why it matters:** AI changes are *persuasive*. A reworded prompt can read smarter while
quietly making the model worse. You can't feel a 3-point drop by skimming outputs. The
number catches what your eyes flatter.

**See note:** [02 — Eval-driven development](02-eval-driven-development.md)

**Related:** eval-as-a-harness (running the eval automatically), classifier metrics (what
the eval measures for the classifier)

---

## eval-as-a-harness

Promoting an eval from a one-off script into a repeatable test that runs automatically —
the same way a unit test guards against regressions in regular code.

**Analogy:** instead of manually weighing yourself every few weeks when you remember, you
set a scale on the floor that syncs to your phone and logs every morning. The check becomes
systematic rather than optional.

The upgrade path: eval CSV → scoring script → wired into CI → a PR that drops accuracy
gets caught before it merges.

**In my projects:** wiring the classifier eval into GitHub Actions is the next milestone
(evals-as-CI, SYS-007).

**Related:** eval, contract (what the harness enforces)

---

## idempotency

Running an operation once vs. five times produces the exact same result. Safe to retry;
duplicates don't accumulate.

**Analogy:** setting a light switch to ON. Flipping it to ON when it's already ON does
nothing extra. Compare with a "add one to counter" button — pressing it five times gives
you five, not one.

**Why it matters:** networks fail, retries happen, message queues sometimes deliver the
same message twice. If your handler isn't idempotent, a harmless retry becomes a bug.

**In my projects:** `PUT /notes/{id}/tags` *replaces* the classifier's labels, not appends
them. Reprocessing the same note five times lands identically to processing it once — 200,
no duplicates.

**Related:** contract (what the API promises), Kafka (at-least-once delivery makes this
necessary)

---

## Kafka

A message queue — a conveyor belt with a long memory.

**Analogy:** instead of handing a package directly to someone (who might not be there),
you drop it on a conveyor belt. The belt holds it. The recipient picks it up whenever
they're ready. If the recipient is busy or offline, the package waits — it doesn't get
lost.

This decouples services: Service A doesn't need to know if Service B is running. It just
drops a message and moves on. Kafka also keeps a log of every message, so a service can
"rewind" and reprocess old messages.

**In my projects:** Kafka was in the original `notes-api` design. It was cut in favor of
simpler in-process background tasks — the right call at this scale, though the
architecture note (SYS-005) captures why Kafka would matter at larger scale.

**Related:** idempotency (Kafka's at-least-once delivery is why this matters),
contract (the message schema is a contract)

---

## LLM (Large Language Model)

The AI model at the center of everything — the thing that reads your prompt and generates
a response.

**Analogy:** a very well-read assistant who has absorbed almost everything on the internet,
can write, reason, and explain — but has no memory of you specifically once the conversation
is over. Every new conversation, you're starting fresh with a stranger who happens to know
everything.

"Large" refers to how it was trained — on enormous amounts of text, with billions of
parameters (internal knobs). The size is what gives it broad capability.

**In my projects:** Claude (Anthropic's model) is the LLM. The classifier uses it to label
articles; `kb-agent` uses it to reason over retrieved notes and synthesize answers.

**Related:** prompt (what you give the LLM), context window (how much it can see at once),
agent (an LLM with tools and a loop)

---

## prompt

The instruction sheet you hand an AI before it does anything.

**Analogy:** a job description handed to a new contractor on day one. A vague job
description gets vague work. A specific one — with examples, constraints, and the format
you want back — gets what you actually needed.

"Prompt engineering" is mostly the discipline of writing better job descriptions: what
role is the AI playing, what are the rules, what format should the output be in, what
are examples of good vs. bad responses.

**In my projects:** the classifier prompt defines the label taxonomy, gives examples of
each category, and specifies the output format. The eval exists specifically to catch when
a reworded prompt sounds better but actually scores lower.

**Related:** LLM, eval (how you check if the prompt is working)

---

## RAG (Retrieval-Augmented Generation)

Open-book exam instead of closed-book. Before answering, look up the relevant pages, hand
them to the AI, and let it answer based on what it just read — not just what it memorized.

**Analogy:** you're asked a question about a contract you signed last year. Closed-book: you
try to remember the terms. Open-book (RAG): you pull the contract out of the drawer, read
the relevant clause, and answer from the actual document. More accurate, and you can cite
the source.

The "retrieval" step is what makes this work — you can't hand the AI your entire knowledge
base (it won't fit). So you search for the relevant pages first, then hand only those over.

**In my projects:** `kb-agent` uses RAG to answer questions over the defense-news knowledge
base. It retrieves relevant notes (via BM25 or vector search), hands them to the LLM as
context, and the LLM answers based on what it read.

**Related:** BM25 and vector search (retrieval strategies), context window (why you
can't hand over everything), embeddings (how vector search finds relevant docs)

---

## token

The unit an LLM reads and writes in. Not quite words, not quite characters — closer to
word-chunks or syllables.

**Analogy:** Scrabble tiles. "classification" might be 3 tiles; "cat" is 1. The AI
processes one tile at a time. Pricing, speed, and context limits are all measured in tiles,
not words.

Rule of thumb: 1 token ≈ 0.75 words in English. A page of text ≈ 500–700 tokens.

**Related:** context window (measured in tokens), LLM

---

## vector search

Search by meaning rather than keyword match.

**Analogy:** you ask "who's acquiring fighter jets?" and it finds documents about defense
procurement acquisitions — even if neither "fighter jets" nor "acquiring" appears in the
text — because the *meaning* is similar. Compare with BM25, which would miss those documents
entirely if the words don't overlap.

Under the hood: both the query and every document are turned into embeddings (coordinates
on a meaning-map). Vector search finds the documents whose coordinates are nearest to the
query's coordinates.

**Related:** embeddings (the coordinates), BM25 (the keyword alternative), RAG
(vector search is one way to do the retrieval step)
