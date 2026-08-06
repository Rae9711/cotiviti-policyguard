#!/usr/bin/env python3
"""Generate the two-page Word report (+ bibliography page) and Markdown source.

Reads actual evaluation metrics from evaluation/results.json when present so
the report does not invent numbers. Run after ``python -m evaluation.run_evaluation``.
"""

from __future__ import annotations

import json
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt

ROOT = Path(__file__).resolve().parent.parent
REPORT_DIR = ROOT / "report"
EVAL_JSON = ROOT / "evaluation" / "results.json"
DOCX_PATH = REPORT_DIR / "PolicyGuard_Report.docx"
MD_PATH = REPORT_DIR / "PolicyGuard_Report.md"


def _pct(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{100.0 * value:.1f}%"


def _load_metrics() -> dict:
    if EVAL_JSON.exists():
        return json.loads(EVAL_JSON.read_text(encoding="utf-8"))
    return {}


def build_markdown(metrics: dict) -> str:
    cd = metrics.get("change_detection", {})
    ed = metrics.get("effective_date_extraction", {})
    sc = metrics.get("source_citation", {})
    ab = metrics.get("abstention", {})
    rt = metrics.get("rule_tests", {})
    ra = metrics.get("reviewer_acceptance", {})

    return f"""# Content Management in Health Care: PolicyGuard for Payment-Policy Change Validation

**Haorui Wang — Cotiviti Generative AI Research Intern Assessment**  
**Topic 3: Content Management in Health Care**

---

## 1. Problem investigation

Payer organizations continuously ingest billing and coding policies (including CMS National Correct Coding Initiative guidance), clinical guidelines, and contract language. Material edits—especially effective-date thresholds and bundling/integral-service wording—must propagate into operational review logic without becoming unsupervised automation. Errors create two failure modes: (1) missed policy updates that allow inappropriate payment leakage, and (2) over-aggressive automation that lacks evidence, auditability, or expert accountability.

Cotiviti’s public positioning around payment accuracy and payment policy management highlights the operational need to keep policy intent aligned with validated edits and human oversight. The research question for this assessment is therefore practical: *Can a lightweight system detect source-grounded policy deltas, propose constrained declarative rules, abstain when language is ambiguous, and test approved rules on claims—without autonomous denial?*

## 2. Approach and proof of concept

**PolicyGuard** is a human-in-the-loop POC that:

1. Compares two policy versions with deterministic `difflib` differencing.
2. Grounds material changes with document, section, effective date, and evidence passage.
3. Proposes **Pydantic-validated JSON rules** (not executable Python).
4. Applies approved rules via a deterministic engine that can only **flag for review**.
5. Records Approve / Reject / Request Expert Interpretation decisions in an append-only audit log.

The demo uses synthetic CMS NCCI Chapter XI–*style* excerpts (not full manual republication) and fictional procedure codes (`EXAMPLE1`, `EXAMPLE2`). An ambiguous “generally considered integral” addition is designed to **abstain**, forcing expert interpretation—an explicit governance feature, not a defect.

## 3. Evaluation (POC-scale, actual measured outputs)

A hand-labeled gold set over the demo passages was scored by `evaluation/run_evaluation.py`. Results (demo-only; not production performance claims):

| Metric | Result |
| --- | --- |
| Change-detection precision | {_pct(cd.get("precision"))} |
| Change-detection recall | {_pct(cd.get("recall"))} |
| Effective-date extraction accuracy | {_pct(ed.get("accuracy"))} |
| Source-citation coverage | {_pct(sc.get("coverage"))} |
| Abstention / proposal correctness | {_pct(ab.get("accuracy"))} |
| Rule-test pass rate | {_pct(rt.get("pass_rate"))} |
| Simulated approve rate | {_pct(ra.get("simulated_approve_rate"))} |
| Simulated expert-interpretation rate | {_pct(ra.get("simulated_expert_rate"))} |

These metrics validate instrumentation and demo correctness. A production program would require larger multi-chapter corpora, inter-annotator agreement, and prospective review studies.

## 4. Strategic recommendation for Cotiviti

**Invest in a policy-change → validated-rule → expert-accountable workflow** adjacent to payment policy management:

- **Near term:** Deterministic diff + constrained rule schema + HITL queue for high-volume, machine-clear effective-date and code-list edits.
- **Mid term:** Optional LLM assistance only as a *proposal* layer with retrieval of source passages, schema validation, and mandatory abstention on low-confidence / qualitative language.
- **Governance:** Treat abstention and expert interpretation as first-class outcomes; prohibit model-authored executable code in payment paths; retain JSONL (or equivalent) audit for every promotion of a rule.

This aligns research-engineering practice with payment-integrity risk: speed on clear changes, friction on ambiguous ones.

## 5. Limitations and future work

- Demo corpus is intentionally tiny; metrics are not generalizable.
- No production claims adjudication, provider network data, or PHI.
- LLM proposal path is optional and not required for the demo.
- Future work: multi-document lineage, section-aware embedding retrieval, reviewer UX studies, and calibration of abstention thresholds against expert panels.

## 6. Conclusion

PolicyGuard demonstrates that content-management technology for healthcare payment policy can be engineered as an **evidence-grounded, schema-constrained, human-gated** system. The strategic value is not autonomous denial—it is faster, auditable translation of written policy into reviewable rules with explicit expert accountability.

---

# Bibliography

Centers for Medicare & Medicaid Services. (n.d.). *National Correct Coding Initiative (NCCI) program*. https://www.cms.gov/medicare/coding-billing/national-correct-coding-initiative-ncci-edits

Centers for Medicare & Medicaid Services. (n.d.). *Medicare NCCI Policy Manual* (Chapter XI and related chapters; cited conceptually—local demo files are synthetic adaptations, not full republication). https://www.cms.gov/medicare/coding-billing/national-correct-coding-initiative-ncci-edits/medicare-ncci-policy-manual

Cotiviti. (n.d.). *Payment accuracy*. https://www.cotiviti.com/solutions/payment-accuracy

Cotiviti. (n.d.). *Payment policy management*. https://www.cotiviti.com/solutions/payment-accuracy/payment-policy-management

American Medical Association. (n.d.). *CPT® overview* (cited for coding-system context only; no CPT content republished in this repository). https://www.ama-assn.org/practice-management/cpt

Dove, G., et al. related methods context: sequence differencing via Python `difflib` (Python Software Foundation documentation). https://docs.python.org/3/library/difflib.html

Pydantic. (n.d.). *Data validation using Python type hints*. https://docs.pydantic.dev/

Streamlit. (n.d.). *Streamlit documentation*. https://docs.streamlit.io/

Amodei, D., et al. (2016). *Concrete problems in AI safety* (abstention / safe failure modes framing). arXiv:1606.06565. https://arxiv.org/abs/1606.06565

Ribeiro, M. T., Singh, S., & Guestrin, C. (2016). “Why should I trust you?” Explaining the predictions of any classifier. *KDD* (evidence/explanation framing for reviewer trust). https://doi.org/10.1145/2939672.2939778
"""


def build_docx(metrics: dict) -> None:
    doc = Document()
    section = doc.sections[0]
    section.top_margin = Inches(0.7)
    section.bottom_margin = Inches(0.7)
    section.left_margin = Inches(0.85)
    section.right_margin = Inches(0.85)

    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(10)

    title = doc.add_paragraph()
    run = title.add_run(
        "Content Management in Health Care: PolicyGuard for Payment-Policy Change Validation"
    )
    run.bold = True
    run.font.size = Pt(13)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER

    meta = doc.add_paragraph()
    meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
    meta.add_run(
        "Haorui Wang — Cotiviti Generative AI Research Intern Assessment\n"
        "Topic 3: Content Management in Health Care"
    ).font.size = Pt(9)

    def h(text: str) -> None:
        p = doc.add_paragraph()
        r = p.add_run(text)
        r.bold = True
        r.font.size = Pt(11)

    def body(text: str) -> None:
        p = doc.add_paragraph(text)
        p.paragraph_format.space_after = Pt(6)
        for run in p.runs:
            run.font.size = Pt(10)

    h("1. Problem investigation")
    body(
        "Payer organizations continuously ingest billing and coding policies (including CMS "
        "National Correct Coding Initiative guidance), clinical guidelines, and contract language. "
        "Material edits—especially effective-date thresholds and bundling/integral-service wording—"
        "must propagate into operational review logic without becoming unsupervised automation. "
        "Errors create two failure modes: (1) missed policy updates that allow inappropriate payment "
        "leakage, and (2) over-aggressive automation that lacks evidence, auditability, or expert "
        "accountability."
    )
    body(
        "Cotiviti’s public positioning around payment accuracy and payment policy management "
        "highlights the operational need to keep policy intent aligned with validated edits and "
        "human oversight. The research question for this assessment is practical: Can a lightweight "
        "system detect source-grounded policy deltas, propose constrained declarative rules, abstain "
        "when language is ambiguous, and test approved rules on claims—without autonomous denial?"
    )

    h("2. Approach and proof of concept")
    body(
        "PolicyGuard is a human-in-the-loop POC that (1) compares policy versions with deterministic "
        "difflib differencing; (2) grounds material changes with document, section, effective date, "
        "and evidence; (3) proposes Pydantic-validated JSON rules (not executable Python); "
        "(4) applies approved rules via a deterministic engine that can only flag for review; and "
        "(5) records Approve / Reject / Request Expert Interpretation decisions in an append-only "
        "audit log. The demo uses synthetic CMS NCCI Chapter XI–style excerpts (not full manual "
        "republication) and fictional codes. An ambiguous “generally considered integral” addition "
        "is designed to abstain, forcing expert interpretation—an explicit governance feature."
    )

    h("3. Evaluation (POC-scale, measured)")
    cd = metrics.get("change_detection", {})
    ed = metrics.get("effective_date_extraction", {})
    sc = metrics.get("source_citation", {})
    ab = metrics.get("abstention", {})
    rt = metrics.get("rule_tests", {})
    ra = metrics.get("reviewer_acceptance", {})
    body(
        "A hand-labeled gold set over the demo passages was scored by evaluation/run_evaluation.py. "
        f"Measured results: change-detection precision {_pct(cd.get('precision'))}, recall "
        f"{_pct(cd.get('recall'))}; effective-date accuracy {_pct(ed.get('accuracy'))}; "
        f"source-citation coverage {_pct(sc.get('coverage'))}; abstention correctness "
        f"{_pct(ab.get('accuracy'))}; rule-test pass rate {_pct(rt.get('pass_rate'))}; "
        f"simulated approve rate {_pct(ra.get('simulated_approve_rate'))}; simulated expert-"
        f"interpretation rate {_pct(ra.get('simulated_expert_rate'))}. These metrics validate "
        "instrumentation and demo correctness only—not production performance."
    )

    h("4. Strategic recommendation for Cotiviti")
    body(
        "Invest in a policy-change → validated-rule → expert-accountable workflow adjacent to "
        "payment policy management. Near term: deterministic diff, constrained rule schema, and a "
        "HITL queue for machine-clear effective-date and code-list edits. Mid term: optional LLM "
        "assistance only as a proposal layer with source retrieval, schema validation, and mandatory "
        "abstention on low-confidence qualitative language. Governance: treat abstention as a "
        "first-class outcome; prohibit model-authored executable code in payment paths; retain an "
        "audit trail for every rule promotion."
    )

    h("5. Limitations, future work, and conclusion")
    body(
        "Limitations include a tiny demo corpus, no PHI or live adjudication, and an optional LLM "
        "path not required for the demo. Future work includes multi-document lineage, section-aware "
        "retrieval, reviewer UX studies, and abstention calibration against expert panels. "
        "Conclusion: PolicyGuard shows content-management technology for healthcare payment policy "
        "can be engineered as an evidence-grounded, schema-constrained, human-gated system. The "
        "strategic value is not autonomous denial—it is faster, auditable translation of written "
        "policy into reviewable rules with explicit expert accountability."
    )

    doc.add_page_break()
    bib_title = doc.add_paragraph()
    br = bib_title.add_run("Bibliography")
    br.bold = True
    br.font.size = Pt(13)

    refs = [
        "Centers for Medicare & Medicaid Services. (n.d.). National Correct Coding Initiative (NCCI) program. https://www.cms.gov/medicare/coding-billing/national-correct-coding-initiative-ncci-edits",
        "Centers for Medicare & Medicaid Services. (n.d.). Medicare NCCI Policy Manual (cited conceptually; local demo files are synthetic adaptations, not full republication). https://www.cms.gov/medicare/coding-billing/national-correct-coding-initiative-ncci-edits/medicare-ncci-policy-manual",
        "Cotiviti. (n.d.). Payment accuracy. https://www.cotiviti.com/solutions/payment-accuracy",
        "Cotiviti. (n.d.). Payment policy management. https://www.cotiviti.com/solutions/payment-accuracy/payment-policy-management",
        "American Medical Association. (n.d.). CPT® overview (context only; no CPT content republished). https://www.ama-assn.org/practice-management/cpt",
        "Python Software Foundation. (n.d.). difflib — Helpers for computing deltas. https://docs.python.org/3/library/difflib.html",
        "Pydantic. (n.d.). Data validation using Python type hints. https://docs.pydantic.dev/",
        "Streamlit. (n.d.). Streamlit documentation. https://docs.streamlit.io/",
        "Amodei, D., et al. (2016). Concrete problems in AI safety. arXiv:1606.06565. https://arxiv.org/abs/1606.06565",
        "Ribeiro, M. T., Singh, S., & Guestrin, C. (2016). “Why should I trust you?” Explaining the predictions of any classifier. KDD. https://doi.org/10.1145/2939672.2939778",
    ]
    for ref in refs:
        p = doc.add_paragraph(ref)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.left_indent = Inches(0.25)
        p.paragraph_format.first_line_indent = Inches(-0.25)
        for run in p.runs:
            run.font.size = Pt(9)

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    doc.save(DOCX_PATH)


def main() -> None:
    metrics = _load_metrics()
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    MD_PATH.write_text(build_markdown(metrics), encoding="utf-8")
    build_docx(metrics)
    print(f"Wrote {MD_PATH}")
    print(f"Wrote {DOCX_PATH}")


if __name__ == "__main__":
    main()
