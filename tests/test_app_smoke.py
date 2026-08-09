"""Lightweight smoke checks that the Streamlit app module imports cleanly."""

from __future__ import annotations

import importlib

from streamlit.testing.v1 import AppTest


def test_app_module_imports():
    module = importlib.import_module("app")
    assert hasattr(module, "main")
    assert hasattr(module, "page_executive")


def test_guide_dismiss_does_not_mutate_widget_key_inline():
    """Dismiss must use on_click so show_guide is set before the toggle exists.

    Assigning st.session_state.show_guide after a widget with key='show_guide'
    raises StreamlitAPIException; the on_click callback pattern is the fix.
    """
    script = """
import streamlit as st

if "show_guide" not in st.session_state:
    st.session_state.show_guide = True
if "guide_seen" not in st.session_state:
    st.session_state.guide_seen = False

def _dismiss_guide():
    st.session_state.guide_seen = True
    st.session_state.show_guide = False

st.toggle("Show guide", key="show_guide")
if st.session_state.show_guide:
    st.button("Got it", key="guide_dismiss_btn", on_click=_dismiss_guide)
"""
    at = AppTest.from_string(script, default_timeout=10)
    at.run()
    assert not at.exception

    dismiss = [b for b in at.button if b.key == "guide_dismiss_btn"]
    assert dismiss
    dismiss[0].click().run()
    assert not at.exception
    assert at.session_state["guide_seen"] is True
    assert at.session_state["show_guide"] is False


def test_main_path_loads_without_exception():
    """Quick load of main() must not raise (including StreamlitAPIException)."""
    at = AppTest.from_file("app.py", default_timeout=30)
    at.run()
    assert not at.exception
