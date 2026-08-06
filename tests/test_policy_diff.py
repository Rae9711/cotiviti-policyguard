"""Tests for policy version comparison (assessment: Stage 2 difflib).

Proves that :func:`src.policy_diff.compare_policy_versions` correctly
surfaces additions/deletions and that the demo policy pair exposes the
EXAMPLE1 material change without an LLM.
"""

from src.policy_diff import compare_policy_versions, format_diff_summary


def test_compare_detects_additions_and_deletions():
    """Unit fixture: revised and swapped lines appear in the correct buckets."""
    old = "Line A\nLine B\nLine C\n"
    new = "Line A\nLine B revised\nLine D\n"
    result = compare_policy_versions(old, new)

    assert "additions" in result
    assert "deletions" in result
    assert "Line B" in result["deletions"]
    assert "Line C" in result["deletions"]
    assert "Line B revised" in result["additions"]
    assert "Line D" in result["additions"]
    assert "Line A" not in result["additions"]
    assert "Line A" not in result["deletions"]


def test_compare_identical_texts_returns_empty():
    """Identical inputs must yield empty addition/deletion lists."""
    text = "Same policy line one.\nSame policy line two.\n"
    result = compare_policy_versions(text, text)
    assert result["additions"] == []
    assert result["deletions"] == []


def test_compare_demo_policies_surface_example1_change():
    """Demo 2025→2026 pair must surface EXAMPLE1 / effective-date language."""
    with open("data/policy_2025.txt", encoding="utf-8") as f:
        old = f.read()
    with open("data/policy_2026.txt", encoding="utf-8") as f:
        new = f.read()

    result = compare_policy_versions(old, new)
    joined_additions = "\n".join(result["additions"])
    assert "2026-01-01" in joined_additions or "EXAMPLE1" in joined_additions
    assert len(result["additions"]) > 0
    assert len(result["deletions"]) > 0


def test_format_diff_summary_counts():
    """Summary helper reports addition and deletion counts for the UI caption."""
    summary = format_diff_summary({"additions": ["a", "b"], "deletions": ["c"]})
    assert "2 addition" in summary
    assert "1 deletion" in summary
