"""Semantic comparison and entity-extraction tests."""

from __future__ import annotations

from src.catalog import get_change
from src.semantic_diff import compare_texts, extract_entities, segment_sentences


def test_segment_sentences():
    text = "First sentence. Second sentence! Third?"
    assert len(segment_sentences(text)) == 3


def test_kx_currency_deltas():
    change = get_change("THERAPY-KX-THRESHOLD-2026")
    result = compare_texts(change.old_snapshot, change.new_snapshot)
    entities = {(d.category, d.entity, d.direction) for d in result.entity_deltas}
    assert ("currency", "$2,480", "added") in entities
    assert ("currency", "$2,410", "removed") in entities


def test_extract_codes():
    ents = extract_entities("Codes 98979, 98984, and 98985 were added.")
    assert "98984" in ents["codes"]


def test_html_escaping_in_highlight():
    result = compare_texts("Fee is <old>", "Fee is <new> & more")
    assert "<old>" not in result.old_highlighted_html or "&lt;old&gt;" in result.old_highlighted_html
    assert "&lt;new&gt;" in result.new_highlighted_html or "new" in result.new_highlighted_html
