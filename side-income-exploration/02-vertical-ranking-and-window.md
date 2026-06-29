# Vertical Ranking + Commoditization Window

If the play is **eval / governance / validation tooling for a regulated industry**, which
vertical? Ranked for *this* profile (solo, few hrs/week, no compliance certs, deep
finance/banking domain access, rigorous eval skills).

---

## The ranking

### 🥇 #1 — Banking / finance model-risk (SR 11-7 → SR 26-2) · barrier: **high (but asymmetric to my advantages)**
Best fit **because** my domain access + eval skills directly neutralize the gates.
Demand is structural and recurring: the bank's model-validation obligation is
**non-delegable**, so eval/validation evidence sells **into** that obligation rather than
competing with it. The SR 26-2 GenAI carve-out + "examined-but-unmandated" analogy gap means
banks must define their own control standard — a **content/methodology** need, not just a tool.
Highest demand-to-barrier ratio *for me specifically*.

### 🥈 #2 — Healthcare / HIPAA · barrier: **very-high**
Strong, fast-compressing demand — but winning factors (BAA posture, FHIR/EHR integration,
clinical validation, references from similar orgs) form a reference-and-integration moat a
few-hours/week solo with **no healthcare access** cannot build. "AI can write the code but
can't sign a BAA or pass the vendor questionnaire."

### 🥉 #3 — Government / FedRAMP (NIST 800-53) · barrier: **very-high**
Gated by one hard credential (FedRAMP ATO) being captured by large incumbents. FedRAMP 20x
eases it but still six figures + full-time. Worst **direct-entry** option for a part-time
solo, even though the long-run trajectory is easing.

---

## 💡 The non-obvious reframe (most valuable takeaway)

**Don't sell a security-reviewed SaaS to banks.** The procurement wall kills no-name solo
vendors (SOC 2 necessary-but-insufficient; deals die in security review).

**Instead, sell the *evidence and methodology* into the bank's own obligation:**
- eval harnesses, **MRM-mapped rubrics**, audit-defensible validation artifact packs,
  bias/explainability attestations — products the bank's *own* MRM team runs.
- This **bypasses the security-review wall** and runs on **domain credibility**, the one
  thing a stranger can't fake.
- It's a **content/methodology** product, not a B2B SaaS the bank must onboard.

> ⚠️ But see `03-compliance-landmines.md`: selling *to banks while employed at one* is its own
> conflict. The lowest-conflict expression of this reframe is **teaching the methodology
> generically** (course / writing / open framework), not selling artifacts to banks.

---

## ⏳ Commoditization survival window

- **Generic** cost-gov / eval / guardrail SaaS: **~12–18 months** (6–12 for generic FinOps).
  Already being eaten from two directions:
  - **Platform vendors:** Microsoft **Foundry Control Plane** natively bundles evaluations,
    guardrails, and end-to-end cost/trace observability (Eval/Monitoring/Tracing GA March 2026;
    auto-generating "Rubric" evaluator). Same bundle a standalone SaaS would sell — now sold by
    the platform the workload already runs on.
    - Source: learn.microsoft.com/en-us/azure/foundry/guardrails/guardrails-overview
  - **Open source:** LiteLLM + Portkey (Portkey open-sourced its gateway under Apache 2.0,
    March 2026) ship the core cost-gov + guardrail stack free. FinOps Foundation ratified
    **FOCUS 1.4** (June 2026) adding token-economics billing columns + launched a Tokenomics
    Foundation — standardizing the very telemetry a third-party would sell.
- **What survives longer (the defensible play):** NOT generic tooling — **regulated-domain
  evidence + methodology** the platform/OSS layer doesn't produce (bank-grade validation
  artifacts, MRM-mapped rubrics, audit-defensible docs, bias/explainability attestations).
  Finance is recommended partly **because** its moat is the slowest to commoditize from below.

---

## Open questions this raised
- Can a solo sell **into** the bank's MRM obligation as a methodology/evidence product
  (playbooks, harnesses, artifact packs) the bank's own staff runs — **bypassing** the
  SOC 2 / security-review wall? Structure suggests yes; no verified working GTM confirms it.
- What will the forthcoming **Fed/OCC/FDIC RFI** on bank GenAI use propose, and when? It
  could either create the bright-line mandate that supercharges demand, or prescribe controls
  incumbents satisfy natively.
- How fast do enterprise MRM-platform vendors (ValidMind / ModelOp / Databricks) add GenAI
  modules that commoditize the bank-evidence layer itself?
