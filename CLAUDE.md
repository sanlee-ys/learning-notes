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

- Verify at a narrow viewport (~390px wide): **no horizontal overflow**, no
  content cut off, text remains readable without pinch-zoom.
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

## Links — verify before sending (hard rule)

Added 2026-07-04 after repeated 404s from links given in chat. Any clickable
reference given to the user must actually resolve:

1. **Full URLs only.** Point at files with the complete
   `https://github.com/<owner>/<repo>/blob/<ref>/<path>` URL — never a
   local-clone path like `<repo-folder>/materials/foo.md`, whose leading
   repo-folder segment doubles when pasted after a GitHub branch URL and 404s.
2. **Verify before sending.** Confirm the exact path exists on the exact ref
   before linking (e.g. GitHub MCP `get_file_contents`, or `git ls-tree
   origin/<branch> -- <path>` after a confirmed push). Unverified links do not
   get sent — say "unverified" instead.
3. **Branch links are perishable.** A `blob/<feature-branch>` URL dies when the
   branch merges and is deleted. Flag branch-scoped links as such; prefer
   `main` URLs once the work has merged.

If a link 404s, the failure mode was here — fix the process, not just the link.
