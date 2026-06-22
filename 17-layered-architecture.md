# 17 — Layered architecture: controller, service, repository

> **TL;DR** Split a backend into three stacked layers — a controller that speaks HTTP, a
> service that holds the rules, and a repository that talks to the database. Each layer knows
> only the one beneath it, so a request flows straight down and the answer travels straight
> back up.

## Plain idea

A request could be handled by one big function that reads the HTTP, runs the logic, and hits
the database all at once. Layered architecture says: don't. Give each job its own layer.

- **Controller** — translates HTTP ↔ method calls. Paths, verbs, status codes. Nothing else.
- **Service** — the business rules. "What does an update mean?" "404 if it's missing?"
- **Repository** — reads and writes the database, and nothing above it.

The dependencies only point **downward**: the controller knows the service, the service knows
the repository, the repository knows the database. Nothing points back up — the database layer
has no idea the web even exists. Each layer is a class with one responsibility (note 13), and
each is handed the layer below it through its constructor (note 14).

## Analogy

A restaurant. The **waiter** (controller) takes your order and brings your food — they talk to
*you*, not the stove. The **kitchen** (service) decides how the dish is actually made. The
**pantry** (repository) just stores and fetches ingredients. The waiter never cooks, the pantry
never greets customers, and you never wander into the kitchen yourself. Everyone has one job,
and the order flows one direction: front of house → kitchen → pantry, then the plate comes back.

## In my project

In `notes-api`, follow one `POST /notes` with body `{"title":"Buy milk","content":"2% and oat"}`:

1. **Controller** (`NoteController.create`) gets the HTTP request, builds a `Note` from the
   request, hands it to the service, wraps the result in a response. Two lines.
2. **Service** (`NoteService.create`) applies the rules — for create it's just "save it," but
   `update` is a read-modify-write in a transaction and `findById` throws a 404 if missing.
3. **Repository** (`NoteRepository.save`) does the actual database write — a method I never
   wrote, because Spring Data generated it.
4. The result travels back up: entity → `NoteResponse` → JSON → HTTP 201.

The key discipline is that the **entity never leaks out**. The controller speaks **DTOs**, not
the `Note` entity — `NoteRequest` coming in, `NoteResponse` going out. `NoteRequest` has no `id`
or timestamp fields, so a client can't set server-owned data (the *mass assignment* bug). The
DTO is the wall between the outside world and my storage shape: entities talk to the database,
DTOs talk to the world.

## Why it matters

- **Test a layer alone.** Hand `NoteService` a fake repository and test the rules with no web
  server and no database (`new NoteService(fakeRepo)` — note 14).
- **Swap a layer.** Move from H2 to PostgreSQL and only the repository cares. Add a CLI and only
  a new top layer changes; the rules stay put.
- **Reason locally.** A wrong status code is a controller bug. A wrong "valid update" is a
  service bug. The layout tells you where to look before you even open the file.

## Go deeper

- Where does a cross-cutting concern (auth, logging, caching) live when it touches every layer?
- The mapping cost — every boundary needs a DTO↔entity conversion. When is that worth it, and
  when is it ceremony?
- "Skinny controller, fat service" — and the failure mode where logic leaks up into the
  controller or down into the entity.
- How transactions span the service ↔ repository boundary, and why the service usually owns them.
