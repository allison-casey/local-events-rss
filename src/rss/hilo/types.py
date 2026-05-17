"""Pydantic models for Hi-Lo Liquor Market events."""

from __future__ import annotations
from html import escape
from typing import Final

from pydantic_extra_types.pendulum_dt import DateTime
from enum import StrEnum

from pydantic import ConfigDict, Field, HttpUrl

from rss.feed.types import FeedEnclosure, FeedItem, RssEvent


class HiloLocation(StrEnum):
    """Store locations listed on the Hi-Lo locations page."""

    LONG_BEACH = "Long Beach"
    COSTA_MESA = "Costa Mesa"
    CULVER_CITY = "Culver City"


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
        f"<p><strong>When:</strong> {escape(event.start_at.format('MMM D LT'))} - {escape(event.end_at.format('LT'))}",
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
