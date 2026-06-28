# 26 — Integration tests with Testcontainers: a real dependency, briefly

> **TL;DR** A unit test fakes everything around your code; an **integration test** runs it
> against a *real* dependency (a broker, a database) so it catches what a mock can't — wire
> formats, serialization, connection config. **Testcontainers** makes that cheap: it starts the
> real dependency in a throwaway Docker container for the test and tears it down after.

## Plain idea

Most tests should be **unit tests** (note 20): fast, no network, every external thing faked. They
prove your code is right *given the inputs you imagined*. Their blind spot is the seam to the
outside world — a unit test that mocks Kafka can't prove the message another service *actually*
publishes deserializes the way you assumed.

An **integration test** fills that gap by adding exactly one real dependency back in. The cost is
that you now need that dependency running. The old ways were bad: a shared dev broker (someone
else mutates it; tests flake), or "install Kafka on the CI box" (slow, brittle, drifts from prod).

**Testcontainers** is the modern answer: in the test itself you ask for a real Kafka/Postgres/Redis,
it starts that as a **Docker container** scoped to the test, hands you its address, and removes it
when the test ends. Real dependency, no shared state, cleaned up automatically. It exists for both
Python (`testcontainers[kafka]`) and the JVM (`org.testcontainers`), with the *same* idea on both.

## Analogy

A unit test is a **flight simulator** — cheap, safe, infinitely repeatable, but the weather is
fake. An integration test is a **short test flight in a rented plane**: you give it back when you
land (Testcontainers returns the container), but for those few minutes the air is real. You don't
test-fly every change — you simulate most of them — but before you trust the seam, you want real
air under the wings once.

## In my project — what these tested, and why they're now historical

**v1 (the Kafka seam).** The system used to run an event loop: `notes-api` published a
`NoteCreated` event → Kafka topic `note-events` → the classifier's consumer tagged the note
(note 18). Both sides were unit-tested with the broker **faked**, so nothing proved a real round
trip. I added a Testcontainers integration test on **each** side:

- **Consumer side (Python)** — `defense-news-classifier/tests/test_consumer_integration.py`: started
  a real broker, published a `NoteCreated` the way notes-api did, and drove the consumer's real
  consume → deserialize → process path.
- **Producer side (Java)** — `notes-api/.../NoteEventPublishingIT.java`: booted the app against a
  real broker and asserted that creating a note landed a real `NoteCreated` on the topic, with the
  frozen wire shape (key = note id, plain JSON, no Java type headers).

I'd written integration tests with Testcontainers back in my Python days, so the *concept* wasn't
new — the refresher here was getting them running in **Java**, where the machinery differs. Same
idea, different tooling; the Rosetta below is the map from what I'd done in Python to the Java side:

| Idea | Python (pytest) | Java (JUnit 5 / Spring Boot) |
|---|---|---|
| Start/stop the container | a fixture that starts it and `yield`s, stopping after | `@Testcontainers` + `@Container` on a `static` field (JUnit owns the lifecycle) |
| Skip when Docker is absent | `pytest.skip(...)` in the fixture | `@Testcontainers(disabledWithoutDocker = true)` |
| Point your client at it | read `container.get_bootstrap_server()` and pass it in | `@ServiceConnection` auto-wires it into `spring.kafka.*` (or `@DynamicPropertySource` to do it by hand) |
| Keep it out of the fast lane | mark `integration`, deselect by default, run with `--run-integration` | name it `*IT` so **Failsafe** runs it in `verify`, while **Surefire** runs `*Test` units in `test` |
| Read the topic to verify | kafka-python `KafkaConsumer` | `org.apache.kafka...KafkaConsumer` (same client, Java API) |

The naming split is the one genuinely Java-specific thing: `./mvnw test` runs only the fast unit
tests (`*Test`), and `./mvnw verify` additionally runs the integration tests (`*IT`) — so the
opt-in is by *filename convention + build phase*, where Python does it with a marker + a CLI flag.

**v2 (no broker).** The Java→Python port collapsed that event loop into an in-process
`BackgroundTask` (note 18), so the Kafka seam these tests guarded no longer exists: the producer IT
is gone with the Java code, and the consumer IT is preserved but inactive. The technique didn't go
anywhere, though — it just points at v2's real seams now. The integration test I'd write next uses
a **Postgres** Testcontainer to catch the SQLite-vs-Postgres dialect bugs note 19 warns about, and
an **HTTP stub** of the classifier's `/classify` to prove the writeback `BackgroundTask` end to end.

## Why it matters

- It catches the failures unit tests **structurally cannot**: a renamed field, a serializer that
  writes dates as numbers, a `bootstrap-servers` typo, a type-header setting the other language
  can't read. These only show up when a real broker is in the loop.
- Testcontainers makes the realistic test **disposable and parallel-safe**, so "use realistic tests
  sparingly" (the test pyramid, note 20) stops meaning "use flaky shared infra."
- Keep it opt-in. Integration tests are slow (they pull an image, boot a broker) and need Docker
  (note 16), so they belong in a separate lane — never gating the fast unit feedback loop.

## Go deeper

- **`@ServiceConnection` vs `@DynamicPropertySource`** — the magic auto-wiring versus the explicit
  "set this property to the container's address," and when the explicit one is clearer.
- **Surefire vs Failsafe** — why the JVM splits unit (`*Test`) and integration (`*IT`) tests across
  two build phases, and how `verify` differs from `test`.
- **Ryuk**, the sidecar container Testcontainers starts to reap leftover containers even if the test
  process is killed — why cleanup is automatic.
- Pinning the container **image version** for reproducibility (note 11), and the trade vs. always
  pulling the latest.
- The v2 integration tests still worth building: a **Postgres** Testcontainer for the data layer
  (so "green on SQLite" can't hide a Postgres dialect bug, note 19) and an **HTTP stub** of
  `/classify` driving the writeback `BackgroundTask` end to end — the focused single-seam tests that
  survive the move off Kafka.
- How this connects to **event-driven architecture** (note 18): the contract between producer and
  consumer is exactly what an integration test on each side protects.
