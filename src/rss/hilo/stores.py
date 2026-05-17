"""Hi-Lo JSON store paths and loading."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from rss.feed.paths import DATA_DIR
from rss.hilo.types import HiloChannel, HiloEvent, HiloLocation

HILO_DATA_DIR = DATA_DIR / "hilo"


def location_from_store_path(path: Path) -> HiloLocation:
    """Infer a Hi-Lo location from a store filename such as ``costa_mesa_events.json``."""
    stem = path.stem
    if stem.endswith("_events"):
        stem = stem[: -len("_events")]
    try:
        return HiloLocation[stem.upper()]
    except KeyError as exc:
        raise ValueError(f"Could not infer Hi-Lo location from store path: {path}") from exc


def default_store_path(location: HiloLocation) -> Path:
    """Default JSON store path for a Hi-Lo location."""
    return HILO_DATA_DIR / f"{location.name.lower()}_events.json"


def load_channel_from_store(path: Path) -> HiloChannel:
    """Load a Hi-Lo channel from a JSON store file."""
    if not path.exists():
        location = location_from_store_path(path)
        return HiloChannel.for_location(location, [])
    payload = json.loads(path.read_text(encoding="utf-8"))
    location = location_from_store_path(path)
    channel = _parse_channel_payload(payload, location)
    if channel.location is not location:
        raise ValueError(
            f"Store {path} is for {channel.location.value}, not {location.value}"
        )
    return channel


def _parse_channel_payload(payload: Any, location: HiloLocation) -> HiloChannel:
    if isinstance(payload, list):
        events = [HiloEvent.model_validate(item) for item in payload]
        return HiloChannel.for_location(location, events)
    if isinstance(payload, dict):
        return HiloChannel.model_validate(payload)
    raise ValueError("Expected a JSON object (channel) or array (legacy events)")
