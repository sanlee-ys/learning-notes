"""Build the concept-map views of the learning notes.

Reads the shared note model (notes_data.load_notes) — each note's category, title,
TL;DR, and the in-text "note NN" cross-references — and writes two things:

    python build_graph.py

  1. concept-map.html — a self-contained, force-directed graph of every note. D3 is
     loaded from a CDN, so the first open needs internet (then the browser caches it).
  2. assets/category-map.svg — a small, stable meta-map of the CATEGORIES (node size
     = notes in the category, edge width = cross-category references). Generated here
     at build time, so it is deterministic and never a hand-taken screenshot. This is
     the README hero image.

Like build_site.py, the .md files stay the single source of truth; both outputs are
always regenerated, never hand-edited.

What becomes what, in the interactive graph:
  * node            = one note. Number shown inside; title beside it.
  * node colour     = its README category (Foundations / LLM app patterns / ...).
  * node size       = how many other notes point AT it (so hubs like 02/03 grow).
  * solid arrow     = a real "note NN" reference you wrote in the prose (directional).
  * faint dashed    = same-category link, so orphans (10/11/12) still cluster.
  * hover a node    = spotlight its neighbourhood; click = pin that focus.
  * double-click    = open that note in your existing index.html (#anchor).
"""

from __future__ import annotations

import html
import json
import math
from pathlib import Path

from notes_data import load_notes

HERE = Path(__file__).resolve().parent
OUT = HERE / "concept-map.html"
SVG_OUT = HERE / "assets" / "category-map.svg"

# Category -> colour. Order here is also the legend order.
CATEGORY_COLORS = {
    "Foundations": "#3a6ea5",        # blue
    "LLM app patterns": "#a5603a",   # rust
    "Data & method": "#4a8c5f",      # green
    "Engineering hygiene": "#8c6dae",# purple
    "Systems & infrastructure": "#2f8f9d",  # teal
    "Working with AI agents": "#b04a7a",     # magenta-rose
}
DEFAULT_COLOR = "#6b6b6b"


# ---- Graph data (from the shared note model) ------------------------------

def collect(notes) -> tuple[list[dict], list[dict]]:
    """Turn the shared Note list into D3 nodes + links.

    Edges are the directional "note NN" prose references; faint same-category links
    are added so orphan notes still cluster. Node in-degree (how many prose refs
    point at it) drives node size in the page.
    """
    nodes = [
        {
            "id": n.num,
            "anchor": n.anchor,            # -> index.html#<anchor>
            "num": f"{n.num:02d}",
            "title": n.title,
            "tldr": n.tldr,
            "category": n.category,
            "project": n.project,
            "indegree": len(n.refs_in),
        }
        for n in notes
    ]

    prose_edges = sorted({(n.num, d) for n in notes for d in n.refs_out})

    # Faint category links: connect every pair within a category, but skip any pair
    # already joined by a prose edge (so we never double-draw a connection).
    prose_pairs = {frozenset(e) for e in prose_edges}
    by_cat: dict[str, list[int]] = {}
    for nd in nodes:
        by_cat.setdefault(nd["category"], []).append(nd["id"])
    cat_edges: list[dict] = []
    for ids in by_cat.values():
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                if frozenset((ids[i], ids[j])) not in prose_pairs:
                    cat_edges.append({"source": ids[i], "target": ids[j], "kind": "category"})

    links = [{"source": a, "target": b, "kind": "prose"} for a, b in prose_edges] + cat_edges
    return nodes, links


# ---- Category meta-map SVG (the stable README hero) -----------------------

def write_category_map_svg(notes, cats) -> Path:
    """Render the small category meta-map as a static SVG.

    One node per category (radius grows with how many notes it holds); an edge
    between two categories when notes in one reference notes in the other (width
    grows with how many such references). Fixed circular geometry → deterministic
    output, no force simulation, no screenshot. A handful of nodes regardless of how
    many notes exist, so it never becomes a hairball.
    """
    counts: dict[str, int] = {c: 0 for c in cats}
    for n in notes:
        counts[n.category] = counts.get(n.category, 0) + 1
    by_num = {n.num: n for n in notes}

    # Undirected cross-category reference weights.
    pair_w: dict[tuple[str, str], int] = {}
    for n in notes:
        for d in n.refs_out:
            c1, c2 = n.category, by_num[d].category
            if c1 == c2:
                continue
            key = tuple(sorted((c1, c2)))
            pair_w[key] = pair_w.get(key, 0) + 1

    W, H = 760, 440
    cx, cy, ring = W / 2, H / 2, 125.0
    n_cats = len(cats) or 1
    pos: dict[str, tuple[float, float]] = {}
    angs: dict[str, float] = {}
    for i, c in enumerate(cats):
        ang = -math.pi / 2 + 2 * math.pi * i / n_cats  # first category at top
        pos[c] = (cx + ring * math.cos(ang), cy + ring * math.sin(ang))
        angs[c] = ang

    max_count = max(counts.values()) or 1
    max_w = max(pair_w.values()) if pair_w else 1

    def node_r(c: str) -> float:
        return 26.0 + 30.0 * (counts[c] / max_count)

    def edge_w(w: int) -> float:
        return 1.5 + 6.0 * (w / max_w)

    parts: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
        f'role="img" aria-labelledby="title desc" '
        f'font-family="-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif">',
        '<title id="title">Learning notes — category map</title>',
    ]
    desc = "How the note categories connect. " + "; ".join(
        f"{c}: {counts[c]} notes" for c in cats
    )
    parts.append(f'<desc id="desc">{html.escape(desc)}</desc>')
    parts.append(f'<rect x="0" y="0" width="{W}" height="{H}" rx="12" fill="#fbfaf7"/>')

    # Edges first, so node circles sit on top.
    for (c1, c2), w in sorted(pair_w.items()):
        x1, y1 = pos[c1]
        x2, y2 = pos[c2]
        parts.append(
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'stroke="#c9c1b2" stroke-width="{edge_w(w):.1f}" stroke-linecap="round"/>'
        )

    # Category nodes + labels.
    for c in cats:
        x, y = pos[c]
        r = node_r(c)
        col = CATEGORY_COLORS.get(c, DEFAULT_COLOR)
        parts.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{col}" '
            f'stroke="#fff" stroke-width="3"/>'
        )
        parts.append(
            f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="middle" dominant-baseline="central" '
            f'fill="#fff" font-weight="700" font-size="20">{counts[c]}</text>'
        )
        # Bottom-side nodes (lower hemisphere, not the bottom pole) place their
        # label diagonally outward so it clears the large bottom node's circle.
        ca, sa = math.cos(angs[c]), math.sin(angs[c])
        gap = 16
        if sa > 0 and abs(ca) > 0.1:
            lx = x + (r + gap) * ca
            ly = y + (r + gap) * sa
            anchor = "start" if ca > 0 else "end"
        else:
            lx, ly, anchor = x, y + r + gap, "middle"
        parts.append(
            f'<text x="{lx:.1f}" y="{ly:.1f}" text-anchor="{anchor}" '
            f'fill="#2b2b2b" font-size="13" font-weight="600">{html.escape(c)}</text>'
        )

    parts.append("</svg>")
    SVG_OUT.parent.mkdir(exist_ok=True)
    SVG_OUT.write_text("\n".join(parts) + "\n", encoding="utf-8")
    return SVG_OUT


# ---- Page assembly --------------------------------------------------------

def build() -> None:
    notes, cats = load_notes()
    nodes, links = collect(notes)
    svg_path = write_category_map_svg(notes, cats)

    graph_json = json.dumps({"nodes": nodes, "links": links}, ensure_ascii=False)
    colors_json = json.dumps(CATEGORY_COLORS, ensure_ascii=False)
    legend = "\n".join(
        f'<span class="chip"><i style="background:{c}"></i>{html.escape(cat)}</span>'
        for cat, c in CATEGORY_COLORS.items()
    )
    n_prose = sum(1 for l in links if l["kind"] == "prose")

    page = PAGE.format(
        graph_json=graph_json,
        colors_json=colors_json,
        default_color=DEFAULT_COLOR,
        legend=legend,
        n_notes=len(nodes),
        n_prose=n_prose,
    )
    OUT.write_text(page, encoding="utf-8")
    print(f"Wrote {OUT}  ({len(nodes)} notes, {n_prose} prose links, {len(page):,} bytes)")
    print(f"Wrote {svg_path}  (category meta-map, {len(cats)} categories)")


PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Learning Notes — Concept Map</title>
<style>
  :root {{ --bg:#fbfaf7; --fg:#2b2b2b; --muted:#6b6b6b; --border:#e7e3da; --card:#fff; }}
  * {{ box-sizing:border-box; }}
  html, body {{ margin:0; height:100%; background:var(--bg); color:var(--fg);
    font:15px/1.5 -apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif; }}
  header {{ position:fixed; top:0; left:0; right:0; padding:14px 20px; z-index:5;
    display:flex; align-items:baseline; gap:18px; flex-wrap:wrap;
    background:linear-gradient(var(--bg),rgba(251,250,247,.85),transparent); }}
  header h1 {{ font-size:1.1rem; margin:0; font-weight:600; }}
  header .hint {{ color:var(--muted); font-size:.82rem; }}
  .legend {{ display:flex; gap:14px; flex-wrap:wrap; margin-left:auto; }}
  .chip {{ display:inline-flex; align-items:center; gap:6px; font-size:.8rem; color:var(--muted); }}
  .chip i {{ width:11px; height:11px; border-radius:3px; display:inline-block; }}
  svg {{ display:block; width:100vw; height:100vh; }}
  .link {{ stroke:#bdb7aa; }}
  .link.prose {{ stroke:#9a8f7a; stroke-width:1.6; }}
  .link.category {{ stroke-width:1; stroke-dasharray:3 4; opacity:.5; }}
  .node circle {{ stroke:#fff; stroke-width:2; cursor:pointer; }}
  .node.pinned circle {{ stroke:#2b2b2b; stroke-width:3; }}
  .node text.num {{ fill:#fff; font-weight:700; font-size:11px; text-anchor:middle;
    dominant-baseline:central; pointer-events:none; }}
  .node text.label {{ fill:var(--fg); font-size:11px; pointer-events:none;
    paint-order:stroke; stroke:var(--bg); stroke-width:3px; }}
  .node.faded {{ opacity:.2; }}
  .link.faded {{ opacity:.06; }}
  #tip {{ position:fixed; max-width:300px; padding:9px 12px; background:var(--card);
    border:1px solid var(--border); border-radius:8px; box-shadow:0 4px 14px rgba(0,0,0,.12);
    font-size:.82rem; pointer-events:none; opacity:0; transition:opacity .12s; z-index:9; }}
  #tip b {{ display:block; margin-bottom:3px; }}
  #tip span {{ color:var(--muted); }}
  #tip span.open {{ display:block; margin-top:5px; color:#9a8f7a; font-size:.72rem; }}
</style>
</head>
<body>
<header>
  <h1>Learning Notes — Concept Map</h1>
  <span class="hint">{n_notes} notes · {n_prose} prose links · hover to focus · click to pin · double-click to open</span>
  <div class="legend">{legend}</div>
</header>
<svg></svg>
<div id="tip"></div>
<script src="https://cdn.jsdelivr.net/npm/d3@7"></script>
<script>
const GRAPH = {graph_json};
const COLORS = {colors_json};
const DEFAULT_COLOR = "{default_color}";
const color = c => COLORS[c] || DEFAULT_COLOR;
const radius = d => 13 + 3.2 * (d.indegree || 0);
const short = s => (s && s.length > 34) ? s.slice(0, 33).trimEnd() + "…" : s;

const svg = d3.select("svg");
let W = window.innerWidth, H = window.innerHeight;
svg.attr("viewBox", [0, 0, W, H]);

// Arrowhead for directional prose links.
svg.append("defs").append("marker")
  .attr("id", "arrow").attr("viewBox", "0 -5 10 10").attr("refX", 22)
  .attr("markerWidth", 6).attr("markerHeight", 6).attr("orient", "auto")
  .append("path").attr("d", "M0,-4L9,0L0,4").attr("fill", "#9a8f7a");

const root = svg.append("g");
// Build a neighbour set so focus can highlight a node + everything it touches.
const neighbours = new Map(GRAPH.nodes.map(n => [n.id, new Set([n.id])]));
GRAPH.links.forEach(l => {{
  neighbours.get(l.source).add(l.target);
  neighbours.get(l.target).add(l.source);
}});

// Each category gets an anchor evenly spaced on a ring, so the clusters stay tidy for
// any number of categories (not just 4). Defined before the simulation because
// d3.forceX/forceY evaluate this accessor at setup time.
const CATS = Object.keys(COLORS);
function anchorXY(d) {{
  const i = CATS.indexOf(d.category);
  if (i < 0) return [W / 2, H / 2];
  const ang = -Math.PI / 2 + 2 * Math.PI * i / CATS.length;
  return [W / 2 + W * 0.30 * Math.cos(ang), H / 2 + H * 0.32 * Math.sin(ang)];
}}

const sim = d3.forceSimulation(GRAPH.nodes)
  .force("link", d3.forceLink(GRAPH.links).id(d => d.id)
    .distance(l => l.kind === "prose" ? 95 : 150).strength(l => l.kind === "prose" ? 0.55 : 0.06))
  .force("charge", d3.forceManyBody().strength(-360))
  .force("collide", d3.forceCollide(d => radius(d) + 20))
  .force("x", d3.forceX(d => anchorXY(d)[0]).strength(0.12))
  .force("y", d3.forceY(d => anchorXY(d)[1]).strength(0.12));

const link = root.append("g").selectAll("line")
  .data(GRAPH.links).join("line")
  .attr("class", d => "link " + d.kind)
  .attr("marker-end", d => d.kind === "prose" ? "url(#arrow)" : null);

const node = root.append("g").selectAll("g")
  .data(GRAPH.nodes).join("g").attr("class", "node")
  .call(d3.drag().on("start", dragStart).on("drag", dragged).on("end", dragEnd))
  .on("mouseover", hover).on("mouseout", hoverOut)
  .on("click", pinToggle)
  .on("dblclick", (event, d) => {{ event.preventDefault(); window.open("index.html#" + d.anchor, "_blank"); }});

node.append("circle").attr("r", radius).attr("fill", d => color(d.category));
node.append("text").attr("class", "num").text(d => d.num);
const labelSel = node.append("text").attr("class", "label")
  .attr("x", d => radius(d) + 5).attr("y", 4).text(d => short(d.title));
// Measure each label once so the de-overlap pass below can box them.
labelSel.each(function(d) {{ d.labelW = this.getComputedTextLength(); }});

sim.on("tick", () => {{
  link.attr("x1", d => d.source.x).attr("y1", d => d.source.y)
      .attr("x2", d => d.target.x).attr("y2", d => d.target.y);
  node.attr("transform", d => `translate(${{d.x}},${{d.y}})`);
  relabel();
}});

// Greedy label de-overlap: place labels by priority (hubs first); hide any that
// would collide with one already placed. Keeps the resting map fully readable.
const labelOrder = GRAPH.nodes.slice().sort((a, b) => (b.indegree - a.indegree) || (a.id - b.id));
function relabel() {{
  const placed = [];
  for (const d of labelOrder) {{
    const w = d.labelW || 60, h = 13;
    const x0 = d.x + radius(d) + 5, y0 = d.y - h / 2, x1 = x0 + w, y1 = d.y + h / 2;
    let ok = true;
    for (const p of placed) {{
      if (x0 < p.x1 && x1 > p.x0 && y0 < p.y1 && y1 > p.y0) {{ ok = false; break; }}
    }}
    d.shown = ok;
    if (ok) placed.push({{ x0, y0, x1, y1 }});
  }}
  labelSel.style("display", d => d.shown ? null : "none");
}}

// Focus = spotlight a node + its neighbours and show a TL;DR tooltip. Hover focuses
// transiently; a click PINS the focus so you can study one note's neighbourhood
// (click the same node or empty space to release; double-click opens the note).
const tip = document.getElementById("tip");
let pinned = null;
function applyFocus(d) {{
  const near = neighbours.get(d.id);
  node.classed("faded", n => !near.has(n.id));
  node.classed("pinned", n => pinned && n.id === pinned.id);
  link.classed("faded", l => l.source.id !== d.id && l.target.id !== d.id);
  tip.innerHTML = `<b>${{d.num}} — ${{escapeHtml(d.title)}}</b><span>${{escapeHtml(d.tldr)}}</span>`
    + `<span class="open">double-click to open →</span>`;
  tip.style.opacity = 1;
}}
function clearFocus() {{
  node.classed("faded", false).classed("pinned", false);
  link.classed("faded", false);
  tip.style.opacity = 0;
}}
function hover(event, d) {{ if (!pinned) {{ applyFocus(d); moveTip(event); }} }}
function hoverOut() {{ if (!pinned) clearFocus(); }}
function pinToggle(event, d) {{
  event.stopPropagation();
  if (pinned && pinned.id === d.id) {{ pinned = null; clearFocus(); return; }}
  pinned = d;
  applyFocus(d);
  moveTip(event);
}}
// A click on empty canvas releases a pinned focus.
svg.on("click", () => {{ if (pinned) {{ pinned = null; clearFocus(); }} }});
node.on("mousemove", event => {{ if (!pinned) moveTip(event); }});
function moveTip(event) {{
  const pad = 16;
  let x = event.clientX + pad, y = event.clientY + pad;
  if (x + 320 > window.innerWidth) x = event.clientX - 320;
  tip.style.left = x + "px"; tip.style.top = y + "px";
}}
function escapeHtml(s) {{ const d = document.createElement("div"); d.textContent = s || ""; return d.innerHTML; }}

function dragStart(event, d) {{ if (!event.active) sim.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y; }}
function dragged(event, d) {{ d.fx = event.x; d.fy = event.y; }}
function dragEnd(event, d) {{ if (!event.active) sim.alphaTarget(0); d.fx = null; d.fy = null; }}

window.addEventListener("resize", () => {{
  W = window.innerWidth; H = window.innerHeight;
  svg.attr("viewBox", [0, 0, W, H]);
  sim.force("x", d3.forceX(d => anchorXY(d)[0]).strength(0.12));
  sim.force("y", d3.forceY(d => anchorXY(d)[1]).strength(0.12));
  sim.alpha(0.3).restart();
}});
</script>
</body>
</html>
"""


if __name__ == "__main__":
    build()
