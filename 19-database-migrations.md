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

The `notes-api` moved from **H2** (an in-memory database wiped on every restart) to **PostgreSQL**
for durable storage, with Flyway owning the schema.

The one migration, `src/main/resources/db/migration/V1__create_notes_and_tags.sql`, creates the
`notes` and `note_tags` tables. The filename encodes the contract: `V` + version + `__` +
description.

On startup Flyway creates `flyway_schema_history` if missing, finds migrations newer than what's
recorded, runs them, and logs each. Hibernate is set to:

```properties
spring.jpa.hibernate.ddl-auto=validate
```

So Hibernate *creates nothing* — Flyway owns the schema, and Hibernate only checks the Java
entities still line up with the tables Flyway built. If they drift, the app refuses to start at
boot instead of failing at 2 a.m.

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
