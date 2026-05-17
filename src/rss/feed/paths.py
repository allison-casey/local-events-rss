"""Filesystem paths for JSON stores and generated RSS feeds."""

from __future__ import annotations

from pathlib import Path
from typing import Final

DATA_DIR: Final[Path] = Path("data")
FEEDS_DIR: Final[Path] = Path("feeds")
ALL_FEED_PATH: Final[Path] = FEEDS_DIR / "all.xml"


def store_feed_path(module: str, store_path: Path) -> Path:
    """Map a JSON store path to its RSS output path under ``feeds/``."""
    stem = store_path.stem
    if stem.endswith("_events"):
        stem = stem[: -len("_events")]
    return FEEDS_DIR / module / f"{stem}.xml"
