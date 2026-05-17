"""Map Hi-Lo events to generic RSS feed models."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from typing import Final

import pendulum

from rss.feed.types import (
    FeedChannel,
    FeedItem,
    sort_feed_items,
)
from rss.hilo.scraping import DEFAULT_TIMEZONE
from rss.hilo.types import LOCATION_PAGE_URLS, HiloEvent, HiloLocation


DEFAULT_CULVER_CITY_FEED_PATH: Final[Path] = Path("data/hilo/culver_city_feed.xml")


def build_hilo_channel(location: HiloLocation) -> FeedChannel:
    """Build RSS channel metadata for a Hi-Lo store location."""
    return FeedChannel(
        title=f"Hi-Lo Liquor Market — {location.value} Events",
        link=LOCATION_PAGE_URLS[location],
        description=(
            f"Upcoming tastings, pop-ups, and events at Hi-Lo Liquor Market "
            f"({location.value})."
        ),
        last_build_date=pendulum.now(DEFAULT_TIMEZONE),
        ttl_minutes=60,
    )


def hilo_events_to_feed_items(
    events: Iterable[HiloEvent],
    *,
    location: HiloLocation | None = None,
    upcoming_only: bool = False,
    timezone: str = DEFAULT_TIMEZONE,
) -> list[FeedItem]:
    """Map Hi-Lo events to RSS items with optional filtering."""
    filtered = filter_hilo_events(
        events,
        location=location,
        upcoming_only=upcoming_only,
        timezone=timezone,
    )
    return sort_feed_items([e.to_feed_item() for e in filtered])


def filter_hilo_events(
    events: Iterable[HiloEvent],
    *,
    location: HiloLocation | None = None,
    upcoming_only: bool = False,
    timezone: str = DEFAULT_TIMEZONE,
) -> list[HiloEvent]:
    """Filter events by location and whether they are still upcoming."""
    now = pendulum.now(timezone)
    selected: list[HiloEvent] = []
    for event in events:
        if location is not None and event.location is not location:
            continue
        if upcoming_only and pendulum.instance(event.end_at) < now:
            continue
        selected.append(event)
    return selected
