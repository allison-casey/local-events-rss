"""Load, merge, and persist scraped Hi-Lo channels."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from pathlib import Path

from rss.hilo.stores import load_channel_from_store
from rss.hilo.types import HiloChannel, HiloEvent, HiloLocation


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
    """Load a Hi-Lo channel, validating that it matches ``location``."""
    channel = load_channel_from_store(path)
    if channel.location is not location:
        raise ValueError(
            f"Store {path} is for {channel.location.value}, not {location.value}"
        )
    return channel


def save_channel(path: Path, channel: HiloChannel) -> None:
    """Persist a Hi-Lo channel to a JSON file."""
    import json

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
