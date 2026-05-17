"""Map Hi-Lo events to generic RSS feed models."""

from __future__ import annotations

from collections.abc import Iterable
from html import escape
from pathlib import Path
from typing import Final

import pendulum

from rss.feed.types import FeedChannel, FeedEnclosure, FeedItem, map_to_feed_items, sort_feed_items
from rss.hilo.scraping import DEFAULT_TIMEZONE
from rss.hilo.types import HiloEvent, HiloLocation

LOCATION_PAGE_URLS: Final[dict[HiloLocation, str]] = {
    HiloLocation.LONG_BEACH: "https://hiloliquor.com/locations/#Long%20Beach",
    HiloLocation.COSTA_MESA: "https://hiloliquor.com/locations/#Costa%20Mesa",
    HiloLocation.CULVER_CITY: "https://hiloliquor.com/locations/#Culver%20City",
}

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


def hilo_event_to_feed_item(event: HiloEvent) -> FeedItem:
    """Map one Hi-Lo event to a generic RSS feed item."""
    enclosure = None
    if event.image_url is not None:
        enclosure = FeedEnclosure(
            url=event.image_url,
            mime_type=_guess_image_mime_type(str(event.image_url)),
        )
    return FeedItem(
        guid=event.event_id,
        title=event.title,
        link=LOCATION_PAGE_URLS[event.location],
        description=format_hilo_event_description(event),
        pub_date=event.start_at,
        guid_is_permalink=False,
        categories=(event.location.value,),
        enclosure=enclosure,
    )


def format_hilo_event_description(event: HiloEvent) -> str:
    """Build HTML description content for a Hi-Lo RSS item."""
    description = escape(event.description) if event.description else ""
    paragraphs = [
        f"<p><strong>When:</strong> {escape(event.schedule_label)} "
        f"({escape(event.month_label)} {event.day})</p>",
        f"<p><strong>Where:</strong> {escape(event.location.value)}</p>",
    ]
    if description:
        paragraphs.append(f"<p>{description}</p>")
    return "\n".join(paragraphs)


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
    return sort_feed_items(map_to_feed_items(filtered, hilo_event_to_feed_item))


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


def _guess_image_mime_type(url: str) -> str:
    lowered = url.lower()
    if lowered.endswith(".png"):
        return "image/png"
    if lowered.endswith(".webp"):
        return "image/webp"
    if lowered.endswith(".gif"):
        return "image/gif"
    return "image/jpeg"
