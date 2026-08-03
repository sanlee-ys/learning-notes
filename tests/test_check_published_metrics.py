"""Failure-path tests for scripts/check_published_metrics.py.

The rules worth testing here are the ones whose failure mode is a QUIET PASS: a marker
the checker cannot see, a placement that breaks the rendered page while the source looks
fine. A mismatch is loud and self-reporting; these are not.

Every fixture below deliberately puts the marker AFTER text on its line except where the
line-initial rule is the thing under test. That is not cosmetic. In faithfulness-judge,
four existing tests had fixtures starting at column zero, which would have documented the
broken shape as the correct one and blessed the bug in the test suite.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import check_published_metrics as cpm  # noqa: E402
from check_published_metrics import (  # noqa: E402
    check_documents,
    check_placement,
    placement_problems,
    same_value,
    sweep_paths,
)

PUBLISHED: dict[str, object] = {
    "category_accuracy": 92.6,
    "category_macro_f1": 0.911,
    "domain_accuracy": 92.6,
}


def problems_for(markdown: str) -> list[str]:
    """Run the document rules over one in-memory note."""
    problems, _ = check_documents({"note.md": markdown}, PUBLISHED)
    return problems


# --- the line-initial rule -------------------------------------------------------


def test_marker_following_text_is_accepted() -> None:
    """The correct shape: the marker follows text, so it stays inside the paragraph."""
    assert problems_for("Scores category <!-- metric:category_accuracy -->92.6% now.\n") == []


def test_marker_at_column_zero_fails() -> None:
    markdown = "The classifier scores\n<!-- metric:category_accuracy -->92.6% category.\n"
    (problem,) = problems_for(markdown)
    assert "note.md:2" in problem
    assert "first thing on this line" in problem
    assert "end of the previous line" in problem


def test_marker_indented_inside_a_list_item_fails() -> None:
    """The shape that actually shipped, and the reason a naive `^<!--` check is not enough.

    Inside a list item the marker is indented to the item's content column, so it is not
    at column zero and does not *look* line-initial. It still is: an HTML block opens on
    up to three spaces of indentation, and relative to the list item's content this is
    column zero either way.
    """
    markdown = (
        "- **Classification quality** — on the gold set it is\n"
        "  <!-- metric:category_macro_f1 -->**0.911** macro-F1, which held.\n"
    )
    (problem,) = problems_for(markdown)
    assert "note.md:2" in problem
    assert "first thing on this line" in problem


def test_tab_indented_marker_fails() -> None:
    (problem,) = problems_for("Text above\n\t<!-- metric:domain_accuracy -->92.6%\n")
    assert "note.md:2" in problem


def test_every_line_initial_marker_is_reported_with_its_own_line() -> None:
    """One report per offence: a fixer needs the whole list, not the first one."""
    markdown = (
        "Current figures:\n"
        "<!-- metric:category_accuracy -->92.6% category,\n"
        "<!-- metric:domain_accuracy -->92.6% domain.\n"
    )
    reports = [p for p in problems_for(markdown) if "first thing on this line" in p]
    assert len(reports) == 2
    assert "note.md:2" in reports[0]
    assert "note.md:3" in reports[1]


def test_marker_inside_a_fenced_block_is_documentation_not_a_use() -> None:
    """These notes teach conventions, so the convention gets written down in prose."""
    markdown = (
        "How a number opts in:\n\n"
        "```markdown\n"
        "<!-- metric:category_accuracy -->92.6%\n"
        "```\n\n"
        "Real use: category <!-- metric:category_accuracy -->92.6% today.\n"
    )
    assert problems_for(markdown) == []


def test_marker_inside_an_inline_code_span_is_not_a_use() -> None:
    markdown = "Write it as `<!-- metric:KEY -->` before the number.\n"
    assert problems_for(markdown) == []


def test_line_initial_marker_fails_even_when_its_value_is_correct() -> None:
    """The placement is the defect. A correct value does not excuse a broken render."""
    markdown = "Text above\n<!-- metric:category_accuracy -->92.6%\n"
    assert problems_for(markdown), "a correct value must not suppress the placement rule"


# --- the placement rule sweeps subdirectories; the value rules do not ------------
#
# `main()` reads notes with a NON-RECURSIVE root glob, so a note in a subdirectory is
# invisible to every rule here. That set is empty today — which is the argument for the
# sweep, not against it: the first note to move into a subdirectory would silently leave
# the checker's reach, and the failure it would then be free to commit is invisible in
# the source. The same fixture discipline as above applies: a marker sits after text on
# its line unless line-initial placement is the thing under test.


def test_the_sweep_reaches_a_subdirectory_note(tmp_path) -> None:
    (tmp_path / "ROOT.md").write_text("root note\n", encoding="utf-8")
    (tmp_path / "archive").mkdir()
    (tmp_path / "archive" / "OLD.md").write_text("archived note\n", encoding="utf-8")
    swept = {p.relative_to(tmp_path).as_posix() for p in sweep_paths(tmp_path)}
    assert swept == {"archive/OLD.md"}, "root notes are already read by main()'s glob"


def test_a_line_initial_marker_in_a_subdirectory_is_caught(tmp_path) -> None:
    (tmp_path / "archive").mkdir()
    (tmp_path / "archive" / "OLD.md").write_text(
        "The classifier scores\n<!-- metric:category_accuracy -->92.6% category.\n",
        encoding="utf-8",
    )
    (problem,) = check_placement(tmp_path, sweep_paths(tmp_path))
    assert "archive/OLD.md:2" in problem
    assert "first thing on this line" in problem


def test_a_fenced_marker_in_a_subdirectory_passes(tmp_path) -> None:
    """Same file, same column-zero marker, only the fence differs."""
    (tmp_path / "archive").mkdir()
    (tmp_path / "archive" / "OLD.md").write_text(
        "How a number opts in:\n\n```markdown\n"
        "<!-- metric:category_accuracy -->92.6%\n```\n",
        encoding="utf-8",
    )
    assert check_placement(tmp_path, sweep_paths(tmp_path)) == []


def test_the_sweep_does_not_walk_generated_or_vendored_trees(tmp_path) -> None:
    """`site/` is the MkDocs build; a marker there is a copy of one in a source note."""
    for skipped in ("site", ".claude", "node_modules", "__pycache__", ".git"):
        (tmp_path / skipped).mkdir()
        (tmp_path / skipped / "STRAY.md").write_text(
            "generated\n<!-- metric:category_accuracy -->92.6%\n", encoding="utf-8"
        )
    assert sweep_paths(tmp_path) == []


def test_the_sweep_applies_only_the_placement_rule() -> None:
    """A stale value or unknown key outside the root is NOT a failure.

    The value rules answer "is this number still current?", which belongs to the notes
    that make present-tense claims. Placement answers "does this file render?".
    """
    stale = (
        "In June it measured <!-- metric:category_accuracy -->**88.9%**, "
        "and <!-- metric:typo_key -->**79.0%** on the synthetic set.\n"
    )
    assert placement_problems("archive/OLD.md", stale, []) == []


def test_placement_line_numbers_are_counted_on_the_raw_text() -> None:
    """Stripping code first would report every line after a fence short by its height."""
    markdown = (
        "intro\n\n```python\nx = 1\ny = 2\n```\n\ntext\n"
        "<!-- metric:category_accuracy -->92.6%\n"
    )
    (problem,) = placement_problems("archive/OLD.md", markdown, [])
    assert "archive/OLD.md:9" in problem


def test_placement_still_runs_when_the_artifact_fetch_fails(
    tmp_path, monkeypatch, capsys
) -> None:
    """An outage skips the value rules. It must not skip a rule that needs no artifact.

    Otherwise a bad merge lands green during a GitHub blip - a gate that did not
    actually run, which reads as a pass and is not one.
    """
    (tmp_path / "README.md").write_text("root note\n", encoding="utf-8")
    (tmp_path / "archive").mkdir()
    (tmp_path / "archive" / "OLD.md").write_text(
        "The classifier scores\n<!-- metric:category_accuracy -->92.6% category.\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(cpm, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(cpm, "fetch_artifact", lambda: None)
    assert cpm.main() == 1
    assert "first thing on this line" in capsys.readouterr().err


def test_a_clean_tree_still_skips_when_the_artifact_fetch_fails(
    tmp_path, monkeypatch, capsys
) -> None:
    """The other half: an outage with no placement fault is a loud skip, not a failure."""
    (tmp_path / "README.md").write_text("root note\n", encoding="utf-8")
    monkeypatch.setattr(cpm, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(cpm, "fetch_artifact", lambda: None)
    assert cpm.main() == 0
    assert "SKIPPED" in capsys.readouterr().out


# --- the pre-existing rules, still enforced --------------------------------------


def test_unknown_key_fails() -> None:
    (problem,) = problems_for("region <!-- metric:region_accuracy -->87.0%\n")
    assert "not in the artifact" in problem


def test_stale_value_fails() -> None:
    (problem,) = problems_for("category <!-- metric:category_accuracy -->88.9%\n")
    assert "88.9" in problem and "92.6" in problem


def test_marked_figures_are_counted() -> None:
    _, checked = check_documents(
        {"note.md": "category <!-- metric:category_accuracy -->92.6% today.\n"}, PUBLISHED
    )
    assert checked == 1


@pytest.mark.parametrize(
    ("shown", "published"),
    [("87.0%", 87), ("92.6%", 92.6), ("0.911", 0.911)],
)
def test_same_value_compares_numerically(shown: str, published: object) -> None:
    """JSON serialises 87.0 as 87, so a string compare would report a mismatch that isn't."""
    assert same_value(shown, published)
