# 16 — Containers & Docker: ship it the same everywhere

> **TL;DR** "Works on my machine" usually means the *machine* is different, not the code. A
> **container** packs the OS, the runtime, the libraries, and your app into one sealed bundle
> that runs the same on your laptop, a teammate's, or the cloud. **Docker** is the tool that
> builds and runs those bundles.

## Plain idea

A container takes everything your app needs to run — a stripped-down Linux, Python 3.11, your
pinned dependencies, and your source files — and seals it into one image. You build the image
once and run it anywhere; the host barely matters because the container carries its own world
with it.

Two files do the work:

- **`Dockerfile`** — the recipe. Start from a base (`python:3.11-slim`), install the deps,
  copy in the code, say how to launch it. Human-edited.
- **`.dockerignore`** — the "don't pack this" list. Keeps junk and secrets out of the bundle
  so the image stays small and safe.

This is the cross-language cousin of the lockfile idea in note 11: a lockfile pins your Python
*dependencies*; a container pins the **whole stack underneath them too** — the OS, the Python
version, the system libraries. The lockfile makes the deps reproducible; the container makes
the entire environment reproducible.

## Analogy

A lockfile is "this exact bag of flour." A container is the **whole sealed test kitchen,
shipped on a pallet** — same oven, same brand of flour, same thermometer, already wired up.
You don't reassemble the kitchen at the destination; you plug in the pallet and it runs.

(The project notes call this a "lunchbox" — chef, kitchen, ingredients, and recipe sealed in
one box. Same idea: the container carries its environment with it.)

## In my project

The classifier has a real `Dockerfile` that packs the serving API:

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements-api.txt .
RUN pip install --no-cache-dir -r requirements-api.txt
COPY src/api.py src/classify.py ./src/
```

A few deliberate choices in it:

- **Lean on purpose.** It installs only `requirements-api.txt` and copies only `api.py` +
  `classify.py`. The generator, the eval scripts, the data, and heavy `pandas` are left out —
  the drive-thru window doesn't need the grading kit.
- **Layer caching.** Deps are copied and installed *before* the source, so changing a line of
  code doesn't re-run the slow `pip install`.
- **Runs as non-root** (`useradd ... appuser`) — if the process is compromised it isn't root
  inside the container.
- **`$PORT` at runtime** — the host injects the port; the image doesn't hardcode it.

The `.dockerignore` is the secrets guard: it lists `.env` and `.env.*` so no API key ever gets
baked into the image — exactly the rule from note 10 (secrets live in the environment, never
in the artifact). It also drops `.git/`, `data/`, and `README.md` to keep the build context
small.

Earlier, my other repo used Docker the other way too — a `docker-compose.yml` spun up a local
**Kafka** broker plus a web UI in one `docker compose up`, back when the system was event-driven
(note 18). That stack is retired now that enrichment runs in-process, but the distinction it
taught still holds: one container to *ship* an app, several wired together to *run a dev stack*.

## Why it matters

It kills the "works on my machine" ghost for good. The image that passes on my laptop is the
*same bytes* that run in the cloud — not a similar setup, the identical one. It also makes the
runtime disposable and honest: a fresh container every time means no leftover state quietly
keeping things alive, and the `.dockerignore` line means a leaked image can't leak a key.

## Go deeper

- **Layers and caching** — why ordering `COPY`/`RUN` well makes rebuilds fast, and how a layer
  is reused until something above it changes.
- **Multi-stage builds** — build in a fat image, copy only the artifact into a slim one. (My
  Dockerfile skips this on purpose: pure-Python wheels, nothing to compile.)
- **Image vs container** — the image is the frozen recipe; the container is one running copy.
- **`docker compose`** — declaring several containers and their wiring in one file (like the
  retired Kafka dev stack), vs a single shipped service.
- **Where images live** — registries, tags, and how CI builds and pushes them.
