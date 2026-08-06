"""Tests that evaluation metrics run end-to-end against the demo gold set.

Proves the assessment evaluation package produces defined metrics without
inventing numbers at report-authoring time — values come from this pipeline.
"""

from evaluation.run_evaluation import run_evaluation


def test_run_evaluation_produces_core_metrics():
    """Full evaluation run returns precision/recall, abstention, and rule-test keys."""
    results = run_evaluation()
    assert results["change_detection"]["precision"] is not None
    assert results["change_detection"]["recall"] is not None
    assert results["abstention"]["accuracy"] is not None
    assert results["rule_tests"]["pass_rate"] is not None
    assert results["source_citation"]["coverage"] is not None
    # Demo gold set should be fully detected by the deterministic analyzer
    assert results["change_detection"]["precision"] == 1.0
    assert results["change_detection"]["recall"] == 1.0
    assert results["abstention"]["accuracy"] == 1.0
    assert results["rule_tests"]["pass_rate"] == 1.0
