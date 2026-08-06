"""Load and query the curated CMS policy intelligence catalog.

Role in PolicyGuard
-------------------
Central access point for official-source metadata and the five curated
policy-change patterns. The Streamlit app and evaluation scripts resolve
evidence, rule proposals, and abstention reasons through this module.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Optional

from src.models import PolicyCatalog, PolicyChange, PolicyRule, PolicySource

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CATALOG = ROOT / "data" / "policies" / "policy_catalog.json"


@lru_cache(maxsize=1)
def load_catalog(path: str | Path | None = None) -> PolicyCatalog:
    """Parse and validate ``policy_catalog.json``.

    Parameters
    ----------
    path:
        Optional override path. Defaults to the committed catalog.

    Returns
    -------
    PolicyCatalog
        Fully validated workspace, sources, and changes.
    """
    catalog_path = Path(path) if path else DEFAULT_CATALOG
    raw = json.loads(catalog_path.read_text(encoding="utf-8"))
    return PolicyCatalog.model_validate(raw)


def list_changes(catalog: PolicyCatalog | None = None) -> list[PolicyChange]:
    """Return all curated change records."""
    cat = catalog or load_catalog()
    return list(cat.changes)


def get_change(change_id: str, catalog: PolicyCatalog | None = None) -> PolicyChange:
    """Look up a change by id.

    Raises
    ------
    KeyError
        If ``change_id`` is not in the catalog.
    """
    cat = catalog or load_catalog()
    for change in cat.changes:
        if change.change_id == change_id:
            return change
    raise KeyError(f"Unknown change_id: {change_id}")


def get_sources_for_change(
    change: PolicyChange,
    catalog: PolicyCatalog | None = None,
) -> list[PolicySource]:
    """Resolve official source cards for a curated change."""
    cat = catalog or load_catalog()
    by_id = {s.source_id: s for s in cat.sources}
    return [by_id[sid] for sid in change.source_ids if sid in by_id]


def executable_rules(catalog: PolicyCatalog | None = None) -> list[tuple[PolicyChange, PolicyRule]]:
    """Return ``(change, rule)`` pairs that are eligible for dry-run simulation."""
    cat = catalog or load_catalog()
    pairs: list[tuple[PolicyChange, PolicyRule]] = []
    for change in cat.changes:
        if change.rule_template is not None:
            pairs.append((change, change.rule_template))
    return pairs


def abstention_changes(catalog: PolicyCatalog | None = None) -> list[PolicyChange]:
    """Return changes that deliberately refuse claim-level automation."""
    cat = catalog or load_catalog()
    return [c for c in cat.changes if c.abstains]


def clear_catalog_cache() -> None:
    """Invalidate the cached catalog (used by tests)."""
    load_catalog.cache_clear()
