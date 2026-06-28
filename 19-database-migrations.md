# 19 — Database migrations: versioning your schema

> **TL;DR** Your database *structure* — tables, columns, types — changes over time. A
> **migration** is one numbered, ordered change to that structure, applied exactly once. Keep
> them in source control and any environment can rebuild the same schema from scratch.

## Plain idea

Code isn't the only thing that evolves; the shape of your database does too. You add a `tags`
table, you widen a column, you add an index. The naive way is to log into each database and
hand-type the change — which means dev, CI, and production slowly drift apart and nobody can say
what's actually in each one.

A **migration** fixes that. It's a small SQL script with a version number, like
`V1__create_notes_and_tags.sql`. A tool (here, **Flyway**) runs them in order, records each one
it applied in a `flyway_schema_history` table, and never runs the same one twice. Start the app
a second time and Flyway sees `V1` is already done and does nothing.

The rule that makes it work: **you never edit an applied migration.** The next change is always a
*new* file — `V2__...sql`. The history is append-only, so the schema is the sum of every
migration replayed in order — reproducible anywhere.

This is the same idea as the lockfile in note 11: there we pinned exact library versions so every
machine builds the identical environment; here we pin the schema as ordered scripts so every
database rebuilds identically — from source, not from someone's memory of what they typed last
Tuesday.

## Analogy

Migrations are the **numbered chapters of a book**. To get the current story you read chapters 1,
2, 3 in order — you don't rewrite chapter 1 once it's published, you write chapter 4. Anyone with
the same book reads the same story. Flyway is the bookmark that remembers which chapter you've
reached, so re-opening doesn't re-read what you've already finished.

## In my project

`notes-api` has lived on both sides of this lesson.

**v1 (Flyway).** As a Java/Spring Boot app on **PostgreSQL**, it let **Flyway** own the schema.
One migration, `V1__create_notes_and_tags.sql`, created the `notes` and `note_tags` tables; the
filename encodes the contract (`V` + version + `__` + description). On startup Flyway recorded each
applied script in `flyway_schema_history` and never re-ran one, while Hibernate ran with
`ddl-auto=validate` — creating nothing, only checking the entities still matched the tables Flyway
built, so drift failed the app at boot instead of at 2 a.m.

**v2 (auto-create, on purpose).** The Python/FastAPI port has **no migration tool**. On startup it
calls SQLAlchemy's `Base.metadata.create_all`, which builds any missing tables straight from the
models, against a default **SQLite** file. That's exactly the auto-create approach the rest of this
note warns against for a real database — and it's the right call *here*: a single-user hobby app on
a throwaway SQLite file has no production schema to protect and nothing to drift from. The day it
grows a real Postgres and a second schema change, the Python answer is **Alembic** (below), and
that's the upgrade I'd make.

## Why it matters

Without migrations, your schema is an undocumented thing that exists differently in every
environment, and "set up a fresh database" becomes tribal knowledge. With them, the schema is
reviewable in a pull request, replayable on a clean machine, and identical in CI and production.

It also surfaces a sharp lesson: a query that passed every H2 test blew up on Postgres
(`function lower(bytea) does not exist`) because H2 isn't Postgres. Versioned, real-engine
migrations are what let you catch dialect bugs *before* production instead of discovering them
there.

## Go deeper

- **The append-only rule** — why you add `V2` instead of editing `V1`, and what
  `flyway_schema_history` actually stores.
- **`validate` vs `migrate` vs auto-create** — letting Hibernate build tables is fine for
  H2/tests, dangerous for a real database (no history, no review).
- **Rollbacks / down-migrations** — most teams roll *forward* with a new fix migration rather
  than truly reversing one.
- **Testing against the real engine** (e.g. Testcontainers) so "green on H2" can't hide a
  Postgres-only bug.
- Other migration tools in the same family: Liquibase (Java), Alembic (Python), Rails migrations.
