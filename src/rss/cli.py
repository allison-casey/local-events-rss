"""Typer CLI for custom RSS feed scrapers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer

from rss.feed.xml import write_rss_feed
from rss.hilo.rss import (
    DEFAULT_CULVER_CITY_FEED_PATH,
    build_hilo_channel,
    hilo_events_to_feed_items,
)
from rss.hilo.scraping import scrape_location_events
from rss.hilo.types import HiloLocation
from rss.hilo.upsert import DEFAULT_CULVER_CITY_STORE_PATH, load_events, sync_events

app = typer.Typer(
    help="Scrape and process custom RSS feed sources.",
    no_args_is_help=True,
    pretty_exceptions_enable=False,
)
hilo_app = typer.Typer(help="Hi-Lo Liquor Market events.")
app.add_typer(hilo_app, name="hilo")


@hilo_app.command("scrape")
def hilo_scrape(
    location: Annotated[
        HiloLocation,
        typer.Option("--location", "-l", help="Store location to scrape."),
    ] = HiloLocation.CULVER_CITY,
    output: Annotated[
        Path | None,
        typer.Option(
            "--output",
            "-o",
            help="Optional JSON file to write scraped events without upserting.",
        ),
    ] = None,
) -> None:
    """Scrape events for a Hi-Lo location and print a summary."""
    events = scrape_location_events(location)
    typer.echo(f"Scraped {len(events)} event(s) for {location.value}.")
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        payload = [event.model_dump(mode="json") for event in events]
        output.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        typer.echo(f"Wrote {output}.")


@hilo_app.command("sync")
def hilo_sync(
    location: Annotated[
        HiloLocation,
        typer.Option("--location", "-l", help="Store location to scrape."),
    ] = HiloLocation.CULVER_CITY,
    store_path: Annotated[
        Path,
        typer.Option(
            "--store",
            help="JSON file used to upsert scraped events.",
        ),
    ] = DEFAULT_CULVER_CITY_STORE_PATH,
) -> None:
    """Scrape events, upsert them into the local store, and print counts."""
    events = scrape_location_events(location)
    merged, counts = sync_events(events, store_path=store_path)
    typer.echo(
        f"Synced {location.value}: added={counts['added']} "
        f"updated={counts['updated']} total={counts['total']} "
        f"-> {store_path}"
    )
    _ = merged


@hilo_app.command("list")
def hilo_list(
    store_path: Annotated[
        Path,
        typer.Option("--store", help="JSON event store to read."),
    ] = DEFAULT_CULVER_CITY_STORE_PATH,
    limit: Annotated[
        int,
        typer.Option("--limit", "-n", help="Maximum number of events to print."),
    ] = 20,
) -> None:
    """List events currently stored for Hi-Lo."""
    events = load_events(store_path)
    if not events:
        typer.echo(f"No events found in {store_path}.")
        raise typer.Exit(code=0)

    for event in events[:limit]:
        typer.echo(
            f"[{event.start_at.isoformat()}] {event.title} ({event.location.value})"
        )
    if len(events) > limit:
        typer.echo(f"... and {len(events) - limit} more")


@hilo_app.command("feed")
def hilo_feed(
    location: Annotated[
        HiloLocation,
        typer.Option("--location", "-l", help="Store location to include in the feed."),
    ] = HiloLocation.CULVER_CITY,
    store_path: Annotated[
        Path,
        typer.Option("--store", help="JSON event store to read."),
    ] = DEFAULT_CULVER_CITY_STORE_PATH,
    output: Annotated[
        Path,
        typer.Option("--output", "-o", help="RSS XML file to write."),
    ] = DEFAULT_CULVER_CITY_FEED_PATH,
    upcoming_only: Annotated[
        bool,
        typer.Option(
            "--upcoming-only",
            help="Omit events that have already ended.",
        ),
    ] = False,
) -> None:
    """Generate an RSS 2.0 XML feed from stored Hi-Lo events."""
    events = load_events(store_path)
    channel = build_hilo_channel(location)
    items = hilo_events_to_feed_items(
        events,
        location=location,
        upcoming_only=upcoming_only,
    )
    write_rss_feed(output, channel, items)
    typer.echo(f"Wrote {len(items)} item(s) for {location.value} to {output}.")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
