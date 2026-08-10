# PolicyGuard assessment video script

**Candidate:** Haorui Wang  
**Product:** PolicyGuard  
**Assessment:** Cotiviti Generative AI Research Intern — Topic 3, Content Management in Health Care  
**Deck:** [`slides/Haorui_Wang_PolicyGuard_Cotiviti_Assessment.pptx`](../slides/Haorui_Wang_PolicyGuard_Cotiviti_Assessment.pptx)  
**Target spoken length:** 4:30–4:50 (hard cap 5:00 MP4)  
**Format:** candidate on camera + slide walkthrough. Optional live Streamlit overlay on slides 5–6 (same spoken lines).  
**Upload:** MP4 in this public repo (`video/Haorui_Wang_PolicyGuard_Demo.mp4`). Do not use YouTube or Drive.

This is an **8-slide walkthrough**. The deck is slide-only; slide 5 already contains a Governance screenshot. Cotiviti also asks for a working-POC screenshare — treat the live app as a **visual swap**, not extra spoken content.

---

## Recording setup

1. Open the PPTX in slideshow (widescreen 16:9).
2. In another window, start the app before recording:

   ```bash
   source .venv/bin/activate
   streamlit run app.py
   ```

   Leave **Simple demo mode** on. Park on **05 · Governance**.
3. Camera: face + upper torso, picture-in-picture. Look at the **camera** for greetings, thesis, disclaimer, and close. Look at the **slide/app** when pointing at numbers or the screenshot.
4. Speak slightly slower than conversation (~145 words/min). Leave 2 seconds of silence at the end before stopping.
5. Export MP4 ≤ 5:00 into `video/Haorui_Wang_PolicyGuard_Demo.mp4`.

**Phrases to use:** flagged for review, paid amount in scope, human review queue, illustrative assumption, required abstention, `automatic_claim_action = false`.  
**Phrases to avoid:** fraud, denial, overpayment, recovery, savings, abusive provider — except to say the demo is **not** those things. Voice the time math as an **assumption**, exactly as the slide labels it.  
**Do not claim** GPT, an LLM, or an API key was used in the demo.

---

## Extracted slide outline

Extracted from the final PPTX (python-pptx + slide-1 raster title). Speaker notes are coaching only — speak the timed script below.

### Slide 1 — Title (image)

- **PolicyGuard**
- Faster, source-grounded policy-to-review
- Flow icons: **source → policy → evidence → rule → review**
- Cotiviti Intern Assessment · Topic 3 · Haorui Wang

### Slide 2 — PROBLEM · Interpret the change once — not claim by claim

- Payers must turn yearly billing and coding policy updates into consistent review logic.
- **Today: fragmented workflow**
  - Slow: reviewers re-read policy while handling individual claims.
  - Manual: change detection, evidence capture, and rule handoff are fragmented.
  - Risky: a missed change causes inconsistent reviews; an unsupported rule creates provider abrasion.
  - Hard to defend: the source trail can get separated from the review decision.
- **Purpose of the POC: centralized change-unit**
  - Grounded: recover five specified CY 2025–2026 changes from public CMS-source evidence.
  - Decidable only: convert changes into schema-validated rules only when claim fields contain the needed facts.
  - Dry-run impact: apply approved rules to 604 synthetic claims and route candidates to human review.
  - Abstain: stop when clinical judgment is required instead of manufacturing a claim rule.
  - No denial without evidence · `automatic_claim_action = false`
- Cost of the status quo: reviewers re-read policy per claim, not once per change.

### Slide 3 — PROBLEM · Grounded in CMS sources, not fictional policy

- The demo uses public first-party sources, concise paraphrases, and synthetic claims.

| Source | What changed | How PolicyGuard used it |
| --- | --- | --- |
| CMS Medicare NCCI Policy Manual · CY 2025 vs CY 2026 | CPT 94662 deleted effective Jan 1, 2026 | Code-retirement rule → coding-configuration review |
| CMS MPFS CR MM14315 · CY 2026 | Therapy KX threshold $2,410 → $2,480; Q3014 facility fee $31.01 → $31.85 | Numeric threshold + fee-tolerance rules |
| CMS Transmittal R13431CP · 2026 Therapy Code List | New RTM codes 98979, 98984, 98985 (sometimes-therapy) | Mapping / configuration check |
| CMS-style skilled therapy narrative (abstention case) | Clinical purpose cannot be inferred from claim fields alone | No rule generated; expert interpretation required |

- Repository stores metadata + short paraphrases, not full manuals or licensed CPT text. Claims: 604 synthetic rows, no PHI.
- Footer: CMS-style narrative is an abstention scenario, not a CMS data source.

### Slide 4 — METHOD · Interpret once, then route evidence

- PolicyOps flow: old/new policy text becomes one evidence packet and one human gate.
- Pipeline: **Compare versions → Extract evidence → Rule or abstain → Dry-run impact → Human decision**
- **Deterministic core:** TF-IDF unigram/bigram similarity + lexical sequence matching; regex extraction for codes, dates, dollar values, modifiers, and percentages.
- **Safety constraints:** Pydantic schema validation + allowlisted operators; no generated Python or SQL execution; only action: `flag_for_review`.
- Thesis: compare official versions → attach evidence → validated review rule or abstain → synthetic claim review → approve / reject / escalate.
- Footer: fully offline deterministic core; no API key required.

### Slide 5 — METHOD · Governance: Only decidable changes become rules

- Ambiguous clinical purpose is a stop sign, not a prompt to invent logic.
- Executable when claim fields contain all required facts → Declarative JSON + validated operators → Deterministic dry run on synthetic claims → Human approve / reject / escalate, audit logged.
- Screenshot caption: **Governance screen: abstention + expert interpretation path** (repository demo asset).
- Screenshot shows control themes + **Record a human decision** (Approve for controlled testing / Reject / Escalate).

### Slide 6 — RESULTS · The queue gets smaller and clearer

- Synthetic pack: 604 claims, four executable rules, one documented abstention.
- **5 gates vs 604 reads** — ≈99.2% fewer policy-interpretation decisions under this accounting assumption.
- **55 / 604 flagged** — 9.1% entered a human review queue. The rest were not auto-paid or denied.
- **$5,627.13 in scope** — paid amount on flagged synthetic rows — not overpayment, recovery, fraud, or savings.
- Flag concentration by change: KX 22 · 94662 18 · Q3014 10 · RTM 5.
- Illustrative time scenario — not a measured labor study:
  - Manual: 604 × 2 min ≈ 20.1 hours
  - PolicyGuard path: 5 × 10 min + 55 × 2 min ≈ 2.7 hours
  - ≈ 17 hours less effort **only under these assumptions**
- Footer: synthetic claims only; not precision, recall, FTE, dollar savings, or production recovery.

### Slide 7 — CONCLUSION · Pilot as a validation layer, not adjudication

- Best fit: upstream of payment-policy execution, next to expert review.
- Use for clear numeric and code-list edits · Keep humans on ambiguous clinical language · Never convert flags into automatic denials.
- **Recommended 90-day internal pilot**
  - Inputs: expert-labeled policy changes + governed retrospective data
  - Measures: source provenance, rule acceptance, abstention quality, queue size, false-positive burden, reviewer time
  - Success test: faster evidence-to-rule handoff without losing traceability or expert accountability
- Close: save reviewer time by interpreting policy once — not 604 times — with a source trail.

### Slide 8 — Close

- Thank you so much for your time!
- PolicyGuard · Haorui Wang

---

## Timed spoken script

Read this column aloud. Visual cues are stage directions — do not speak the bracket tags.

### 0:00–0:20 · Slide 1 · [CAMERA]

Hi, I’m Haorui Wang. This is PolicyGuard — Cotiviti intern assessment, Topic 3, Content Management in Health Care.

Faster, source-grounded policy-to-review: source, policy, evidence, rule, then review.

It is a human-in-the-loop proof of concept. It flags claims for review. It does not deny, reprice, or adjudicate.

### 0:20–1:00 · Slide 2 · [SLIDE] look at camera on the purpose column

The problem: interpret the change once — not claim by claim.

Payers must turn yearly billing and coding updates into consistent review logic. Today reviewers re-read policy claim by claim; evidence and rules fragment; missed or unsupported changes create inconsistency and abrasion.

This POC treats the change as the unit of work. Recover five specified CY 2025–2026 CMS-source changes. Emit schema-validated rules only when claim fields hold the needed facts. Dry-run them on 604 synthetic claims for human review. Abstain when clinical judgment is required.

No denial without evidence — automatic_claim_action is false.

### 1:00–1:48 · Slide 3 · [SLIDE] point down the table

Grounded in CMS sources, not fictional policy — public first-party sources, short paraphrases, synthetic claims.

NCCI Policy Manual, CY 2025 versus 2026: CPT 94662 deleted January 1, 2026 — a code-retirement rule for coding-configuration review.

MPFS CR MM14315: KX threshold 2,410 to 2,480 dollars; Q3014 facility fee 31.01 to 31.85 — numeric-threshold and fee-tolerance rules.

Transmittal R13431CP Therapy Code List: RTM codes 98979, 98984, 98985 — mapping and configuration check.

Last row is a CMS-style skilled-therapy narrative: the abstention case, not a CMS download. Clinical purpose is not in claim fields, so no rule. Expert interpretation required.

The repo stores metadata and paraphrases, not full manuals or licensed CPT. 604 synthetic claims, no PHI.

### 1:48–2:22 · Slide 4 · [SLIDE] walk left to right

Method: interpret once, then route evidence. Old and new text become one evidence packet and one human gate.

Compare versions, extract evidence, rule or abstain, dry-run impact, human decision.

Deterministic core: TF-IDF plus lexical matching, and regex for codes, dates, dollars, modifiers.

Safety: Pydantic schema, allowlisted operators, no generated Python or SQL. Only action: flag_for_review. No LLM in this demo. Offline. No API key.

Thesis: official versions, attach evidence, validated rule or abstain, synthetic review, then approve, reject, or escalate.

### 2:22–2:52 · Slide 5 · [SLIDE] screenshot — or [APP] tab **05 · Governance**

Governance: only decidable changes become rules. Ambiguous clinical purpose is a stop sign, not a prompt to invent logic.

Four administrative changes are executable — declarative JSON, dry run, then human approve, reject, or escalate, audit logged.

The fifth — skilled therapy versus fitness — abstains. That is not a failure; it avoids unsupported rules.

*[If sharing the live app: switch to Streamlit **05 · Governance**. Point to control themes and Record a human decision — Approve, Reject, or Escalate. Do not fill the form unless ahead of time. Return to the deck.]*

No proposal becomes operational without a reviewer.

### 2:52–3:52 · Slide 6 · [SLIDE] — optional [APP] tab **04 · Claim impact**

Results: 604 synthetic claims, four executable rules, one abstention.

Five gates versus 604 reads — about 99.2 percent fewer interpretation decisions under that accounting assumption.

55 of 604 flagged for review — 9.1 percent entered a human queue. The rest were not auto-paid or denied.

Paid amount in scope is 5,627.13 dollars on those synthetic rows — not overpayment, recovery, fraud, or savings.

Four bars: KX 22, 94662 18, Q3014 10, RTM 5. The fifth change abstains — no bar, no claim rule.

The time math is illustrative, not a labor study. Manual: 604 times 2 minutes, about 20.1 hours. PolicyGuard path: five 10-minute gates plus 55 two-minute reviews, about 2.7 hours — roughly 17 hours less only under these assumptions. Not FTE savings or financial recovery.

### 3:52–4:22 · Slide 7 · [CAMERA]

Pilot as a validation layer, not adjudication. Best fit: upstream of payment-policy execution, next to expert review.

Use for clear numeric and code-list edits. Keep humans on ambiguous clinical language. Never convert flags into automatic denials.

90-day pilot inputs: expert-labeled changes and governed retrospective data. Measures: provenance, rule acceptance, abstention quality, queue size, false-positive burden, reviewer time. Success: faster evidence-to-rule handoff without losing traceability or accountability.

Interpret policy once — not 604 times — with a source trail.

### 4:22–4:42 · Slide 8 · [CAMERA]

Thank you so much for your time. I’m Haorui Wang, and this is PolicyGuard.

The working proof of concept is in the public repository: github.com/Rae9711/cotiviti-policyguard. Clone it, install requirements, then run `streamlit run app.py`. No API key.

---

## Timing check

| Block | Visual | Words | Target |
| --- | --- | ---: | --- |
| 1 Title | Camera | ~55 | 0:20 |
| 2 Problem | Slide | ~100 | 0:40 |
| 3 Sources | Slide | ~120 | 0:48 |
| 4 Method | Slide | ~85 | 0:34 |
| 5 Governance | Slide or App 05 | ~60 | 0:30 |
| 6 Results | Slide or App 04 | ~125 | 1:00 |
| 7 Conclusion | Camera | ~85 | 0:30 |
| 8 Thank you + repo | Camera | ~40 | 0:20 |
| **Spoken total** | | **~670 → ~4:35 at 145 wpm; ~4:20 at 155 wpm** | **4:30–4:50** |

If rehearsal exceeds 4:50, drop slide 3’s RTM code list (keep “mapping check”) then slide 7’s measures list (keep Success). Do not cut the disclaimer, paid-in-scope line, time-assumption caveat, or repo close.

After recording, commit `video/Haorui_Wang_PolicyGuard_Demo.mp4` and keep this script in the repo.
