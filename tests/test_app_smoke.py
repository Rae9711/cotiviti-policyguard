"""Lightweight smoke checks that the Streamlit app module imports cleanly."""

from __future__ import annotations

import importlib


def test_app_module_imports():
    module = importlib.import_module("app")
    assert hasattr(module, "main")
    assert hasattr(module, "page_executive")
