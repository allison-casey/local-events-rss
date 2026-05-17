"""Register built-in feed module loaders."""

from __future__ import annotations

from rss.feed.registry import register_module
from rss.hilo.stores import load_channel_from_store


def register_builtin_modules() -> None:
    register_module("hilo", load_channel_from_store)
