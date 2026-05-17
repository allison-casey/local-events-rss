"""Registry mapping data modules to channel loaders."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from rss.feed.types import RssChannel

ChannelLoader = Callable[[Path], RssChannel]

_LOADERS: dict[str, ChannelLoader] = {}


def register_module(name: str, loader: ChannelLoader) -> None:
    """Register a loader that parses one JSON store into an ``RssChannel``."""
    _LOADERS[name] = loader


def load_channel(module: str, store_path: Path) -> RssChannel:
    """Load a channel JSON store for a registered module."""
    try:
        loader = _LOADERS[module]
    except KeyError as exc:
        raise ValueError(f"Unknown feed module: {module}") from exc
    return loader(store_path)


def registered_modules() -> tuple[str, ...]:
    """Return registered module names in sorted order."""
    return tuple(sorted(_LOADERS))
