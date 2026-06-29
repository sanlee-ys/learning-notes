# Market Research Findings (verified)

Two deep-research runs, each with 3-vote adversarial verification. Below are the
claims that **survived** verification, plus the ones that were **killed** (for honesty).

---

## Run 1 — Where the whitespace is (broad scan)

**18 of 24 claims confirmed.** Headline: the obvious "netops for AI agents" platform
play is *not* whitespace; the real opening is one layer up.

### ✅ Confirmed
- **The "netops for AI agents" platform layer is NOT solo whitespace — it's consolidating.**
  Palo Alto Networks acquired **Portkey** → shipped **Prisma AIRS "AI Gateway"** (real-time
  authn/authz for every agent interaction, ~$700M-class, closed May 2026). **Cisco** is
  acquiring **Astrix Security** (~$300–400M). The non-human-identity category already has
  5+ funded players (Oasis $120M, Entro ~$200M acquisition, GitGuardian $50M, Clutch).
  - Sources: paloaltonetworks.com/blog/2026/04/securing-and-governing-ai-agents-at-scale-through-a-unified-ai-gateway/ · siliconangle.com/2026/05/04/cisco-buys-astrix-security-strengthen-ai-agent-discovery-governance/ · cremit.io/reports/rsac-2026-nhi
- **The AI-gateway / egress-proxy / per-key-budget primitive is free & commoditized.**
  **LiteLLM** (MIT) already does per-team/key budgets, spend tracking, rate limits,
  guardrails, self-hosted. Rebuilding the plumbing has no moat.
  - Source: github.com/BerriAI/litellm
- **AI cost-governance / FinOps-for-agents is the strongest validated demand signal.**
  State of FinOps 2026 (n=1,192, $83B+ spend): **98% now manage AI spend** (up from 63%→31%
  the prior two years); AI cost management is the **#1 most-desired skill**. Agent tasks burn
  **5–30×+ the tokens** of a chatbot.
  - Sources: finops.org/wg/finops-for-ai-tools-services-considerations/ · oplexa.com/ai-inference-cost-crisis-2026/
- **Eval is genuine whitespace vs observability — a ~37-point adoption gap.**
  LangChain State of Agent Engineering 2025 (n=1,340): **~89% adopted observability, only
  ~52% adopted evals.** "Tracing without evaluation is expensive logging." Defensible angle =
  eval **content + vertical compliance**, not another trace viewer.
  - Sources: langchain.com/state-of-agent-engineering · braintrust.dev/articles/best-ai-governance-platforms-llm-applications-2026

### ❌ Killed (do not repeat these)
- "EU AI Act high-risk enforcement took effect Aug 2026 w/ €35M fines" — **refuted 0-3.**
- "Enterprise AI budgets grew $1.2M → $7M (5–6×)" — **refuted 0-3.**
- "40–60% of enterprise RAG fails to reach production" — **refuted 0-3.**
- "AI governance market → $15.8B by 2030" — refuted; real Gartner figure ~$492M → ~$1B.
  (AI-gateway TAM still small: ~$50–100M in 2025.)

### Sober base rate (verified context)
- Median micro-SaaS ≈ **$500/mo MRR**; ~30% never hit $1K (abandon), ~50% plateau $1K–10K,
  ~15% scale $10K–100K, ~5% >$100K. Breaking **$1K MRR takes a median 12–18 months.**
- Niche APIs: **$500–5K/mo**; vertical tools charge **~3×** a generic equivalent; AI-*native*
  (not wrappers) grew ~2× faster. SMB churn **~8.2%/mo** vs enterprise **~1%/mo** → aim upmarket.
  - Sources: saasranger.com/blog/micro-saas-revenue-reality-what-1000-founders-actually-earn/ · flowjam.com/blog/27-micro-saas-examples-that-actually-print-money-in-2025 · idlen.io/blog/api-economy-developers-make-money-apis-2026/

---

## Run 2 — Vertical selection (finance vs healthcare vs gov)

**23 of 26 claims confirmed.** See `02-vertical-ranking-and-window.md` for the ranking.
Key verified facts:

### ✅ Confirmed — Finance / model-risk
- **No bright-line mandate.** **SR 26-2** (April 17, 2026; Fed/OCC/FDIC) explicitly places
  **generative AI and agentic AI OUT of scope** ("novel and rapidly evolving"). Demand is
  **governance-driven, not mandate-driven.** A forthcoming RFI is signaled.
  - Sources: occ.gov/news-issuances/bulletins/2026/bulletin-2026-13.html · federalreserve.gov/supervisionreg/srletters/SR2602.htm
- **"Examined but unmandated" gap.** Supervisors / internal audit already apply model-risk
  expectations **by analogy** to LLM underwriting assistants, AML triage agents, copilots —
  banks must invent their own control standard. That's where eval/validation evidence sells.
- **Accountability is non-delegable.** Under SR 11-7 / SR 26-2 accountability does **not**
  transfer to the vendor; "we bought it" is not an exam defense. → eval evidence is a
  **recurring** purchase, not a one-time tool.
- **Procurement wall for a solo.** Banks raise diligence on small/no-name single-operator
  vendors; **SOC 2 is necessary-but-not-sufficient** (doesn't validate model accuracy/bias);
  deals stall in security review. → the wedge is **selling validation evidence/methodology**
  the bank's own MRM team runs, NOT a security-reviewed SaaS.
  - Source: deloitte.com/.../ai-in-banking-risk-management.html

### ✅ Confirmed — Healthcare / HIPAA
- Strong, **compressing** buy cycles (health systems 8.0 → 6.6 months; outpatient 4.7), but
  procurement is won on **BAA posture, FHIR/EHR integration (6–12 mo to Epic App Orchard),
  clinical validation, audit trails, and references from similar orgs** — a moat a
  few-hours/week solo with no clinical relationships **cannot build.**
  - Source: menlovc.com/perspective/2025-the-state-of-ai-in-healthcare/

### ✅ Confirmed — Government / FedRAMP
- Gated by a single hard credential being captured by incumbents (IBM watsonx). **FedRAMP 20x**
  lowers the gate (removes agency sponsor, ~2 months, ~$100K–$300K) but still demands six
  figures + full-time effort + an agency Authorizing Official — incompatible with a
  few-hours/week uncertified solo.
  - Sources: gsa.gov/.../gsa-fedramp-prioritize-20x-authorizations-for-ai-08252025 · elevateconsult.com/insights/fedramp-ato-for-ai-platforms-hidden-requirements-you-must-meet/ · paramify.com/blog/fedramp-cost

### ❌ Killed
- "Finance barrier is *primarily* procurement, not licensing" — nuanced down / refuted.
- "58.8% of banks cite clearer guidance as the #1 MRM barrier" — refuted.
- "Console-level monthly spend limits are the primary native cost guardrail vendors ship" — refuted.

### ⚠️ Still unanswered (the real gap)
**Realized solo-builder income for these *specific* niches** (AI FinOps / LLM-eval) was NOT
established — no citable Indie Hackers / MicroConf MRR/ARR figures surfaced. Demand and
barriers are well-evidenced; **realized revenue is not.** Close this before sizing the bet.
