"""Pydantic models for Hi-Lo Liquor Market events."""

from __future__ import annotations

from html import escape
from typing import Final

import pendulum
from enum import StrEnum

from pydantic import ConfigDict, Field, HttpUrl, model_validator
from pydantic_extra_types.pendulum_dt import DateTime

from rss.feed.types import (
    FeedChannel,
    FeedEnclosure,
    FeedItem,
    RssChannel,
    RssEvent,
    sort_feed_items,
)

DEFAULT_TIMEZONE: Final[str] = "America/Los_Angeles"


class HiloLocation(StrEnum):
    """Store locations listed on the Hi-Lo locations page."""

    LONG_BEACH = "Long Beach"
    COSTA_MESA = "Costa Mesa"
    CULVER_CITY = "Culver City"


ALL_HILO_LOCATIONS: Final[tuple[HiloLocation, ...]] = tuple(HiloLocation)


LOCATION_PAGE_URLS: Final[dict[HiloLocation, str]] = {
    HiloLocation.LONG_BEACH: "https://hiloliquor.com/locations/#Long%20Beach",
    HiloLocation.COSTA_MESA: "https://hiloliquor.com/locations/#Costa%20Mesa",
    HiloLocation.CULVER_CITY: "https://hiloliquor.com/locations/#Culver%20City",
}


def _guess_image_mime_type(url: str) -> str:
    lowered = url.lower()
    if lowered.endswith(".png"):
        return "image/png"
    if lowered.endswith(".webp"):
        return "image/webp"
    if lowered.endswith(".gif"):
        return "image/gif"
    return "image/jpeg"


def format_hilo_event_description(event: HiloEvent) -> str:
    """Build HTML description content for a Hi-Lo RSS item."""
    description = escape(event.description) if event.description else ""
    paragraphs = [
        f"<p><strong>When:</strong> {escape(event.start_at.format('MMM D LT'))} - {escape(event.end_at.format('LT'))}</p>",
        f"<p><strong>Where:</strong> {escape(event.location.value)}</p>",
    ]
    if description:
        paragraphs.append(f"<p>{description}</p>")
    return "\n".join(paragraphs)


class HiloEvent(RssEvent):
    """One in-store event at a Hi-Lo location."""

    model_config = ConfigDict(frozen=True)

    event_id: str = Field(description="Stable identifier used for upserts.")
    location: HiloLocation
    title: str
    description: str
    start_at: DateTime
    end_at: DateTime
    image_url: HttpUrl | None = None

    def to_feed_item(self) -> FeedItem:
        return FeedItem(
            guid=self.event_id,
            title=self.title,
            link=LOCATION_PAGE_URLS[self.location],
            description=format_hilo_event_description(self),
            pub_date=self.start_at,
            guid_is_permalink=False,
            categories=(self.location.value,),
            enclosure=(
                FeedEnclosure(
                    url=self.image_url,
                    mime_type=_guess_image_mime_type(str(self.image_url)),
                )
                if self.image_url
                else None
            ),
        )


class HiloChannel(RssChannel[HiloEvent]):
    """RSS source for one Hi-Lo store location and its events."""

    model_config = ConfigDict(frozen=True)

    location: HiloLocation
    events: list[HiloEvent] = Field(default_factory=list)
    language: str = "en-us"
    ttl_minutes: int = Field(default=60, ge=1)

    @model_validator(mode="after")
    def _events_match_location(self) -> HiloChannel:
        for event in self.events:
            if event.location is not self.location:
                raise ValueError(
                    f"Event {event.event_id!r} belongs to {event.location.value}, "
                    f"not {self.location.value}"
                )
        return self

    @property
    def title(self) -> str:
        return f"Hi-Lo Liquor Market — {self.location.value} Events"

    @property
    def link(self) -> str:
        return LOCATION_PAGE_URLS[self.location]

    @property
    def description(self) -> str:
        return (
            f"Upcoming tastings, pop-ups, and events at Hi-Lo Liquor Market "
            f"({self.location.value})."
        )

    @classmethod
    def for_location(
        cls,
        location: HiloLocation,
        events: list[HiloEvent] | None = None,
    ) -> HiloChannel:
        """Build a channel containing only events for ``location``."""
        selected = [event for event in (events or []) if event.location is location]
        return cls(location=location, events=selected)

    def filter_events(
        self,
        *,
        upcoming_only: bool = False,
        timezone: str = DEFAULT_TIMEZONE,
    ) -> list[HiloEvent]:
        """Return channel events, optionally omitting events that have ended."""
        if not upcoming_only:
            return list(self.events)
        now = pendulum.now(timezone)
        return [
            event for event in self.events if pendulum.instance(event.end_at) >= now
        ]

    def to_feed_channel(
        self,
        *,
        upcoming_only: bool = False,
        timezone: str = DEFAULT_TIMEZONE,
    ) -> FeedChannel:
        items = sort_feed_items(
            [
                event.to_feed_item()
                for event in self.filter_events(
                    upcoming_only=upcoming_only,
                    timezone=timezone,
                )
            ]
        )
        return FeedChannel(
            title=self.title,
            link=self.link,
            description=self.description,
            language=self.language,
            last_build_date=pendulum.now(timezone),
            ttl_minutes=self.ttl_minutes,
            items=items,
        )
