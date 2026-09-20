# CLAUDE.md

Guidance for AI agents working in this repo.

## What this is

A public **portfolio / learning-notes site**, served via GitHub Pages at
`sanlee-ys.github.io/learning-notes`. Links to it get shared on social and other
platforms, so **a large share of traffic arrives on mobile.**

## Mobile is a first-class constraint

Treat every user-facing change as something that must work on a phone, not just a
desktop browser. This is a standing directive — apply it even when a request
doesn't mention mobile.

**This repo has a gate, since 2026-09-20.** Run it from the repo root before you
commit any change to layout, style, or markup:

```
python build_site.py && python build_graph.py && node scripts/mobile-qa.cjs
```

The gate renders every deployed page at **320, 360, 390 and 430px** and **fails on
horizontal overflow**. CI runs it in the `mobile-qa` job, and it runs the pass twice.
The second pass sets a 20px root font, which is a reader's large-text setting:

```
ROOT_FONT_PX=20 node scripts/mobile-qa.cjs
```

**Run the large-text pass. It finds what the default pass cannot.** A heading sizes
itself in rem, so a long token fits at a 16px root and widens the page at a 20px
root. `index.html` did that when the gate landed: a 369px scroll width against a
320px viewport, while the default pass was green. The fix is a rule that breaks the
token, not a px breakpoint, because a rem inside a media query does not follow the
injected root.

**Prerequisite: Playwright and a Chromium that matches the pin.** `node_modules/` is
untracked, and each Playwright version maps to one browser revision, so a fresh
clone cannot run the gate until you run both commands:

```
npm --prefix scripts ci
npm --prefix scripts exec -- playwright install chromium
```

Use `--prefix scripts` and not a bare `npx`. The prefix resolves the version that
`scripts/package.json` pins, which is the revision CI uses.

**If the gate cannot launch a browser, it is unrun, not green.** The gate reports an
unrun state for two more causes: a permitted external request that failed, and an
inline `<svg>` that stayed empty. `concept-map.html` loads D3 from a CDN and D3 draws
the whole graph, so a blocked request would leave an empty element that cannot
overflow. The gate would then pass a page it never rendered.

**The gate checks overflow only. You uphold the rest** — tap targets, readable text,
and the "☰ Contents" path below. **"Looks responsive" from reading the CSS is not a
check**; say it is unverified instead, the same way an unverified link gets labelled
rather than sent.

- Render at a narrow viewport (~390px wide, and 320px if the change touches layout):
  **no horizontal overflow**, no content cut off, text readable without pinch-zoom.
- Images and SVGs must scale to the viewport (`max-width:100%; height:auto`),
  never force a fixed pixel width wider than the screen.
- Interactive controls need real tap targets (~44px) and a way to be dismissed.
- The sidebar nav is desktop-only; on mobile it's reached through the floating
  **"☰ Contents"** overlay button. Keep that path working.

**Adaptable, but unflinching.** Adapt to what each task asks for — but if a change
would ship a broken or degraded mobile experience, don't quietly do it. Fix it,
or flag it and propose the fix. Don't wait to be asked about mobile.

## Generated files — edit the source, not the output

Two pages are **generated**; hand-edits to them get overwritten on the next build.

| Output | Generator | Source of truth |
| --- | --- | --- |
| `index.html` | `python build_site.py` | `README.md` + `NN-*.md` notes; CSS/JS/template live in `build_site.py` |
| `concept-map.html`, `assets/category-map.svg` | `python build_graph.py` | the `NN-*.md` notes + `notes_data.py` |

So:

- The page CSS/JS lives in the `CSS` and `SCRIPT` constants in `build_site.py`.
- The homepage hero image markup lives in `README.md` (passed through verbatim).
  Because `README.md` is also rendered on GitHub, prefer the `width`/`height`
  attributes over inline `style="…"` (GitHub strips `style`); the page's
  `img { max-width:100%; height:auto }` rule makes it responsive on the site.
- After editing any source, **regenerate** (`python build_site.py` and/or
  `python build_graph.py`) and commit the regenerated output alongside the source
  so the two never drift.

## Pull requests — batch related work

Prefer **one PR per coherent unit of work**, not one PR per tweak. Group related
changes (e.g. a fix plus its follow-up polish) and merge once the set is
complete. One-PR-per-change fragments history and forces a branch re-sync with
`main` between every merge. Open a separate PR only when changes are genuinely
unrelated.

<!-- shared:links-verify v1 -->
## Links — verify before sending (hard rule)

Links given in chat must resolve: **full `github.com/<owner>/<repo>/blob/<ref>/<path>` URLs only**, **verify the path exists on the ref before sending** (unverified → say so), and **branch links are perishable** (prefer `main` once merged). Full rule + rationale: [agent-ops `conventions/links-verify.md`](https://github.com/sanlee-ys/agent-ops/blob/main/conventions/links-verify.md).
<!-- /shared:links-verify -->
