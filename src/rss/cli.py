"""Typer CLI for custom RSS feed scrapers."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from rss.feed.xml import write_rss_feed
from rss.hilo.rss import DEFAULT_CULVER_CITY_FEED_PATH, hilo_channel_to_feed
from rss.hilo.scraping import scrape_location_channel, scrape_location_channels
from rss.hilo.types import ALL_HILO_LOCATIONS, HiloChannel, HiloLocation
from rss.hilo.upsert import default_store_path, load_channel, save_channel, sync_channel

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
    channel = scrape_location_channel(location)
    typer.echo(f"Scraped {len(channel.events)} event(s) for {location.value}.")
    if output is not None:
        save_channel(output, channel)
        typer.echo(f"Wrote {output}.")


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


@hilo_app.command("sync")
def hilo_sync(
    locations: Annotated[
        list[HiloLocation],
        typer.Option(
            "--location",
            "-l",
            help="Store location(s) to sync (default: all locations).",
        ),
    ] = [],
    store_path: Annotated[
        Path | None,
        typer.Option(
            "--store",
            help="JSON file for a single-location sync (ignored when syncing multiple).",
        ),
    ] = None,
) -> None:
    """Scrape events, upsert them into per-location JSON stores, and print counts."""
    targets = locations or list(ALL_HILO_LOCATIONS)
    if store_path is not None and len(targets) != 1:
        raise typer.BadParameter("--store requires exactly one --location")
    if len(targets) == 1:
        _sync_location(targets[0], store_path=store_path)
        return
    for scraped in scrape_location_channels(targets):
        _sync_location(scraped.location, scraped=scraped)


@hilo_app.command("list")
def hilo_list(
    location: Annotated[
        HiloLocation,
        typer.Option("--location", "-l", help="Store location to list."),
    ] = HiloLocation.CULVER_CITY,
    store_path: Annotated[
        Path | None,
        typer.Option(
            "--store",
            help="JSON channel store to read (default: per-location store file).",
        ),
    ] = None,
    limit: Annotated[
        int,
        typer.Option("--limit", "-n", help="Maximum number of events to print."),
    ] = 20,
) -> None:
    """List events currently stored for Hi-Lo."""
    path = store_path or default_store_path(location)
    channel = load_channel(path, location)
    if not channel.events:
        typer.echo(f"No events found for {location.value} in {path}.")
        raise typer.Exit(code=0)

    for event in channel.events[:limit]:
        typer.echo(
            f"[{event.start_at.isoformat()}] {event.title} ({event.location.value})"
        )
    if len(channel.events) > limit:
        typer.echo(f"... and {len(channel.events) - limit} more")


@hilo_app.command("feed")
def hilo_feed(
    location: Annotated[
        HiloLocation,
        typer.Option("--location", "-l", help="Store location to include in the feed."),
    ] = HiloLocation.CULVER_CITY,
    store_path: Annotated[
        Path | None,
        typer.Option(
            "--store",
            help="JSON channel store to read (default: per-location store file).",
        ),
    ] = None,
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
    path = store_path or default_store_path(location)
    channel = load_channel(path, location)
    feed_channel, items = hilo_channel_to_feed(channel, upcoming_only=upcoming_only)
    write_rss_feed(output, feed_channel, items)
    typer.echo(f"Wrote {len(items)} item(s) for {location.value} to {output}.")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
