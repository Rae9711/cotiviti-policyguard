# PolicyGuard Video Script (≤5 minutes)

**Target length:** 4:30–5:00  
**Format:** MP4, candidate on camera + slides + live POC screenshare  
**Product one-liner:** PolicyGuard compares healthcare billing policy versions, grounds material changes in source evidence, proposes validated declarative rules, and tests approved rules on synthetic claims—with human approval required.

**Opening disclaimer (say once, clearly):**  
“PolicyGuard is a human-in-the-loop proof of concept. It does not make autonomous clinical, payment, or claim-denial decisions.”

---

## Timed outline

| Time | Visual | Spoken talking points |
| --- | --- | --- |
| **0:00–0:25** | Camera + title slide | Name, university/position applied for, Topic 3 Content Management. One-sentence product pitch + disclaimer. |
| **0:25–0:55** | Problem slide | Why payment-policy content changes matter for payment integrity; risk of missed updates vs unsupervised automation. |
| **0:55–1:25** | Approach / architecture | difflib → grounded change → Pydantic JSON rule → HITL → deterministic engine → audit log. Emphasize: **no API key**, **no executable LLM Python**. |
| **1:25–3:20** | **Live Streamlit POC** | Walk the app (see demo beats below). |
| **3:20–3:55** | Evaluation slide | Report actual metrics from `evaluation/results.md` (precision/recall, abstention, rule-test). State honestly: small demo gold set. |
| **3:55–4:30** | Governance + recommendation | Abstention as a feature; Cotiviti-aligned suggestion: policy→validated rule→expert accountability. |
| **4:30–5:00** | Closing slide | Restate disclaimer; thank viewer; point to GitHub deliverables map in README. |

---

## Live demo beats (≈2 minutes)

1. **Select** 2025→2026 demo pair; show side-by-side policies.  
2. **Diff:** point out additions/deletions (EXAMPLE1 date language; ambiguous integral section).  
3. **Grounded change:** document, section, effective date `2026-01-01`, evidence passage.  
4. **Proposed rule:** show JSON; say “validated schema, flag_for_review only.”  
5. **Approve** → claim impact: “potentially affected / flagged for review”; show count; say “no automated denial.”  
6. **Ambiguous change:** show abstain reason → click **Request Expert Interpretation**.  
7. **Audit trail:** briefly show JSONL events.

---

## Phrases to use / avoid

**Use:** potentially affected, flagged for review, requires expert validation, insufficient evidence, no automated action taken.  
**Avoid:** fraud detected, claim denied, abusive provider, automatic rejection.

---

## Recording tips

- Speak slightly slower than conversational pace; leave 2–3 seconds of silence before stopping the recording so the ending is clean.  
- Keep browser zoom ~110% so evidence text is readable on camera.  
- If a rerun clears a button state, narrate “session decision recorded” from the info banner.
