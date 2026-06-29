# Compliance Landmines (learned the hard way)

I work at a large bank. That's my biggest moat **and** my biggest constraint. Two ideas
died on compliance during this session — capturing *why* so I don't re-walk into them.

> ⚠️ Not legal advice. My firm's **Code of Conduct + employment agreement + Compliance team**
> are the actual authority. When in doubt, **disclose and ask** — a documented yes beats a
> clever quiet workaround every time.

---

## 💣 Landmine #1 — Selling to banks while employed at one

**The moat and the trap are the same fact.** "I work at a bank, I have deep domain access"
is *why* I'd win in the finance vertical — and *why* selling validation tooling to banks is
the sharpest possible conflict:

- Big banks require **disclosure / pre-approval of outside business activities.**
- Selling *to banks* invites the worst question: *am I leveraging confidential knowledge of
  my employer's MRM process?* Even if scrupulously not, the **appearance** is hard to disprove,
  and the firm's own validation methodology may itself be confidential.
- "Competing with / selling to the same industry as your employer" is the textbook thing
  these policies exist to catch.

### The conflict spectrum (risk drops fast as you move down)
1. **Highest conflict:** B2B SaaS/tooling sold *to banks.* ← the landmine.
2. **Much lower:** **teach the methodology** — course / writing / open eval framework.
   Teaching a skill ≠ competing ≠ using firm data. *(This is the leading idea.)*
3. **Lower still:** point the same eval skill at a **non-bank, non-competing** customer
   (lose some domain moat, dodge the conflict).
4. **Zero side-income conflict:** make it **career capital** instead — become the internal
   go-to for LLM eval / governance at work.

---

## 💣 Landmine #2 — Personal trading bot (PAD)

Idea was: build a trading bot, fund it with money I can lose, let it ride. **Killed by
Personal Account Dealing (PAD) rules** — which for a bank employee typically:

- require **pre-clearance of every trade** (kills "automated, let it ride"),
- mandate **minimum holding periods / ban day-trading**,
- restrict me to **approved brokers that send duplicate confirms to Compliance**,
- enforce **restricted lists & blackout windows**.

An always-on bot firing API orders is *exactly* the pattern these rules catch. Depending on
role, automated personal trading may be **prohibited or per-trade pre-cleared** — and **I'd
have to report it.** Shelved.

> Note: building/backtesting/**paper-trading** code is fine (no real trades). The line is
> **real personal trades**, which is where PAD bites.

---

## The standing rules I'm taking forward

- ✅ Build **only** on **synthetic / public data**, my own time, my own hardware. **Zero firm
  IP, zero firm data, ever.**
- ✅ Prefer the **teach-the-methodology** shape (lowest conflict, see `04-ideas-and-next-steps.md`).
- ✅ **Read the outside-activities / PAD policy** before building anything money-adjacent.
- ✅ If there's a disclosure process, **use it** — disclosed-and-approved > clever-and-quiet.
