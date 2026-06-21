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

In `notes-api`:

- **Valid-by-construction.** `Note` has two constructors: a no-arg one Java's persistence layer
  needs to rebuild rows from the database, and `Note(title, content)` for my own code — which
  refuses to make a note missing its essentials.
- **Dependency injection.** `NoteService(NoteRepository repository)` takes its data layer
  through the constructor; the field is `final` (set once, never null), and in a unit test I can
  write `new NoteService(fakeRepo)` with no framework at all.

The Python mirror: a constructor is `__init__`. The day `generate.py` (note 13) grows shared
config, I'd give it a `DatasetGenerator.__init__(self, client, model=...)` — the same move,
handing the client in once instead of threading it through every call.

Related: the immutable request object `NoteRequest` (a Java `record`) is a constructor that
also *validates*, and it deliberately has no `id` field, so a client can't set one. That's the
same "the schema is the contract" principle as structured output in note 01.

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
