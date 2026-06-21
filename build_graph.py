"""Build an interactive concept map of the learning notes.

Reads README.md (for each note's category + project tag) and every NN-*.md note
(for its title, TL;DR, and the in-text "note NN" cross-references), then writes a
single self-contained concept-map.html — a force-directed graph you can drag around.

    python build_graph.py

Like build_site.py, the .md files stay the single source of truth; this file is
always regenerated, never hand-edited. D3 is loaded from a CDN, so the first open
needs internet (after that the browser caches it).

What becomes what, in the graph:
  * node            = one note. Number shown inside; title beside it.
  * node colour     = its README category (Foundations / LLM app patterns / ...).
  * node size       = how many other notes point AT it (so hubs like 02/03 grow).
  * solid arrow     = a real "note NN" reference you wrote in the prose (directional).
  * faint dashed    = same-category link, so orphans (10/11/12) still cluster.
  * click a node    = jump to that note in your existing index.html (#anchor).
"""

from __future__ import annotations

import html
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "concept-map.html"

# Category -> colour. Order here is also the legend order.
CATEGORY_COLORS = {
    "Foundations": "#3a6ea5",        # blue
    "LLM app patterns": "#a5603a",   # rust
    "Data & method": "#4a8c5f",      # green
    "Engineering hygiene": "#8c6dae",# purple
}
DEFAULT_COLOR = "#6b6b6b"


# ---- Parse the README's "Concept map" list --------------------------------

def parse_readme() -> dict[int, dict]:
    """Map note number -> {category, project} by reading README's concept map.

    The README groups notes under `### <Category>` headings, one bullet each:
        - [x] 01 — Structured output via tool use *(both projects)*
    We only read inside the `## Concept map` section so other lists don't leak in.
    """
    meta: dict[int, dict] = {}
    readme = HERE / "README.md"
    if not readme.exists():
        return meta

    category = None
    in_map = False
    for line in readme.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if s.startswith("## "):                 # entering/leaving a top section
            in_map = s.lower().startswith("## concept map")
            category = None
            continue
        if not in_map:
            continue
        if s.startswith("### "):                 # a category heading
            category = s[4:].strip()
            continue
        m = re.match(r"-\s*\[.\]\s*(\d+)\s*—\s*(.*)", s)
        if m:
            num = int(m.group(1))
            tag = re.search(r"\*\((.*?)\)\*", m.group(2))
            meta[num] = {"category": category, "project": normalize_tag(tag.group(1) if tag else "")}
    return meta


def normalize_tag(raw: str) -> str:
    raw = raw.lower()
    if "both" in raw:
        return "both"
    if "kb-agent" in raw:
        return "kb-agent"
    if "classifier" in raw:
        return "classifier"
    return "other"


# ---- Parse each note ------------------------------------------------------

def first_heading(text: str) -> str:
    for raw in text.splitlines():
        if raw.startswith("# "):
            return raw[2:].strip()
    return ""


def short_title(heading: str) -> str:
    """'01 — Structured output via tool use' -> 'Structured output via tool use'."""
    return re.split(r"\s*—\s*", heading, maxsplit=1)[-1].strip()


def extract_tldr(text: str) -> str:
    """Grab the '> **TL;DR** ...' blockquote as a one-line tooltip string."""
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
    joined = re.sub(r"\*\*TL;DR\*\*\s*", "", joined)   # drop the label
    joined = re.sub(r"[*`]", "", joined)               # strip md emphasis
    return joined.strip()


def collect() -> tuple[list[dict], list[dict]]:
    meta = parse_readme()
    nodes: list[dict] = []
    prose_edges: set[tuple[int, int]] = set()   # (src, dst) directional
    numbers: set[int] = set()

    for path in sorted(HERE.glob("[0-9][0-9]-*.md")):
        num = int(path.stem[:2])
        numbers.add(num)
        body = path.read_text(encoding="utf-8")
        heading = first_heading(body)
        info = meta.get(num, {})
        nodes.append({
            "id": num,
            "anchor": path.stem,                       # -> index.html#<anchor>
            "num": f"{num:02d}",
            "title": short_title(heading) or path.stem,
            "tldr": extract_tldr(body),
            "category": info.get("category") or "Uncategorized",
            "project": info.get("project", "other"),
        })
        # In-text references: "note 07", "note 02", etc. -> directed edge.
        for ref in re.findall(r"\bnote\s*0*(\d+)\b", body, flags=re.IGNORECASE):
            dst = int(ref)
            if dst != num:
                prose_edges.add((num, dst))

    # Keep only references to notes that actually exist.
    prose_edges = {(a, b) for a, b in prose_edges if a in numbers and b in numbers}

    # Faint category links: connect every pair within a category, but skip any
    # pair already joined by a prose edge (so we never double-draw a connection).
    prose_pairs = {frozenset(e) for e in prose_edges}
    by_cat: dict[str, list[int]] = {}
    for n in nodes:
        by_cat.setdefault(n["category"], []).append(n["id"])
    cat_edges: list[dict] = []
    for ids in by_cat.values():
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                if frozenset((ids[i], ids[j])) not in prose_pairs:
                    cat_edges.append({"source": ids[i], "target": ids[j], "kind": "category"})

    # In-degree (how many prose refs point at a node) -> node size.
    indeg: dict[int, int] = {n["id"]: 0 for n in nodes}
    for _src, dst in prose_edges:
        indeg[dst] += 1
    for n in nodes:
        n["indegree"] = indeg[n["id"]]

    links = [{"source": a, "target": b, "kind": "prose"} for a, b in sorted(prose_edges)] + cat_edges
    return nodes, links


# ---- Page assembly --------------------------------------------------------

def build() -> None:
    nodes, links = collect()
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
  .node text.num {{ fill:#fff; font-weight:700; font-size:11px; text-anchor:middle;
    dominant-baseline:central; pointer-events:none; }}
  .node text.label {{ fill:var(--fg); font-size:11px; pointer-events:none;
    paint-order:stroke; stroke:var(--bg); stroke-width:3px; opacity:0; transition:opacity .12s; }}
  .node.hub text.label, .node.show text.label {{ opacity:1; }}
  .node.faded {{ opacity:.18; }}
  .node.faded text.label {{ opacity:0; }}
  .link.faded {{ opacity:.06; }}
  #tip {{ position:fixed; max-width:300px; padding:9px 12px; background:var(--card);
    border:1px solid var(--border); border-radius:8px; box-shadow:0 4px 14px rgba(0,0,0,.12);
    font-size:.82rem; pointer-events:none; opacity:0; transition:opacity .12s; z-index:9; }}
  #tip b {{ display:block; margin-bottom:3px; }}
  #tip span {{ color:var(--muted); }}
</style>
</head>
<body>
<header>
  <h1>Learning Notes — Concept Map</h1>
  <span class="hint">{n_notes} notes · {n_prose} prose links · drag to rearrange · hover to focus · click to read</span>
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
// Build a neighbour set so hover can highlight a node + everything it touches.
const neighbours = new Map(GRAPH.nodes.map(n => [n.id, new Set([n.id])]));
GRAPH.links.forEach(l => {{
  neighbours.get(l.source).add(l.target);
  neighbours.get(l.target).add(l.source);
}});

// Each category gets an anchor on a 2x2 grid -> 4 tidy clusters. Defined before
// the simulation because d3.forceX/forceY evaluate this accessor at setup time.
const CATS = Object.keys(COLORS);
function anchorXY(d) {{
  const i = CATS.indexOf(d.category);
  if (i < 0) return [W / 2, H / 2];
  const col = i % 2, row = Math.floor(i / 2);
  return [W * (0.34 + 0.34 * col), H * (0.34 + 0.36 * row)];
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
  .data(GRAPH.nodes).join("g")
  .attr("class", d => "node" + (d.indegree >= 2 ? " hub" : ""))
  .call(d3.drag().on("start", dragStart).on("drag", dragged).on("end", dragEnd))
  .on("mouseover", focus).on("mouseout", unfocus)
  .on("click", (e, d) => window.open("index.html#" + d.anchor, "_blank"));

node.append("circle").attr("r", radius).attr("fill", d => color(d.category));
node.append("text").attr("class", "num").text(d => d.num);
node.append("text").attr("class", "label")
  .attr("x", d => radius(d) + 5).attr("y", 4).text(d => short(d.title));

sim.on("tick", () => {{
  link.attr("x1", d => d.source.x).attr("y1", d => d.source.y)
      .attr("x2", d => d.target.x).attr("y2", d => d.target.y);
  node.attr("transform", d => `translate(${{d.x}},${{d.y}})`);
}});

// Hover: spotlight the node and its neighbours; show a TL;DR tooltip.
const tip = document.getElementById("tip");
function focus(event, d) {{
  const near = neighbours.get(d.id);
  node.classed("faded", n => !near.has(n.id));
  node.classed("show", n => near.has(n.id));
  link.classed("faded", l => l.source.id !== d.id && l.target.id !== d.id);
  tip.innerHTML = `<b>${{d.num}} — ${{escapeHtml(d.title)}}</b><span>${{escapeHtml(d.tldr)}}</span>`;
  tip.style.opacity = 1;
  moveTip(event);
}}
function unfocus() {{
  node.classed("faded", false);
  node.classed("show", false);
  link.classed("faded", false);
  tip.style.opacity = 0;
}}
node.on("mousemove", moveTip);
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
