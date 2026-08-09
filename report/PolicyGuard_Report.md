# A Human-in-the-Loop Approach to Healthcare Content Management

**Haorui (Rae) Wang**  
**Cotiviti Intern Assessment | August 2026**

## Abstract

Healthcare billing and coding content changes through annual manuals, fee schedules, and program guidance, but each change must ultimately become consistent operational logic. This paper evaluates PolicyGuard, a controlled proof of concept for a PolicyOps workflow that compares policy versions, preserves source evidence, proposes schema-validated review rules, tests them on synthetic claims, and records expert decisions. Rather than measuring model accuracy, the evaluation asks whether the workflow can recover specified policy changes, automate only structurally decidable cases, and abstain when clinical judgment is required. Across five curated CY 2025-2026 changes and 604 synthetic claims, PolicyGuard produced four review rules and one abstention, routing 55 claims to human review. The results support PolicyGuard as a pre-deployment policy-validation layer for Cotiviti, not an automated adjudicator.

## 1. Introduction

Healthcare content management is the controlled acquisition, versioning, interpretation, and operational use of billing policies, coding manuals, clinical guidance, fee schedules, and payer-provider contracts. In payment integrity, this content is not merely reference material: effective dates, code lists, modifiers, thresholds, and exceptions become edits, review criteria, and reimbursement configurations. This paper uses PolicyOps to describe the lifecycle from authoritative evidence to comparison, rule proposal, testing, expert approval, deployment, and monitoring. The need is increasing because annual policy updates create repeated interpretation work, while AI-assisted research can accelerate extraction without eliminating the need for source traceability and expert accountability. Cotiviti is a natural setting for this approach because its Payment Policy Management capability already supports health plans in tailoring, testing, and executing clinical and payment policies, and its responsible-AI position emphasizes accuracy, transparency, security, and accountability (Cotiviti, n.d.-a, n.d.-b).

## 2. Methods

PolicyGuard Intelligence Studio was evaluated as a controlled proof of concept. Its source layer contains nine first-party public-source entries and five curated CY 2025-2026 change records chosen to represent five common transformation problems: a retired procedure code, a therapy threshold, a telehealth facility-fee update, new remote-therapeutic-monitoring codes, and an ambiguous skilled-therapy narrative (Wang, 2026). Policy text is segmented into sentences and compared using TF-IDF unigram/bigram vectors with cosine similarity plus lexical sequence matching. Regular expressions separately recover code patterns, dates, dollar values, modifiers, and percentages so material entity changes remain visible even when surrounding language is similar.

A policy change becomes a claim-level rule only when all required facts are available in structured claim fields. Pydantic validates a declarative schema and allowlisted operators, after which a deterministic interpreter executes the conditions. No large language model was invoked in the reported experiments, and the system never executes generated Python or SQL. Its only claim-level action is `flag_for_review`. A fixed seed generated 600 synthetic rows, and four named boundary cases produced N = 604 rows with no PHI. Four administrative changes were executable; the skilled-therapy item was required to abstain because procedure and payment fields alone cannot establish clinical purpose. Verification used positive/negative fixtures for each executable rule, six pre-specified entity deltas, provenance checks for all five change records, two abstention checks, and nine automated tests (Wang, 2026).

## 3. Results: POC Conformance and Synthetic Workflow Impact

PolicyGuard was measured as a controlled demonstrator, not as a production payment-integrity model. The unit of automation was a schema-validated declarative rule or an explicit abstention. The checks below answer whether the implemented workflow behaves as specified on known fixtures; they do not estimate real-claim precision, recall, reviewer agreement, or financial recovery.

### 3.1 Correctness of Specified Behavior

**Table 1. POC conformance checks**

| Check family | n | Passed | What the check establishes |
| --- | --- | --- | --- |
| Rule assertions | 8 | 8 | Effective-date, KX, fee-tolerance, and RTM logic matched the intended truth table. |
| Entity-delta recovery | 6 | 6 | Target dates, dollar amounts, and codes were recovered from before/after snapshots. |
| Source provenance | 5 changes | 5/5 | Every curated change retained organization, document, locator, and effective date. |
| Abstention | 2 | 2 | The clinical-purpose item emitted no claim rule and stored a human-readable reason. |

All specified fixtures behaved as intended. The 8/8, 6/6, and 2/2 ratios should therefore be read as reproducible conformance to the demonstration contract, not as “100% model accuracy.” These checks establish correct behavior on the small, known fixture set; they do not establish generalization to production claims.

### 3.2 Portfolio Impact on Synthetic Claims

**Table 2. Synthetic review-queue output**

| Quantity | Observed value |
| --- | --- |
| Claims evaluated | 604 |
| Unique claims routed to review | 55 (9.1%) |
| Distinct synthetic providers in queue | 33 |
| Paid amount associated with flagged rows | $5,627.13 |
| Flags by change | KX 22 \| 94662 18 \| Q3014 10 \| RTM 5 |

*Note.* Paid amount in scope is a sum over flagged synthetic rows; it is not overpayment, recovery, fraud, waste, or savings.

Applying the four approved rules produced a review queue rather than a denial file. Fifty-five of 604 rows (9.1%) were routed to human review, representing 33 synthetic providers and $5,627.13 in paid amount in scope. The KX threshold generated the largest queue (22 rows), followed by post-deletion use of 94662 (18), Q3014 fee variance (10), and RTM mapping (5). The abstention scenario produced zero claim flags by design. The practical result is concentration: each approved policy interpretation is represented once, tested once, and then applied consistently to candidate claims while preserving claim-level human review.

### 3.3 Workflow Comparison (Illustrative, Not a Labor Study)

Relative to a simplified counterfactual in which a reviewer independently reinterprets the changed policy for all 604 claims, the POC changes the decision grain. Five policy-level human gates - four executable proposals and one documented abstention - replace 604 repeated policy-interpretation events, a 99.2% reduction under that accounting assumption. Claim-level review is not eliminated: 55/604 rows (9.1%) enter the queue, while the remaining 90.9% are simply not flagged by these four rules and are not auto-adjudicated. The four executable rules concentrate 55 queued claims, or about 13.8 flagged rows per rule-level gate. These figures describe workflow compression in this synthetic demonstration, not measured productivity or staffing savings.

## 4. Conclusion and Value to Cotiviti

The POC suggests a concrete role upstream of Cotiviti's existing policy execution: policy-change intake and pre-deployment validation. Instead of asking reviewers or rule engineers to repeatedly rediscover the same change, PolicyGuard packages the old and new language, extracted codes and values, effective date, source locator, rule proposal or abstention reason, and fixture results into one evidence packet. After expert approval, the same proposal can be dry-run against synthetic or appropriately governed retrospective claims to estimate review volume, provider concentration, and configuration impact before deployment. This can improve the handoff among policy researchers, coders, clinical experts, analysts, and rule engineers while preserving an auditable record of how a written policy became executable review logic.

The opportunity is therefore not autonomous adjudication, but faster and more defensible policy operations. The principal threats remain wrong-version use, jurisdictional exceptions, stale code sets, unsupported interpretation, licensed-content constraints, PHI exposure, and overly broad rules that create false positives or provider abrasion. PolicyGuard addresses only part of this risk at POC scale through source provenance, deterministic execution, schema constraints, test fixtures, explicit abstention, human approval, and `automatic_claim_action = false`. A practical next step for Cotiviti would be a 90-day internal pilot on a small number of policy domains using expert-labeled changes and governed retrospective data. The pilot should measure source-provenance completeness, rule-template acceptance, appropriateness of abstention, reviewer time, queue size, and false-positive burden before any production integration. This approach aligns with Cotiviti's existing Payment Policy Management capabilities while adding a controlled evidence-to-rule validation layer rather than replacing expert judgment (Cotiviti, n.d.-a, n.d.-b; Autio et al., 2024).

---

## References

Autio, C., Schwartz, R., Dunietz, J., Jain, S., Stanley, M., Tabassi, E., Hall, P., & Roberts, K. (2024). *Artificial intelligence risk management framework: Generative artificial intelligence profile* (NIST AI 600-1). National Institute of Standards and Technology. https://doi.org/10.6028/NIST.AI.600-1

Centers for Medicare & Medicaid Services. (2024). *Medicare Physician Fee Schedule final rule summary: Calendar year 2025* (MLN Matters MM13887). https://www.cms.gov/files/document/mm13887-medicare-physician-fee-schedule-final-rule-summary-cy-2025.pdf

Centers for Medicare & Medicaid Services. (2025). *Medicare Physician Fee Schedule final rule summary: Calendar year 2026* (MLN Matters MM14315). https://www.cms.gov/files/document/mm14315-medicare-physician-fee-schedule-final-rule-summary-cy-2026.pdf

Centers for Medicare & Medicaid Services. (2026a). *Medicare National Correct Coding Initiative policy manual for Medicare services: Chapter XI - Medicine, evaluation and management services*. https://www.cms.gov/files/document/11-chapter11a-ncci-medicare-policy-manual-2026-final.pdf

Centers for Medicare & Medicaid Services. (2026b). *Therapy services: Calendar year 2026 updates*. https://www.cms.gov/medicare/coding-billing/therapy-services

Centers for Medicare & Medicaid Services. (2026c). *Billing and coding: Outpatient physical and occupational therapy services (A56566)*. https://www.cms.gov/medicare-coverage-database/view/article.aspx?articleid=56566

Cotiviti. (n.d.-a). *AI that drives value responsibly*. Retrieved August 9, 2026, from https://www.cotiviti.com/about/responsible-ai-use

Cotiviti. (n.d.-b). *Payment Policy Management*. Retrieved August 9, 2026, from https://www.cotiviti.com/solutions/payment-accuracy/payment-policy-management

Wang, H. (2026). *PolicyGuard Intelligence Studio* [Computer software]. GitHub. https://github.com/Rae9711/cotiviti-policyguard
