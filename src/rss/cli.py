"""Typer CLI for custom RSS feed scrapers."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from rss.feed import build_feeds
from rss.hilo import ops as hilo_ops
from rss.hilo.types import HiloLocation
from rss.modules import resolve_modules

app = typer.Typer(
    help="Scrape and process custom RSS feed sources.",
    no_args_is_help=True,
    pretty_exceptions_enable=False,
)
hilo_app = typer.Typer(help="Hi-Lo Liquor Market events.")
app.add_typer(hilo_app, name="hilo")


@app.command("scrape")
def scrape(
    modules: Annotated[
        list[str],
        typer.Option(
            "--module",
            "-m",
            help="Feed module(s) to scrape (default: all registered modules).",
        ),
    ] = [],
    locations: Annotated[
        list[HiloLocation],
        typer.Option(
            "--location",
            "-l",
            help="Hi-Lo location(s) to scrape (default: all Hi-Lo locations).",
        ),
    ] = [],
    output: Annotated[
        Path | None,
        typer.Option(
            "--output",
            "-o",
            help="Optional JSON file for a single Hi-Lo location scrape.",
        ),
    ] = None,
) -> None:
    """Scrape feed source modules and print summaries."""
    selected = resolve_modules(modules or None)
    for module in selected:
        if module.name == "hilo":
            module.scrape(
                locations=locations or None,
                output=output if len(selected) == 1 else None,
            )
        else:
            module.scrape()


@app.command("sync")
def sync(
    modules: Annotated[
        list[str],
        typer.Option("--module", "-m", help="Feed module(s) to sync."),
    ] = [],
    locations: Annotated[
        list[HiloLocation],
        typer.Option("--location", "-l", help="Hi-Lo location(s) to sync."),
    ] = [],
    store_path: Annotated[
        Path | None,
        typer.Option(
            "--store",
            help="JSON store for a single Hi-Lo location sync.",
        ),
    ] = None,
) -> None:
    """Scrape and upsert feed source modules into JSON stores under ``data/``."""
    selected = resolve_modules(modules or None)
    for module in selected:
        if module.name == "hilo":
            module.sync(
                locations=locations or None,
                store_path=store_path if len(selected) == 1 else None,
            )
        else:
            module.sync()


@app.command("list")
def list_events(
    modules: Annotated[
        list[str],
        typer.Option("--module", "-m", help="Feed module(s) to list."),
    ] = [],
    locations: Annotated[
        list[HiloLocation],
        typer.Option("--location", "-l", help="Hi-Lo location(s) to list."),
    ] = [],
    store_path: Annotated[
        Path | None,
        typer.Option("--store", help="JSON store for a single Hi-Lo location."),
    ] = None,
    limit: Annotated[
        int,
        typer.Option("--limit", "-n", help="Maximum events to print per channel."),
    ] = 20,
) -> None:
    """List events stored under ``data/`` for each feed module."""
    selected = resolve_modules(modules or None)
    for module in selected:
        if module.name == "hilo":
            module.list_events(
                locations=locations or None,
                store_path=store_path if len(selected) == 1 else None,
                limit=limit,
            )
        else:
            module.list_events(limit=limit)


@app.command("feed")
def feed(
    upcoming_only: Annotated[
        bool,
        typer.Option(
            "--upcoming-only",
            help="Omit events that have already ended.",
        ),
    ] = False,
) -> None:
    """Build RSS feeds under ``feeds/`` from JSON stores under ``data/``."""
    paths = build_feeds(upcoming_only=upcoming_only)
    for path in paths:
        typer.echo(f"Wrote {path}")


@hilo_app.command("scrape")
def hilo_scrape(
    locations: Annotated[
        list[HiloLocation],
        typer.Option("--location", "-l", help="Store location(s) to scrape."),
    ] = [],
    output: Annotated[
        Path | None,
        typer.Option("--output", "-o", help="Optional JSON output file."),
    ] = None,
) -> None:
    """Scrape Hi-Lo locations."""
    hilo_ops.scrape(locations=locations or None, output=output)


@hilo_app.command("sync")
def hilo_sync(
    locations: Annotated[
        list[HiloLocation],
        typer.Option("--location", "-l", help="Store location(s) to sync."),
    ] = [],
    store_path: Annotated[
        Path | None,
        typer.Option("--store", help="JSON store for a single-location sync."),
    ] = None,
) -> None:
    """Sync Hi-Lo JSON stores under ``data/hilo/``."""
    hilo_ops.sync(locations=locations or None, store_path=store_path)


@hilo_app.command("list")
def hilo_list(
    locations: Annotated[
        list[HiloLocation],
        typer.Option("--location", "-l", help="Store location(s) to list."),
    ] = [],
    store_path: Annotated[
        Path | None,
        typer.Option("--store", help="JSON store for a single location."),
    ] = None,
    limit: Annotated[
        int,
        typer.Option("--limit", "-n", help="Maximum number of events to print."),
    ] = 20,
) -> None:
    """List Hi-Lo events from JSON stores."""
    hilo_ops.list_events(locations=locations or None, store_path=store_path, limit=limit)


@hilo_app.command("feed")
def hilo_feed(
    upcoming_only: Annotated[
        bool,
        typer.Option("--upcoming-only", help="Omit events that have already ended."),
    ] = False,
) -> None:
    """Build RSS feeds for all JSON stores (including combined ``feeds/all.xml``)."""
    paths = build_feeds(upcoming_only=upcoming_only)
    for path in paths:
        typer.echo(f"Wrote {path}")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
