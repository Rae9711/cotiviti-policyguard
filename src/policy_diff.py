"""Policy version comparison using difflib (no LLM required).

Role in PolicyGuard
-------------------
This module is the first stage of the pipeline: given two policy text
versions, it produces line-level additions and deletions that later stages
ground into source-backed change objects and (optionally) declarative rules.

Design choices
--------------
* Uses ``difflib.ndiff`` only — deterministic, offline, and auditable.
* Does not interpret clinical or payment meaning; interpretation belongs
  to the change analyzer / human reviewer.
* Never mutates input text; never executes or generates code.

Governance
----------
Diff output alone is never used to deny claims or take automated payment
action. Reviewers must approve any proposed rule before claim impact
analysis runs.
"""

from __future__ import annotations

from difflib import ndiff
from typing import TypedDict


class PolicyDiffResult(TypedDict):
    """Structured line-level diff between two policy texts.

    Attributes
    ----------
    additions:
        Lines present in the new version but not the old (``ndiff`` ``+ ``).
    deletions:
        Lines present in the old version but not the new (``ndiff`` ``- ``).
    """

    additions: list[str]
    deletions: list[str]


def compare_policy_versions(old_text: str, new_text: str) -> PolicyDiffResult:
    """Return line-level additions and deletions between two policy texts.

    Splits each document on newlines and runs ``difflib.ndiff``. Lines
    beginning with ``+ `` are treated as additions; lines beginning with
    ``- `` are deletions. Unchanged lines (``  ``) and hint lines (``? ``)
    are ignored.

    Parameters
    ----------
    old_text:
        Full text of the prior policy version (e.g. 2025 demo excerpt).
    new_text:
        Full text of the newer policy version (e.g. 2026 demo excerpt).

    Returns
    -------
    PolicyDiffResult
        Dictionary with ``additions`` and ``deletions`` lists of stripped
        line content (the ``+ `` / ``- `` markers themselves are removed).

    Edge cases
    ----------
    * Identical inputs yield empty lists.
    * Empty strings are valid; comparing empty→non-empty yields only additions.
    * Trailing newlines do not create phantom empty-line diffs beyond what
      ``splitlines()`` already omits.

    Safety
    ------
    This function performs no claim scoring and no rule generation.
    """
    old_lines = old_text.splitlines()
    new_lines = new_text.splitlines()

    additions: list[str] = []
    deletions: list[str] = []

    for line in ndiff(old_lines, new_lines):
        if line.startswith("+ "):
            additions.append(line[2:])
        elif line.startswith("- "):
            deletions.append(line[2:])

    return {"additions": additions, "deletions": deletions}


def format_diff_summary(diff: PolicyDiffResult) -> str:
    """Return a short human-readable count summary of a diff result.

    Parameters
    ----------
    diff:
        Output of :func:`compare_policy_versions`.

    Returns
    -------
    str
        e.g. ``"3 addition line(s) · 2 deletion line(s)"``.
    """
    return (
        f"{len(diff['additions'])} addition line(s) · "
        f"{len(diff['deletions'])} deletion line(s)"
    )
