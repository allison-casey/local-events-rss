"""Load, merge, and persist scraped Hi-Lo channels."""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any, Final

from rss.hilo.types import HiloChannel, HiloEvent, HiloLocation

DEFAULT_CULVER_CITY_STORE_PATH: Final[Path] = Path("data/hilo/culver_city_events.json")


def default_store_path(location: HiloLocation) -> Path:
    """Default JSON store path for a Hi-Lo location."""
    return Path(f"data/hilo/{location.name.lower()}_events.json")


def upsert_events(
    existing: Iterable[HiloEvent],
    incoming: Iterable[HiloEvent],
) -> list[HiloEvent]:
    """Merge events by ``event_id``, preferring newer incoming records."""
    merged: dict[str, HiloEvent] = {event.event_id: event for event in existing}
    for event in incoming:
        merged[event.event_id] = event
    return sorted(merged.values(), key=lambda event: event.start_at)


def load_channel(path: Path, location: HiloLocation) -> HiloChannel:
    """Load a Hi-Lo channel from a JSON file, returning an empty channel if missing."""
    if not path.exists():
        return HiloChannel.for_location(location, [])
    payload = json.loads(path.read_text(encoding="utf-8"))
    channel = _parse_channel_payload(payload, location)
    if channel.location is not location:
        raise ValueError(
            f"Store {path} is for {channel.location.value}, not {location.value}"
        )
    return channel


def save_channel(path: Path, channel: HiloChannel) -> None:
    """Persist a Hi-Lo channel to a JSON file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(channel.model_dump(mode="json"), indent=2, ensure_ascii=False)
        + "\n",
        encoding="utf-8",
    )


def sync_channel(
    channel: HiloChannel,
    incoming: Iterable[HiloEvent],
    *,
    store_path: Path,
) -> tuple[HiloChannel, Mapping[str, int]]:
    """Upsert incoming events into the store file and return the merged channel."""
    existing = load_channel(store_path, channel.location)
    merged_events = upsert_events(existing.events, incoming)
    merged_channel = existing.model_copy(update={"events": merged_events})
    save_channel(store_path, merged_channel)
    incoming_ids = {event.event_id for event in incoming}
    existing_ids = {event.event_id for event in existing.events}
    added = len(incoming_ids - existing_ids)
    updated = len(incoming_ids & existing_ids)
    return merged_channel, {
        "added": added,
        "updated": updated,
        "total": len(merged_channel.events),
    }


def _parse_channel_payload(payload: Any, location: HiloLocation) -> HiloChannel:
    if isinstance(payload, list):
        events = [HiloEvent.model_validate(item) for item in payload]
        return HiloChannel.for_location(location, events)
    if isinstance(payload, dict):
        return HiloChannel.model_validate(payload)
    raise ValueError("Expected a JSON object (channel) or array (legacy events)")
