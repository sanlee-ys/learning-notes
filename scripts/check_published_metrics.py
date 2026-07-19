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

WHAT IS DELIBERATELY NOT MARKED. The v1 and v2 figures in the notes' historical blocks.
They are the *lesson* — this note's whole argument is that a number is inseparable from
how it was measured, so superseded figures stay exactly as first written. Marking them
would make this script rewrite history on every classifier release.

FAILURE POLICY (matches the sibling checks):
  - marked value mismatches artifact -> exit 1
  - unknown metric key               -> exit 1, a typo checks nothing and passes forever
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


def main() -> int:
    """Check every marked figure in the notes against the artifact."""
    artifact = fetch_artifact()
    if artifact is None:
        print("Published-metrics check SKIPPED (see warning above).")
        return 0

    published = artifact.get("gold", {})
    known = set(published)
    problems: list[str] = []
    checked = 0

    for path in sorted(REPO_ROOT.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        for key, shown in MARKER.findall(text):
            if key not in known:
                problems.append(
                    f"{path.name}: metric key '{key}' is not in the artifact. "
                    f"Known: {', '.join(sorted(known))}."
                )
                continue
            checked += 1
            if not same_value(shown, published[key]):
                problems.append(
                    f"{path.name}: '{key}' is written as {shown} but the classifier "
                    f"measured {published[key]}. The artifact is the source of truth."
                )

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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
