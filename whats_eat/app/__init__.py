"""Application entrypoints for the What's Eat backend."""

from __future__ import annotations

from typing import Any

__all__ = ["build_app"]


def build_app(*args: Any, **kwargs: Any):
    """Lazily import and build the LangGraph application."""

    from .supervisor_app import build_app as _build_app

    return _build_app(*args, **kwargs)

