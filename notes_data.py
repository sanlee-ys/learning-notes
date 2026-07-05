"""Shared note model for the learning-notes build scripts.

Both build_site.py (the single-page reader) and build_graph.py (the concept map)
need the same facts about the notes: each note's number, title, category, TL;DR,
and the "note NN" cross-references that connect them. Parsing that in one place
means the two builders can never disagree, and new views (backlinks, a category
index, a category meta-map) all read from the same source. Pure standard library.

Single source of truth, as before: the NN-*.md files plus the README "Concept map"
registry. Nothing here is hand-maintained.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

HERE = Path(__file__).resolve().parent

# A "note NN" mention in a note's prose becomes a directed edge to note NN.
_REF_RE = re.compile(r"\bnote\s*0*(\d+)\b", re.IGNORECASE)


@dataclass
class Note:
    """One note, with its connections resolved both ways."""

    num: int
    path: Path
    anchor: str  # filename stem -> index.html#<anchor>
    heading: str  # full first "# " heading, e.g. "01 — Structured output..."
    title: str  # heading minus the "NN — " prefix
    tldr: str
    category: str
    project: str
    refs_out: list[int] = field(default_factory=list)  # notes this one cites
    refs_in: list[int] = field(default_factory=list)  # notes that cite this one


def normalize_tag(raw: str) -> str:
    """Map a free-text project tag from the README to one of the known buckets."""
    raw = raw.lower()
    if "both" in raw:
        return "both"
    if "kb-agent" in raw:
        return "kb-agent"
    if "classifier" in raw:
        return "classifier"
    return "other"


def parse_readme() -> tuple[dict[int, dict], list[str]]:
    """Read the README "## Concept map" list.

    Only lines inside the "## Concept map" section are read, so other lists in
    the README can't leak in.

    Returns:
        A (meta, category_order) tuple: meta maps note number -> {"category",
        "project"}; category_order is the order the "### Category" headings
        appear, so callers group and colour consistently.
    """
    meta: dict[int, dict] = {}
    order: list[str] = []
    readme = HERE / "README.md"
    if not readme.exists():
        return meta, order

    category = None
    in_map = False
    for line in readme.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if s.startswith("## "):  # entering/leaving a top-level section
            in_map = s.lower().startswith("## concept map")
            category = None
            continue
        if not in_map:
            continue
        if s.startswith("### "):  # a category heading
            category = s[4:].strip()
            if category not in order:
                order.append(category)
            continue
        m = re.match(r"-\s*\[.\]\s*(\d+)\s*—\s*(.*)", s)
        if m:
            num = int(m.group(1))
            tag = re.search(r"\*\((.*?)\)\*", m.group(2))
            meta[num] = {
                "category": category,
                "project": normalize_tag(tag.group(1) if tag else ""),
            }
    return meta, order


def first_heading(text: str) -> str:
    """Return the note's first "# " heading line, or "" if it has none."""
    for raw in text.splitlines():
        if raw.startswith("# "):
            return raw[2:].strip()
    return ""


def short_title(heading: str) -> str:
    """Strip the leading "NN — " prefix from a note heading.

    '01 — Structured output via tool use' -> 'Structured output via tool use'.
    """
    return re.split(r"\s*—\s*", heading, maxsplit=1)[-1].strip()


def extract_tldr(text: str) -> str:
    """Grab the '> **TL;DR** ...' blockquote as a one-line string (for tooltips)."""
    quote: list[str] = []
    collecting = False
    for raw in text.splitlines():
        s = raw.strip()
        if s.startswith(">"):
            collecting = True
            quote.append(s.lstrip("> ").rstrip())
        elif collecting:
            break
    joined = " ".join(quote)
    joined = re.sub(r"\*\*TL;DR\*\*\s*", "", joined)  # drop the label
    joined = re.sub(r"[*`]", "", joined)  # strip md emphasis
    return joined.strip()


def load_notes() -> tuple[list[Note], list[str]]:
    """Parse every NN-*.md note + the README registry into a connected model.

    Cross-reference edges are resolved both ways (refs_out / refs_in) and
    filtered to notes that exist, so a typo'd "note 99" never produces a
    dangling link.

    Returns:
        A (notes_sorted_by_number, category_order) tuple.
    """
    meta, order = parse_readme()
    notes: list[Note] = []
    for path in sorted(HERE.glob("[0-9][0-9]-*.md")):
        num = int(path.stem[:2])
        body = path.read_text(encoding="utf-8")
        heading = first_heading(body)
        info = meta.get(num, {})
        out = sorted({int(r) for r in _REF_RE.findall(body) if int(r) != num})
        notes.append(
            Note(
                num=num,
                path=path,
                anchor=path.stem,
                heading=heading,
                title=short_title(heading) or path.stem,
                tldr=extract_tldr(body),
                category=info.get("category") or "Uncategorized",
                project=info.get("project", "other"),
                refs_out=out,
            )
        )

    valid = {n.num for n in notes}
    by_num = {n.num: n for n in notes}
    for n in notes:
        n.refs_out = [d for d in n.refs_out if d in valid]
    for n in notes:
        for d in n.refs_out:
            by_num[d].refs_in.append(n.num)
    for n in notes:
        n.refs_in.sort()

    # Categories present: README order first, then any stragglers not in the registry.
    cats = list(order)
    for n in notes:
        if n.category not in cats:
            cats.append(n.category)
    return notes, cats
