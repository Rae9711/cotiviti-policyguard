# Five-minute demonstration script

**Live demo:** [https://cotiviti-policyguard-haorui-wang.streamlit.app/](https://cotiviti-policyguard-haorui-wang.streamlit.app/) (same `main` code). Local backup: `streamlit run app.py` → [http://localhost:8501](http://localhost:8501). Report, slides, video, and resume stay in this GitHub repo.

Evaluator-facing walkthrough (tabs, what to look for, careful language): [`USER_GUIDE.md`](USER_GUIDE.md).

The assessment video must remain under five minutes. This route shows breadth without clicking through every chart.

**Thesis to state early:** Policy change → source-grounded evidence → validated rule (or abstain) → synthetic claim review → human approval. No automatic claim action.

## 0:00–0:35 — Problem and thesis

“Healthcare policy changes are not valuable until they are detected, traced to evidence, translated consistently, tested, and reviewed. PolicyGuard demonstrates that workflow using public CMS sources and synthetic claims. It does not deny or reprice claims.”

## 0:35–1:10 — Executive overview

- Point out 9 official sources, 5 curated changes, 4 executable proposals, and 1 abstention.
- Explain the policy opportunity matrix.
- State that the 604-row dataset is deterministic and contains no PHI.

## 1:10–2:05 — Policy intelligence

- Select **Therapy KX threshold increased**.
- Show before/after values, highlighted text, extracted currency/date deltas, and official source cards.
- Mention that uploaded TXT/PDF versions can be compared locally.

## 2:05–2:55 — Rule studio

- Show the four validated conditions.
- Open the JSON proposal.
- Emphasize that the engine interprets JSON and never executes generated code.
- Show the dry-run count and sample affected claims.

## 2:55–3:55 — Claim impact

- Show the five impact KPIs.
- Use the time trend, provider bubble chart, and prioritized reviewer queue.
- Explain that “paid amount in scope” is neither an overpayment nor a savings estimate.

## 3:55–4:35 — Abstention and governance

- Select **Skilled-therapy versus general-fitness interpretation**.
- Show that Rule Studio refuses to create a rule.
- Explain why clinical purpose requires documentation context and expert judgment.
- Record an escalation in the Governance tab.

## 4:35–4:55 — Close

“PolicyGuard’s value is not autonomous decision-making. It is faster, more traceable preparation for expert decisions. The next step would be a controlled retrospective pilot with licensed policy content, credentialed reviewers, and production monitoring.”
