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

## In my project

`notes-api` is where I felt this firsthand. `NoteService.create()` used to just save a note and
return. Now it saves the note and then **publishes a `NoteCreated` event**:

```java
Note saved = repository.save(note);
NoteCreated event = new NoteCreated(saved.getId(), saved.getTitle(),
        saved.getContent(), saved.getTags(), saved.getCreatedAt());
kafkaTemplate.send("note-events", saved.getId().toString(), event);
return saved;
```

That one `send` changed what kind of system it is. The `POST /notes` returns the instant the row
is saved — it doesn't wait on anything downstream. The event lands on the `note-events` **topic**,
**keyed by the note id** so every event about the same note stays in order on the same partition.
A future classifier consumer could subscribe and tag the note on its own time; `notes-api` never
has to know it exists.

The honest catch is written right into the code's comments: the DB save and the Kafka send
**aren't atomic**, so a crash between them could drop an event. That dual-write risk is accepted
for now, with the *transactional outbox* noted as the real fix.

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
