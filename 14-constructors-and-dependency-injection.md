# 14 — Constructors & dependency injection

> **TL;DR** A constructor is the setup ritual that runs when you create an object; its job is
> to leave the object valid and ready, so nobody can get a half-built one. Passing an object's
> dependencies *into* its constructor (dependency injection) makes those dependencies explicit,
> final, and easy to fake in tests.

## Plain idea

When you create an object, a special function runs first: the **constructor** (`__init__` in
Python, `Note(...)` in Java). Its one job is to leave the new object in a valid, usable
state — it's the gatekeeper of "what valid means." If a `Note` can't exist without a title,
the constructor demands a title, and there's simply no way to build a blank one.

A second, bigger use: **dependency injection.** Instead of an object reaching out and creating
the things it needs, you hand them in through the constructor. The object just declares "I need
a repository" and someone supplies one — turning a hidden dependency into a stated one.

## Analogy

A constructor is *new-hire onboarding* before someone's allowed to start: badge issued, laptop
assigned, paperwork signed. You don't let a half-onboarded employee answer support tickets.
Dependency injection is the company *handing* them the laptop on day one, rather than the
employee buying a random one off the street — you control, and can swap, what they're given.

## In my project

In `notes-api`, **valid-by-construction** lives in the request schema. `NoteRequest` is a
**Pydantic model**, and its fields *are* the definition of valid — a note with no title simply
can't be built:

```python
class NoteRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1, max_length=10000)
    tags: list[str] = Field(default_factory=list)
```

A request missing its title never makes it past construction — FastAPI rejects it with a 422
before any of my code runs. It deliberately has no `id` field, so a client can't set server-owned
data — the same "the schema is the contract" principle as structured output in note 01.

**Dependency injection** shows up in `NoteService`: it takes its database session through the
constructor and stores it, so the service can't exist without one — and a unit test can hand it a
throwaway session with no web server in sight:

```python
class NoteService:
    def __init__(self, db: Session) -> None:  # the dependency is handed IN
        self.db = db

# In a test — no FastAPI, just a session against a temp database:
service = NoteService(test_session)
```

For real requests FastAPI supplies that session via `Depends(get_db)`, which opens one per
request and closes it after — the framework doing the injection instead of me wiring it by hand.

The same shape recurs in the classifier: the day `generate.py` (note 13) grows shared config, I'd
hand the client in once through `__init__` rather than threading it through every call:

```python
class DatasetGenerator:
    def __init__(self, client, model="claude-..."):  # __init__ = the constructor
        self.client = client      # dependency injected here, reused by every method
        self.model = model
```

## Why it matters

- **No half-built objects.** Whole classes of "I forgot to set field X" bugs vanish — the
  constructor won't let you.
- **Testability.** Injected dependencies can be swapped for fakes, so I can test the rules
  without a real database or network.
- **Honesty.** A constructor's parameter list is a public statement of what the object truly
  needs in order to exist.

## Go deeper

- Constructor injection vs field/setter injection — why is constructor injection usually
  preferred?
- What's an immutable object, and why are `record` / frozen-`dataclass` types worth reaching
  for?
- When a constructor needs many parameters, what patterns (builder, factory) keep it sane?
