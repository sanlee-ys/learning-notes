# 29 — Ablate your own scaffolding: was the hand-written part doing anything?

> **TL;DR** I hand-wrote a detailed spec to help an AI implement a tricky algorithm, and it
> worked. Then I deleted the spec and ran it again — **same result, same quality, first try.**
> The scaffolding I was proud of had been doing nothing, and I'd never have known without
> deliberately removing it.

## Plain idea

When you build something with an AI agent, you usually add scaffolding: a carefully written
contract, a worked example, a list of edge cases, a nudge about the tricky part. Then it
works, and you conclude the scaffolding is why.

That conclusion is unearned. You ran **one** condition. You have no idea what the run
without your scaffolding looks like, because you never did it.

The fix is borrowed from experimental science and called an **ablation**: remove one
component, hold everything else fixed, re-run, compare. If the result doesn't move, that
component wasn't carrying the weight you thought.

I tried this on a job where the model had to implement a genuinely fiddly piece of
networking logic — the kind with interacting timers where a naive fix makes other cases
fail. I'd written a detailed contract describing the algorithm's rules. The run passed
**38 of 38** checks after one repair pass.

Then I stripped the contract out of the prompt, leaving only the task and the automated
grader, and ran it again.

Identical outcome. 38 of 38, one pass, and the code it produced implemented the actual
standardized algorithm — correctly, unprompted. The model already knew. My contract had been
**a very confident restatement of something already in the weights.**

## Analogy

You put a lucky charm in your pocket before every exam and keep passing. Obvious conclusion:
the charm works. The only way to find out is to leave it at home once — and the reason
nobody does is that the test is scary and passing feels too important to risk.

Ablating your own work has the same flavour. You're deliberately running the condition that
could show your contribution was decorative.

## What made the comparison trustworthy

An ablation is only as good as the thing measuring it. Two conditions producing "looks fine"
tells you nothing.

What made this readable was an **automated grader that had been built before the
implementation existed** and that produced a hard number — 38 discrete checks, pass or fail,
no judgment call at the end. Both runs were scored by the same grader on the same cases, so
"identical" meant identical, not "seemed similar."

The order matters more than it sounds. Build the grader first and it encodes what correct
means, independent of whatever the model happens to produce. Build it after, and you'll
unconsciously write checks the existing output already passes (note 02, note 21 — same
red-then-green instinct as TDD).

And the grader itself needs checking. Feed it **deliberately broken inputs** and confirm it
catches each one for the right reason. A grader that silently never fires gives you a
flawless score and zero information — that's the same failure as a test suite that passes
because it asserts nothing (note 20).

## Why it matters

- **You're usually measuring your own effort, not its effect.** The scaffolding felt
  load-bearing because writing it was work. Effort spent is not evidence of effect.
- **A negative result is cheap and final.** One extra run answered a question I'd otherwise
  have carried for months, and it redirected the whole project. That's a better return than
  most features.
- **Model capability moves under you.** A contract that was genuinely necessary a year ago
  may be dead weight now, and nothing in your setup will tell you. The scaffolding doesn't
  announce when it stops mattering.
- **It's the honest version of "I used AI to build this."** "It worked" is a story.
  "It worked, and here's the run proving my part wasn't the reason" is a finding.

## Go deeper

- **Which scaffolding survives ablation?** Task framing, worked examples, edge-case lists,
  and output-format contracts are all doing different jobs. Ablate them one at a time and
  some almost certainly still earn their place.
- **Where does the effect come back?** Presumably there's a difficulty threshold below which
  the model doesn't need your help and above which it does. Finding that boundary is more
  useful than one data point on either side.
- **n=1 is not a result.** Same ablation, several runs, on a task with any randomness in it —
  does the delta stay at zero, or was one run lucky? (Note 03 on why a single number without
  spread is hard to read.)
- **The uncomfortable generalization:** how much of what we call prompt engineering would
  survive its own ablation?
