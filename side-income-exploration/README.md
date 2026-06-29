# Side-Income Exploration — Session Archive

> A distilled archive of a brainstorming + deep-research session on building
> **passive / semi-passive side income**. Saved so the thinking survives the
> session being archived. Pick up here.
>
> **Date:** 2026-06-29 · **Status:** exploration ongoing — no idea committed yet.

---

## The brief (what I'm actually optimizing for)

- **Goal:** something I build **once** that keeps earning **while I'm at my day job** —
  i.e. low ongoing time, not a second job.
- **Time budget:** a few hours/week.
- **Horizon:** balance — some near-term wins, real long-term upside.
- **Risk:** fun matters; willing to lose money I'm comfortable losing.

## The profile (what makes my angle unusual)

- Software engineer with a **network operations (netops)** background **+ an MBA**.
- **Claude Code Max** subscriber — can orchestrate AI agents to ship software fast.
- Practical **AI/ML integration** skills (competent integrator, not a research-level ML expert).
- **I work at a large bank.** ← this is both my biggest moat *and* my biggest constraint
  (see `03-compliance-landmines.md` — it killed two ideas).

## The one-line conclusion (so far)

> Shipping software fast is **no longer a moat** — by 2026 everyone can. The durable
> edge is the stuff AI can't supply: **domain depth, trust/access, and a real
> distribution channel.** The idea that survived *every* filter is the lowest-tech one:
> **teach the LLM-evaluation methodology** I already practice (see `04-ideas-and-next-steps.md`).

---

## The decision funnel (what we considered, and what happened to each)

| Idea | Verdict | Why |
|---|---|---|
| Generic "ship fast with AI" micro-SaaS | ⚠️ weak | Build-speed isn't a moat; ~90% of AI startups projected dead by end-2026 |
| **"NetOps for AI agents"** platform (egress/policy/observability) | ❌ killed | Consolidating into Cisco (Astrix ~$400M), Palo Alto (Portkey/Prisma AIRS); proxy primitive is free & commoditized (LiteLLM, MIT) |
| AI **cost-governance / FinOps-for-agents** | 🟡 live | Strongest demand signal (98% of FinOps teams now manage AI spend) but commoditizing fast from below |
| **Vertical eval + governance** (regulated niche) | 🟢 strong | The ~37pt gap between observability (89%) and eval (52%) adoption; defensible via domain depth |
| Sell eval/validation **SaaS to banks** | ❌ killed | Procurement wall + **employment conflict** (I work at a bank) |
| **Personal trading bot** ("let it ride") | ❌ killed | **Personal Account Dealing (PAD)** policy — automated personal trading is gated/prohibited for bank employees |
| **Teach the methodology** (course / writing / open eval framework) | 🟢 **leading** | Survived every gate: no build-moat issue, no sell-to-banks conflict, no PAD issue, hardest to commoditize, most passive |

Full reasoning in the companion files:

- **`01-market-research-findings.md`** — verified findings from two deep-research runs (with sources)
- **`02-vertical-ranking-and-window.md`** — finance vs healthcare vs gov ranking + the commoditization survival window
- **`03-compliance-landmines.md`** — the PAD + sell-to-banks conflicts (learned the hard way)
- **`04-ideas-and-next-steps.md`** — live / parked / killed ideas + concrete next step

---

## How this research was done (and how much to trust it)

Findings came from a **fetch-free deep-research harness** (multi-agent: fan-out web
searches → extract falsifiable claims → **3-vote adversarial verification** → synthesize).
`WebFetch` was blocked by the environment's egress policy, so claims were extracted from
search snippets and corroborated with additional searches rather than full page reads.

**Confidence caveats baked in:**
- Evidence is **search-snippet-level**, not full-page-verified.
- Many demand stats come from **self-interested vendor/consultancy surveys** (LangChain
  sells eval tooling, Gravitee sells governance, etc.) — directional, not neutral.
- The market is **moving monthly** (M&A, regulation, native platform features) — this has
  a short shelf life. Re-check before betting.
- Claims that **failed** verification are listed in the findings file for transparency.
