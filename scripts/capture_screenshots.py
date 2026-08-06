#!/usr/bin/env python3
"""Capture Streamlit POC screenshots into screenshots/ for the assessment package."""

from __future__ import annotations

from pathlib import Path

from playwright.sync_api import sync_playwright

OUT = Path(__file__).resolve().parent.parent / "screenshots"
URL = "http://localhost:8502"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.goto(URL, wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(2500)

        page.screenshot(
            path=str(OUT / "01_overview_disclaimer_diff.png"), full_page=True
        )

        # Scroll toward grounded changes / reviewer controls
        page.evaluate("window.scrollTo(0, document.body.scrollHeight * 0.45)")
        page.wait_for_timeout(800)
        page.screenshot(path=str(OUT / "02_grounded_changes.png"), full_page=False)

        # Click Approve on EXAMPLE1 if present
        approve = page.get_by_role("button", name="Approve").first
        if approve.count() > 0:
            approve.click()
            page.wait_for_timeout(2500)
            page.screenshot(
                path=str(OUT / "03_approved_claim_impact.png"), full_page=True
            )

        # Expert interpretation on ambiguous change (second expert button if any)
        expert_buttons = page.get_by_role("button", name="Request Expert Interpretation")
        if expert_buttons.count() > 1:
            expert_buttons.nth(1).click()
            page.wait_for_timeout(1500)
        elif expert_buttons.count() == 1:
            expert_buttons.first.click()
            page.wait_for_timeout(1500)

        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(800)
        page.screenshot(path=str(OUT / "04_audit_trail.png"), full_page=False)

        browser.close()

    readme = OUT / "README.md"
    readme.write_text(
        "# Screenshots\n\n"
        "Captured from the local Streamlit POC (`streamlit run app.py`).\n\n"
        "| File | Contents |\n| --- | --- |\n"
        "| `01_overview_disclaimer_diff.png` | Disclaimer, policy pair, line-level diff |\n"
        "| `02_grounded_changes.png` | Source-grounded change cards / evidence |\n"
        "| `03_approved_claim_impact.png` | After Approve: claim impact (careful language) |\n"
        "| `04_audit_trail.png` | Audit JSONL / lower page |\n",
        encoding="utf-8",
    )
    print(f"Wrote screenshots to {OUT}")


if __name__ == "__main__":
    main()
