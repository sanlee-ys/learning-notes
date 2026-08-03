"""Assert classifier eval numbers quoted in these notes against the published artifact.

WHY THIS EXISTS. Note 03 teaches how to read eval numbers, using the defense-news
classifier's own runs as the worked example. On 2026-07-19 its most recent figures were
v2's 88.9%, a day after v3.0.0 shipped 92.6% — correctly labelled as v2, but a reader
takes the last number in a note as the current one.

That matters more here than on a static page: **`kb-agent` indexes this repo**, so a
stale number in these notes is retrievable and speakable by an agent as today's accuracy.
`SYS-017` recorded exactly that propagation path when a wrong citation reached the
glossary; this is the same corpus, one file over.

HOW A NUMBER OPTS IN. Precede it with an invisible comment — the same convention the
architecture repo's `check_program_metrics.py` and the portfolio's
`check-published-metrics.cjs` use, so one habit covers every repo:

    category accuracy <!-- metric:category_accuracy -->92.6%

WHERE A MARKER MAY GO. Anywhere except the start of a line. In CommonMark/GFM a line
beginning with `<!--` opens an *HTML block*: it closes the paragraph above it and
suspends inline markdown parsing until the next blank line. A line-initial marker
therefore splits a paragraph on the rendered page and leaves `code` spans showing as
literal backticks — while the source looks fine and this checker reports a clean pass.
The invisibility is the whole point of the convention, and this is the one placement
where it stops being invisible, so it gets a rule rather than a habit. A marker must
always follow text on its line; wrap the prose around it rather than onto the next line.

This repo was clean when the rule was added (2026-08-02) — the sibling repos were not,
and `faithfulness-judge` had shipped it to a public README. Added here as prevention.

WHICH FILES EACH RULE REACHES. The value and unknown-key rules read the notes at the repo
ROOT, which is where every note lives today. The placement rule is swept over every `.md`
in the tree instead, and the difference is deliberate:

  - "Is this number still current?" is only meaningful for a present-tense claim, and the
    answer belongs to the artifact. Correctly scoped to the notes that make such claims.
  - "Does this file render correctly?" is true of every file. A line-initial marker breaks
    the page whether the figure beside it is live, historical, or a frozen v1 baseline.

Today those two sets are the same, because the root glob happens to cover every note. That
is the argument FOR the sweep, not against it: the moment a note moves into a subdirectory
it would silently leave the checker's reach, and the failure it would then be free to
commit is invisible in the source. Nothing the sweep reports can pressure anyone to restate
a number — the only fix it asks for is moving a marker onto the end of the previous line.

WHAT IS DELIBERATELY NOT MARKED. The v1 and v2 figures in the notes' historical blocks.
They are the *lesson* — this note's whole argument is that a number is inseparable from
how it was measured, so superseded figures stay exactly as first written. Marking them
would make this script rewrite history on every classifier release.

FAILURE POLICY (matches the sibling checks):
  - marked value mismatches artifact -> exit 1
  - unknown metric key               -> exit 1, a typo checks nothing and passes forever
  - marker at the start of a line    -> exit 1, it silently breaks the rendered page.
                                        Checked in every markdown file in the tree, and
                                        checked even when the artifact fetch fails — it
                                        reads no artifact, so an outage must not quietly
                                        switch it off.
  - zero marked figures              -> exit 1, a check verifying nothing reads as a pass
  - artifact fetch failure           -> exit 0, loudly. A GitHub outage must not redden
                                        an unrelated docs build.

Run locally:
    python scripts/check_published_metrics.py
"""

from __future__ import annotations

import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ARTIFACT_URL = (
    "https://raw.githubusercontent.com/sanlee-ys/defense-news-classifier/"
    "main/evals/metrics.json"
)

MARKER = re.compile(r"<!--\s*metric:([A-Za-z0-9_]+)\s*-->\s*\**\s*(\d+(?:\.\d+)?%?)")

# A marker that is the first non-whitespace thing on its line. See "WHERE A MARKER MAY
# GO" above: this is the one placement where an invisible marker stops being invisible,
# and it is invisible in the *source*, so nobody spots it in review. Matched loosely (any
# `metric:` marker, not just a well-formed one) because the damage is done by the `<!--`
# opening the line, whatever follows it.
LINE_INITIAL_MARKER = re.compile(r"^[ \t]*(<!--\s*metric:)", re.M)

# Fenced blocks and inline code spans. A marker written inside backticks is documentation
# OF the convention, not a use of it — these notes teach conventions, so an example of the
# marker will show up in prose sooner or later, and it must not trip the rule that the
# example exists to explain.
CODE = re.compile(r"```.*?```|`[^`\n]*`", re.S)

# Directories the placement sweep does not own: version control, agent scratch space,
# environments, caches, and the MkDocs build output. `.claude` holds agent worktrees —
# entire second checkouts of this repo — so walking it would report every finding twice
# under a path nobody edits. `node_modules` is listed although nothing here creates one,
# so the set does not have to be rediscovered if something ever does.
SWEEP_SKIP_DIRS = frozenset(
    {
        ".git",
        ".claude",
        ".venv",
        "venv",
        "site",
        "graphify-out",
        "node_modules",
        "__pycache__",
        ".pytest_cache",
        ".ruff_cache",
    }
)


def fetch_artifact() -> dict | None:
    """Fetch the published metrics artifact, or None if it cannot be read."""
    try:
        with urllib.request.urlopen(ARTIFACT_URL, timeout=15) as resp:  # noqa: S310
            if resp.status != 200:
                print(f"WARNING: HTTP {resp.status} fetching the metrics artifact.")
                return None
            return json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
        print(f"WARNING: could not fetch the metrics artifact: {exc}")
        return None


def same_value(shown: str, published: object) -> bool:
    """Compare numerically: JSON serialises 87.0 as 87, so a string compare lies."""
    try:
        return abs(float(shown.rstrip("%")) - float(str(published))) < 1e-9
    except ValueError:
        return shown.strip() == str(published).strip()


def _in_code(spans: list[tuple[int, int]], position: int) -> bool:
    return any(lo <= position < hi for lo, hi in spans)


def placement_problems(name: str, text: str, code: list[tuple[int, int]]) -> list[str]:
    """Every marker in `text` that opens a markdown HTML block by starting its line.

    Line numbers are counted on `text` exactly as handed in, which must be the RAW file
    rather than a code-stripped copy: stripping a fenced block to nothing shifts every
    line below it, and a confidently wrong line number is worse than none. Code is
    skipped by POSITION instead, which is why `code` is a parameter.
    """
    problems: list[str] = []
    for match in LINE_INITIAL_MARKER.finditer(text):
        if _in_code(code, match.start(1)):
            continue
        line = text.count("\n", 0, match.start(1)) + 1
        problems.append(
            f"{name}:{line}: a metric marker is the first thing on this line. "
            "That opens a markdown HTML block, which splits the paragraph and "
            "stops inline formatting until the next blank line - so the rendered "
            "page breaks while the source looks fine. Move the marker onto the "
            "end of the previous line; it must always follow text."
        )
    return problems


def sweep_paths(root: Path) -> list[Path]:
    """Every markdown file under `root` that the root-level glob does not already read.

    The complement of the notes `main()` loads, so a misplaced marker in a note is not
    reported twice. Union of the two is every `.md` in the repo.
    """
    found: list[Path] = []
    for path in root.rglob("*.md"):
        if not path.is_file():
            continue
        if SWEEP_SKIP_DIRS & set(path.relative_to(root).parts):
            continue
        if path.parent == root:
            continue
        found.append(path)
    return sorted(found)


def check_placement(root: Path, paths: list[Path]) -> list[str]:
    """Apply the placement rule — and only it — to every path in `paths`.

    Returns problems and nothing else: this pass has no values to compare and no markers
    to count, because "does this file render?" does not depend on the artifact. That is
    also why main() runs it even when the artifact fetch fails.
    """
    problems: list[str] = []
    for path in paths:
        text = path.read_text(encoding="utf-8")
        code = [m.span() for m in CODE.finditer(text)]
        problems += placement_problems(path.relative_to(root).as_posix(), text, code)
    return problems


def check_documents(
    documents: dict[str, str], published: dict[str, object]
) -> tuple[list[str], int]:
    """Check every marked figure in `documents` against `published`.

    Returns (problems, figures checked). Split out from main() so the rules can be
    exercised against literal markdown in tests without reaching the network.
    """
    known = set(published)
    problems: list[str] = []
    checked = 0

    for name, text in sorted(documents.items()):
        code = [m.span() for m in CODE.finditer(text)]

        problems += placement_problems(name, text, code)

        for key, shown in MARKER.findall(text):
            if key not in known:
                problems.append(
                    f"{name}: metric key '{key}' is not in the artifact. "
                    f"Known: {', '.join(sorted(known))}."
                )
                continue
            checked += 1
            if not same_value(shown, published[key]):
                problems.append(
                    f"{name}: '{key}' is written as {shown} but the classifier "
                    f"measured {published[key]}. The artifact is the source of truth."
                )

    return problems, checked


def main() -> int:
    """Check every marked figure in the notes against the artifact."""
    artifact = fetch_artifact()

    # Run the placement sweep before the fetch-failure bail, deliberately. Every other
    # rule needs the artifact, so an outage legitimately skips them; placement needs
    # nothing but the file on disk. A rule that quietly stops running whenever GitHub is
    # slow is a gate that did not actually run, which reads as a pass and is not one.
    swept = sweep_paths(REPO_ROOT)
    placement = check_placement(REPO_ROOT, swept)

    if artifact is None:
        if placement:
            print("MARKERS BREAK THE RENDERED PAGE:\n", file=sys.stderr)
            for problem in placement:
                print(f"  - {problem}\n", file=sys.stderr)
            print(
                "The metrics check itself was skipped (artifact fetch failed), but "
                "placement does not depend on the artifact.",
                file=sys.stderr,
            )
            return 1
        print(
            f"Published-metrics check SKIPPED (see warning above). Marker placement "
            f"still checked in {len(swept)} markdown file(s) outside the repo root."
        )
        return 0

    published = artifact.get("gold", {})
    documents = {
        path.name: path.read_text(encoding="utf-8")
        for path in sorted(REPO_ROOT.glob("*.md"))
    }
    problems, checked = check_documents(documents, published)
    problems += placement

    if problems:
        print("PUBLISHED METRICS ARE STALE:\n", file=sys.stderr)
        for problem in problems:
            print(f"  - {problem}\n", file=sys.stderr)
        print(
            "kb-agent indexes this repo, so a stale figure here is speakable by an "
            "agent as the current number. Do not silence this.",
            file=sys.stderr,
        )
        return 1

    if checked == 0:
        print(
            "No metric markers found. Either they were dropped or this check is "
            "inert - both are failures, because a check that verifies nothing reads "
            "as a pass.",
            file=sys.stderr,
        )
        return 1

    print(
        f"OK - {checked} quoted metric(s) match the classifier artifact "
        f"(v{artifact.get('version', '?')})."
    )
    # Say what each pass reached. A guard narrower than its claim surface reads as full
    # coverage unless it reports its own scope.
    print(
        f"     marker placement additionally checked in {len(swept)} markdown file(s) "
        f"outside the repo root; the value rules deliberately do not reach them."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
