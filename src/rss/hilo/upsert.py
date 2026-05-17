"""Load, merge, and persist scraped Hi-Lo events."""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Final

from rss.hilo.types import HiloEvent

DEFAULT_CULVER_CITY_STORE_PATH: Final[Path] = Path("data/hilo/culver_city_events.json")


def upsert_events(
    existing: Iterable[HiloEvent],
    incoming: Iterable[HiloEvent],
) -> list[HiloEvent]:
    """Merge events by ``event_id``, preferring newer incoming records."""
    merged: dict[str, HiloEvent] = {event.event_id: event for event in existing}
    for event in incoming:
        merged[event.event_id] = event
    return sorted(merged.values(), key=lambda event: event.start_at)


def load_events(path: Path) -> list[HiloEvent]:
    """Load events from a JSON file, returning an empty list if missing."""
    if not path.exists():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError(f"Expected a JSON array in {path}")
    return [HiloEvent.model_validate(item) for item in payload]


def save_events(path: Path, events: Iterable[HiloEvent]) -> None:
    """Persist events to a JSON file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    serialized = [event.model_dump(mode="json") for event in events]
    path.write_text(
        json.dumps(serialized, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def sync_events(
    incoming: Iterable[HiloEvent],
    *,
    store_path: Path,
) -> tuple[list[HiloEvent], Mapping[str, int]]:
    """Upsert incoming events into the store file and return counts."""
    existing = load_events(store_path)
    merged = upsert_events(existing, incoming)
    save_events(store_path, merged)
    incoming_ids = {event.event_id for event in incoming}
    existing_ids = {event.event_id for event in existing}
    added = len(incoming_ids - existing_ids)
    updated = len(incoming_ids & existing_ids)
    return merged, {"added": added, "updated": updated, "total": len(merged)}
