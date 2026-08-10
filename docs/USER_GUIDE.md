# PolicyGuard user guide (evaluators)

**Live demo:** [https://cotiviti-policyguard-haorui-wang.streamlit.app/](https://cotiviti-policyguard-haorui-wang.streamlit.app/) (same `main` code as this repo). Or run locally with `streamlit run app.py` → [http://localhost:8501](http://localhost:8501) if the hosted free tier is asleep. GitHub remains the official submission for report, slides, video, and resume.

**Main thesis (do not miss this):**

> Policy change → source-grounded evidence → validated rule (or abstain) → synthetic claim review → human approval. **No automatic claim action.**

Core flow: **Compare → Evidence → Rule/Abstain → Impact → Human decision**

## Main function

PolicyGuard turns a public CMS policy version change into:

1. Source-grounded before/after evidence
2. A schema-validated review-rule **proposal** (or an explicit **abstention**)
3. A synthetic claim-impact preview (flagged for review only)
4. A human **Approve / Reject / Escalate** decision with an exportable audit

It never denies, reprices, adjudicates, or makes a clinical decision. Audit events hard-code `automatic_claim_action=false`.

## 60-second in-app path

| Order | Tab | What to look for |
|---|---|---|
| 1 | **01 · Executive overview** | Five policy patterns; one required abstention; charts are supporting context |
| 2 | **02 · Policy intelligence** | Before/after highlights + official source locators |
| 3 | **03 · Rule studio** | Validated JSON proposal **or** abstention — not auto-denial code |
| 4 | **04 · Claim impact** | Claims *flagged for review*; review-burden % vs naive all-claim screening; “paid amount in scope” ≠ savings/fraud |
| 5 | **05 · Governance** | Record Approve / Reject / Escalate; download audit JSONL |

## Recommended scenarios

1. **Therapy KX threshold increased** (`THERAPY-KX-THRESHOLD-2026`) — default evaluator path: clear currency change → validated rule → dry run.
2. Alternate: **Ventilation management code 94662 retired** (`NCCI-94662-RETIREMENT`).
3. Then: **Skilled-therapy versus general-fitness** (`THERAPY-SKILLED-VS-FITNESS`) — abstention is a **feature** (refusing to automate when claim fields are insufficient).

## In-app guidance

- Persistent **What this proves** banner under the hero
- Sidebar **Simple demo mode** (default on): highlights the recommended scenario and collapses secondary charts under “Optional detail”
- Sidebar **Show guide** + **Evaluator / Demo Guide** expander
- First-visit **Start here** coach mark
- Per-section **What is this?** expanders and chart purpose captions

Charts and matrices are **supporting evidence**, not the point. The point is the controlled workflow ending in a human gate.

## Related docs

- [`DEMO_SCRIPT.md`](DEMO_SCRIPT.md) — five-minute spoken route
- [`FUNCTION_REFERENCE.md`](FUNCTION_REFERENCE.md) — module/API map
- [`SOURCE_METHOD.md`](SOURCE_METHOD.md) — how sources were curated
