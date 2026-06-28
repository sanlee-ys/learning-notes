# 18 — Event-driven architecture: working through a message queue

> **TL;DR** Instead of one component calling another directly and waiting for a reply, it
> **publishes an event to a queue and moves on**. Whoever cares subscribes and reacts on their
> own time. The two sides stop depending on each other being up.

## Plain idea

In the usual request-and-wait flow (note 17), component A calls component B and blocks until B
answers. A has to know B exists, know how to reach it, and B has to be up — or A's request
fails. They're chained together.

**Event-driven architecture** breaks that chain. A does its own job, then **announces a fact**
("a note was created") by dropping a message onto a queue. It returns immediately. It doesn't
know or care who's listening. Later — on their own schedule — any interested consumers pick the
message up and react.

Three words carry most of it:

- **Producer** — the side that publishes the event (A).
- **Consumer** — the side that subscribes and reacts (B, and any others).
- **Topic** — the named stream the event goes onto. The queue in the middle (here, Kafka) holds
  events in a durable log, so a slow or absent consumer doesn't lose anything; the message waits
  until it's read.

A topic is split into **partitions** (parallel lanes) living on **brokers** (the queue's
servers). That's just how the queue scales and stays safe — more lanes serve more consumers at
once, more brokers mean copies survive a machine dying. You can publish without thinking about
either.

## Analogy

**A phone call vs. a mailbox.** The synchronous way is phoning someone: you both have to be on
the line at the same time, and you wait while they think. The event-driven way is dropping a
letter in a mailbox and walking off. You're done the moment it's posted. Whoever's interested
checks the box later and acts — and you never had to know who they were.

## In my project — I built this, then deliberately took it out

`notes-api` is where I felt this firsthand, and where I later learned the other half of the
lesson: *when not to use it.*

**v1 (Kafka).** `NoteService.create()` saved a note and then **published a `NoteCreated` event**
to a `note-events` **topic**, keyed by the note id so every event about the same note stayed in
order on one partition. `POST /notes` returned the instant the row was saved, never waiting on
anything downstream. A separate classifier **consumer** subscribed and tagged the note on its own
time; `notes-api` never had to know it existed. That one publish is what made it event-driven.
The honest catch was that the DB save and the event send **weren't atomic**, so a crash between
them could drop an event — a dual-write risk I'd accepted, with the *transactional outbox* noted
as the real fix.

**v2 (no broker).** I then ported `notes-api` from Java/Spring Boot to Python/FastAPI and, in the
process, **deliberately collapsed the queue away**. Enrichment now runs in-process: creating a
note schedules a FastAPI `BackgroundTask` that calls the classifier's HTTP `/classify` and writes
the labels back as tags. `POST /notes` still returns immediately, so I kept the *responsiveness*
win, but I gave up the *decoupling* and *resilience* the durable log was buying.

**Why I made that trade.** For a single-writer hobby system with one consumer, Kafka was paying
rent I wasn't using. There were no other subscribers to decouple from, no replay to backfill, no
throughput that needed partitions — just a broker, a topic, and a dual-write hazard to babysit.
The in-process task removes the broker, the dual-write window, and a whole class of operational
surface, in exchange for losing what I was never actually using. If a second consumer or a real
replay need ever shows up, the queue earns its place back. The old Kafka consumer is preserved,
marked inactive, in the classifier repo as a reference implementation, and the idempotent
prefixed-tag writeback it pioneered now lives in `notes-api`'s `tasks.py`.

The rest of this note describes the pattern itself, which is worth knowing cold even when the
right call is to *not* reach for it.

## Why it matters

This is the asynchronous, decoupled alternative to the synchronous layered flow in note 17. It
buys three things: **decoupling** (add a new consumer without touching the producer),
**resilience** (a consumer being down doesn't break the producer — the event waits in the log),
and **responsiveness** (slow work moves off the request path).

The cost is honesty about **eventual consistency**: the note exists now, its tags show up a
moment later. The flow also hops across services and time, which is harder to follow — the price
you pay for not chaining everything together.

## Go deeper

- **Idempotent consumers** — the queue may deliver the same event twice (at-least-once), so a
  consumer must handle a repeat without double-acting.
- **The transactional outbox** — the production fix for the dual-write problem above.
- **Eventual consistency** — when "correct in a moment" is fine and when it isn't.
- **Replay** — because the log keeps events by offset and doesn't delete on read, a brand-new
  consumer can read history from the start and backfill.
- Tracing an event across services (distributed tracing) when there's no single top-to-bottom
  call to read.
