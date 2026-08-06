# Content Management in Health Care: PolicyGuard for Payment-Policy Change Validation

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
| Change-detection precision | 100.0% |
| Change-detection recall | 100.0% |
| Effective-date extraction accuracy | 100.0% |
| Source-citation coverage | 100.0% |
| Abstention / proposal correctness | 100.0% |
| Rule-test pass rate | 100.0% |
| Simulated approve rate | 33.3% |
| Simulated expert-interpretation rate | 33.3% |

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
