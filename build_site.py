"""Build a single self-contained HTML page from the learning notes.

Reads README.md (as the intro) and every NN-*.md note in numeric order, converts
a small Markdown subset to HTML, and writes index.html — one file, no external
dependencies, fully offline. Open index.html in a browser, or re-run this after
editing/adding notes to regenerate it:

    python build_site.py

The .md files stay the single source of truth; index.html is always regenerated,
never hand-edited.
"""

from __future__ import annotations

import html
import re
from pathlib import Path

from notes_data import Note, load_notes

HERE = Path(__file__).resolve().parent
OUT = HERE / "index.html"


# ---- Markdown -> HTML (just the subset these notes use) --------------------

# Block-level HTML tags. A line that *starts* with one of these (e.g. the
# README's centered hero) is passed through verbatim instead of being escaped
# as paragraph text — the same idea as CommonMark's raw "HTML blocks".
_BLOCK_TAGS = {
    "p", "div", "figure", "figcaption", "table", "thead", "tbody", "tr", "td",
    "th", "section", "article", "header", "footer", "aside", "details",
    "summary", "nav", "dl", "dt", "dd", "ul", "ol", "blockquote", "pre",
    "img", "hr",
}


def _inline(text: str) -> str:
    """Inline formatting: code spans, links, bold, italic — with HTML escaping."""
    # Stash code spans first so we don't format or double-escape inside them.
    spans: list[str] = []

    def stash(m: re.Match) -> str:
        spans.append(m.group(1))
        return f"\x00{len(spans) - 1}\x00"

    text = re.sub(r"`([^`]+)`", stash, text)
    text = html.escape(text, quote=False)
    text = re.sub(
        r"\[([^\]]+)\]\(([^)]+)\)",
        lambda m: f'<a href="{html.escape(m.group(2), quote=True)}">{m.group(1)}</a>',
        text,
    )
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\*([^*\n]+)\*", r"<em>\1</em>", text)
    text = re.sub(r"\x00(\d+)\x00", lambda m: f"<code>{html.escape(spans[int(m.group(1))])}</code>", text)
    return text


def md_to_html(text: str) -> str:
    lines = text.split("\n")
    out: list[str] = []
    para: list[str] = []
    list_type: str | None = None
    list_items: list[str] = []

    def flush_para() -> None:
        if para:
            out.append(f"<p>{_inline(' '.join(para))}</p>")
            para.clear()

    def flush_list() -> None:
        nonlocal list_type, list_items
        if list_type:
            out.append(f"<{list_type}>")
            out.extend(f"  <li>{_inline(it)}</li>" for it in list_items)
            out.append(f"</{list_type}>")
            list_type, list_items = None, []

    def flush_blocks() -> None:
        flush_para()
        flush_list()

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Fenced code block — emit verbatim, no inline processing.
        if stripped.startswith("```"):
            flush_blocks()
            code: list[str] = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code.append(lines[i])
                i += 1
            i += 1  # skip closing fence
            out.append(f"<pre><code>{html.escape(chr(10).join(code))}</code></pre>")
            continue

        # Continuation of a wrapped list item (indented, while a list is open).
        if list_type and line[:1] == " " and stripped and not re.match(r"[-*]\s|\d+\.\s", stripped):
            list_items[-1] += " " + stripped
            i += 1
            continue

        if stripped == "":
            flush_blocks()
        elif stripped == "---":
            flush_blocks()
            out.append("<hr>")
        elif m := re.match(r"(#{1,6})\s+(.*)", stripped):
            flush_blocks()
            level = len(m.group(1))
            out.append(f"<h{level}>{_inline(m.group(2))}</h{level}>")
        elif stripped.startswith(">"):
            flush_blocks()
            quote: list[str] = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                q = lines[i].strip()[1:]
                quote.append(q[1:] if q.startswith(" ") else q)
                i += 1
            out.append(f"<blockquote>{_inline(' '.join(quote))}</blockquote>")
            continue
        elif (hm := re.match(r"<(/?)([a-zA-Z][\w-]*)", stripped)) and (
            not hm.group(1) and hm.group(2).lower() in _BLOCK_TAGS
        ):
            # Raw block-level HTML (the README hero) — copy verbatim, no escaping,
            # until the blank line that ends the block.
            flush_blocks()
            raw: list[str] = []
            while i < len(lines) and lines[i].strip() != "":
                raw.append(lines[i])
                i += 1
            out.append("\n".join(raw))
            continue
        elif m := re.match(r"[-*]\s+(.*)", stripped):
            flush_para()
            if list_type != "ul":
                flush_list()
                list_type = "ul"
            list_items.append(m.group(1))
        elif m := re.match(r"(\d+)\.\s+(.*)", stripped):
            flush_para()
            if list_type != "ol":
                flush_list()
                list_type = "ol"
            list_items.append(m.group(2))
        else:
            flush_list()
            para.append(stripped)
        i += 1

    flush_blocks()
    return "\n".join(out)


# ---- Page assembly ---------------------------------------------------------

def first_heading(text: str, fallback: str) -> str:
    for raw in text.split("\n"):
        if raw.startswith("# "):
            return raw[2:].strip()
    return fallback


def related_aside(note: Note, by_num: dict[int, Note]) -> str:
    """An auto "References / Referenced by" rail, built from the note's edges.

    Outgoing edges are the "note NN" mentions the author wrote; incoming edges are
    the reverse — the backlinks the concept map could never show inline. Returns ""
    when a note is isolated, so unconnected notes get no empty box.
    """
    rows: list[tuple[str, list[int]]] = []
    if note.refs_out:
        rows.append(("References", note.refs_out))
    if note.refs_in:
        rows.append(("Referenced by", note.refs_in))
    if not rows:
        return ""

    html_rows = []
    for label, nums in rows:
        chips = " ".join(
            f'<a href="#{by_num[m].anchor}">{m:02d} · {html.escape(by_num[m].title)}</a>'
            for m in nums
            if m in by_num
        )
        html_rows.append(
            f'<div class="rel-row"><span class="rel-label">{label}</span>{chips}</div>'
        )
    return '<aside class="related">\n' + "\n".join(html_rows) + "\n</aside>"


CSS = """
:root { --bg:#fbfaf7; --fg:#2b2b2b; --muted:#6b6b6b; --accent:#3a6ea5;
        --card:#ffffff; --border:#e7e3da; --code-bg:#f3f1ec; }
* { box-sizing: border-box; }
body { margin:0; background:var(--bg); color:var(--fg);
       font:16px/1.65 -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }
.layout { display:flex; max-width:1100px; margin:0 auto; }
nav { position:sticky; top:0; align-self:flex-start; width:260px; height:100vh;
      overflow-y:auto; padding:28px 18px; border-right:1px solid var(--border); }
nav h2 { font-size:.8rem; letter-spacing:.08em; text-transform:uppercase;
         color:var(--muted); margin:0 0 12px; }
nav a { display:block; padding:5px 8px; color:var(--fg); text-decoration:none;
        border-radius:6px; font-size:.9rem; }
nav a:hover { background:var(--code-bg); color:var(--accent); }
main { flex:1; min-width:0; padding:40px 48px 120px; }
section { margin-bottom:56px; padding-bottom:8px; border-bottom:1px dashed var(--border); }
section:last-child { border-bottom:none; }
h1 { font-size:1.9rem; margin:.2em 0 .6em; }
h2 { font-size:1.25rem; margin:1.6em 0 .4em; }
h3 { font-size:1.05rem; margin:1.3em 0 .3em; }
a { color:var(--accent); }
code { background:var(--code-bg); padding:.12em .35em; border-radius:4px;
       font:.88em "SF Mono", Consolas, "Liberation Mono", monospace; }
pre { background:var(--code-bg); border:1px solid var(--border); border-radius:8px;
      padding:14px 16px; overflow-x:auto; }
pre code { background:none; padding:0; font-size:.85rem; line-height:1.5; }
blockquote { margin:1em 0; padding:.8em 1.1em; background:var(--card);
             border-left:4px solid var(--accent); border-radius:0 8px 8px 0;
             box-shadow:0 1px 2px rgba(0,0,0,.04); }
blockquote p { margin:.3em 0; }
hr { border:none; border-top:1px solid var(--border); margin:1.4em 0; }
ul, ol { padding-left:1.4em; }
li { margin:.25em 0; }
#search { width:100%; padding:8px 10px; margin-bottom:14px; border:1px solid var(--border);
          border-radius:8px; background:#fff; color:var(--fg); font:.9rem inherit; }
#search:focus { outline:none; border-color:var(--accent);
                box-shadow:0 0 0 2px rgba(58,110,165,.25); }
#noresults { display:none; color:var(--muted); font-style:italic; }
.navgroup { margin-bottom:6px; }
.navgroup h3 { font-size:.68rem; letter-spacing:.09em; text-transform:uppercase;
               color:var(--muted); font-weight:700; margin:16px 8px 4px; }
aside.related { margin-top:26px; padding-top:14px; border-top:1px solid var(--border); }
.rel-row { display:flex; flex-wrap:wrap; gap:6px 8px; align-items:baseline; margin:.35em 0; }
.rel-label { flex:0 0 auto; min-width:104px; color:var(--muted); font-weight:700;
             text-transform:uppercase; font-size:.66rem; letter-spacing:.06em; }
aside.related a { padding:2px 9px; background:var(--code-bg); border-radius:12px;
                  text-decoration:none; font-size:.82rem; color:var(--accent); }
aside.related a:hover { background:#e9e4d8; }
img { max-width:100%; height:auto; }
/* Mobile "Contents" overlay nav — the sidebar is hidden on small screens, so a
   floating button reveals the same nav list as a full-screen overlay. */
#navtoggle, #navclose { display:none; }
@media (max-width:780px) {
  nav { display:none; }
  main { padding:28px 20px 80px; }
  #navtoggle { display:inline-flex; align-items:center; gap:7px; position:fixed;
    right:16px; bottom:16px; z-index:30; padding:11px 16px; border:none;
    border-radius:22px; background:var(--accent); color:#fff;
    font:600 .9rem/1 -apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
    box-shadow:0 2px 10px rgba(0,0,0,.22); cursor:pointer; }
  body.nav-open nav { display:block; position:fixed; inset:0; width:auto;
    height:100dvh; z-index:40; background:var(--bg); border-right:none;
    padding:22px 20px 90px; }
  body.nav-open { overflow:hidden; }
  #navclose { position:absolute; top:12px; right:14px; width:34px; height:34px;
    border:1px solid var(--border); border-radius:50%; background:var(--card);
    color:var(--fg); font-size:1.05rem; line-height:1; cursor:pointer; }
  body.nav-open #navclose { display:block; }
}
"""


# Client-side search: filter sections and nav links as you type. No dependencies.
SCRIPT = """
const q = document.getElementById('search');
const sections = [...document.querySelectorAll('main section')];
const links = [...document.querySelectorAll('nav a')];
const navFor = Object.fromEntries(links.map(a => [a.getAttribute('href').slice(1), a]));
const groups = [...document.querySelectorAll('.navgroup')];
const noresults = document.getElementById('noresults');
q.addEventListener('input', () => {
  const term = q.value.trim().toLowerCase();
  let shown = 0;
  for (const s of sections) {
    const hit = !term || s.textContent.toLowerCase().includes(term);
    s.style.display = hit ? '' : 'none';
    const a = navFor[s.id];
    if (a) a.style.display = hit ? '' : 'none';
    if (hit) shown++;
  }
  // Hide a category heading once all of its notes are filtered out.
  for (const g of groups) {
    const any = [...g.querySelectorAll('a')].some(a => a.style.display !== 'none');
    g.style.display = any ? '' : 'none';
  }
  noresults.style.display = shown ? 'none' : 'block';
});

// Mobile "Contents" overlay: toggle the otherwise-hidden sidebar, and close it
// once a destination is picked (or Esc / the close button).
const navToggle = document.getElementById('navtoggle');
const navClose = document.getElementById('navclose');
const navEl = document.querySelector('nav');
function setNav(open) {
  document.body.classList.toggle('nav-open', open);
  if (navToggle) navToggle.setAttribute('aria-expanded', open ? 'true' : 'false');
}
if (navToggle) navToggle.addEventListener('click', () => setNav(true));
if (navClose) navClose.addEventListener('click', () => setNav(false));
if (navEl) navEl.addEventListener('click', e => { if (e.target.closest('a')) setNav(false); });
document.addEventListener('keydown', e => { if (e.key === 'Escape') setNav(false); });
"""


def build() -> None:
    notes, cat_order = load_notes()
    by_num = {n.num: n for n in notes}

    def clean(t: str) -> str:
        return html.escape(re.sub(r"[`*]", "", t))

    # Overview section from the README.
    overview_title, overview_html = "Overview", ""
    readme = HERE / "README.md"
    if readme.exists():
        rb = readme.read_text(encoding="utf-8")
        overview_title = first_heading(rb, "Overview")
        overview_html = md_to_html(rb)

    # Note sections in numeric order, each with an auto backlink rail appended.
    sections = [f'<section id="overview">\n{overview_html}\n</section>']
    for n in notes:
        note_html = md_to_html(n.path.read_text(encoding="utf-8")) + related_aside(n, by_num)
        sections.append(f'<section id="{n.anchor}">\n{note_html}\n</section>')
    body = "\n".join(sections)

    # Category-grouped sidebar: overview link, then a group per category (README order).
    nav_parts = [f'<a href="#overview">{clean(overview_title)}</a>']
    for cat in cat_order:
        in_cat = [n for n in notes if n.category == cat]
        if not in_cat:
            continue
        rows = "\n".join(
            f'<a href="#{n.anchor}">{n.num:02d} · {html.escape(n.title)}</a>' for n in in_cat
        )
        nav_parts.append(f'<div class="navgroup"><h3>{html.escape(cat)}</h3>\n{rows}\n</div>')
    nav = "\n".join(nav_parts)

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Learning Notes</title>
<style>{CSS}</style>
</head>
<body>
<button id="navtoggle" type="button" aria-label="Open contents" aria-expanded="false">☰ Contents</button>
<div class="layout">
<nav><button id="navclose" type="button" aria-label="Close contents">✕</button><h2>Learning Notes</h2>
<input id="search" type="search" placeholder="Search notes…" autocomplete="off" aria-label="Search notes">
{nav}
</nav>
<main>
<p id="noresults">No matching notes.</p>
{body}
</main>
</div>
<script>{SCRIPT}</script>
</body>
</html>
"""
    OUT.write_text(page, encoding="utf-8")
    print(f"Wrote {OUT}  ({len(notes) + 1} sections, {len(page):,} bytes)")


if __name__ == "__main__":
    build()
