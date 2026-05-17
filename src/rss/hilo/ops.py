"""Hi-Lo scrape, sync, and list operations."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

import typer

from rss.hilo.scraping import scrape_location_channel, scrape_location_channels
from rss.hilo.stores import default_store_path, load_channel_from_store
from rss.hilo.types import ALL_HILO_LOCATIONS, HiloChannel, HiloLocation
from rss.hilo.upsert import save_channel, sync_channel


def resolve_locations(locations: list[HiloLocation] | None) -> list[HiloLocation]:
    return locations or list(ALL_HILO_LOCATIONS)


def scrape(
    *,
    locations: list[HiloLocation] | None = None,
    output: Path | None = None,
) -> None:
    """Scrape Hi-Lo locations and optionally write one channel to JSON."""
    targets = resolve_locations(locations)
    if output is not None and len(targets) != 1:
        raise typer.BadParameter("--output requires exactly one --location")

    if len(targets) == 1:
        channel = scrape_location_channel(targets[0])
        typer.echo(f"Scraped {len(channel.events)} event(s) for {targets[0].value}.")
        if output is not None:
            save_channel(output, channel)
            typer.echo(f"Wrote {output}.")
        return

    for channel in scrape_location_channels(targets):
        typer.echo(f"Scraped {len(channel.events)} event(s) for {channel.location.value}.")


def sync(
    *,
    locations: list[HiloLocation] | None = None,
    store_path: Path | None = None,
) -> None:
    """Scrape and upsert Hi-Lo channels into JSON stores."""
    targets = resolve_locations(locations)
    if store_path is not None and len(targets) != 1:
        raise typer.BadParameter("--store requires exactly one --location")

    if len(targets) == 1:
        _sync_location(targets[0], store_path=store_path)
        return

    for scraped in scrape_location_channels(targets):
        _sync_location(scraped.location, scraped=scraped)


def list_events(
    *,
    locations: list[HiloLocation] | None = None,
    store_path: Path | None = None,
    limit: int = 20,
) -> None:
    """Print stored Hi-Lo events."""
    targets = resolve_locations(locations)
    if store_path is not None and len(targets) != 1:
        raise typer.BadParameter("--store requires exactly one --location")

    for location in targets:
        path = store_path or default_store_path(location)
        channel = load_channel_from_store(path)
        typer.echo(f"\n{location.value} ({path}):")
        if not channel.events:
            typer.echo("  (no events)")
            continue
        for event in channel.events[:limit]:
            typer.echo(
                f"  [{event.start_at.isoformat()}] {event.title} ({event.location.value})"
            )
        if len(channel.events) > limit:
            typer.echo(f"  ... and {len(channel.events) - limit} more")


def iter_stored_channels(
    locations: Iterable[HiloLocation] | None = None,
) -> list[HiloChannel]:
    """Load all on-disk Hi-Lo channels for the given locations."""
    targets = resolve_locations(list(locations) if locations is not None else None)
    return [load_channel_from_store(default_store_path(location)) for location in targets]


def _sync_location(
    location: HiloLocation,
    *,
    store_path: Path | None = None,
    scraped: HiloChannel | None = None,
) -> None:
    path = store_path or default_store_path(location)
    channel = scraped or scrape_location_channel(location)
    merged, counts = sync_channel(channel, channel.events, store_path=path)
    typer.echo(
        f"Synced {location.value}: added={counts['added']} "
        f"updated={counts['updated']} total={counts['total']} "
        f"-> {path}"
    )
    _ = merged
