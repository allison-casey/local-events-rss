"""Generic RSS 2.0 channel and item models shared across feed modules."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from datetime import datetime
from typing import Protocol, TypeVar

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

T = TypeVar("T", contravariant=True)


class FeedEnclosure(BaseModel):
    """Media enclosure attached to a feed item."""

    model_config = ConfigDict(frozen=True)

    url: HttpUrl | str
    mime_type: str
    length: int | None = None


class FeedItem(BaseModel):
    """One entry in an RSS 2.0 feed."""

    model_config = ConfigDict(frozen=True)

    guid: str
    title: str
    link: HttpUrl | str
    description: str
    pub_date: datetime
    guid_is_permalink: bool = False
    categories: tuple[str, ...] = ()
    enclosure: FeedEnclosure | None = None


class FeedChannel(BaseModel):
    """RSS 2.0 channel metadata."""

    model_config = ConfigDict(frozen=True)

    title: str
    link: HttpUrl | str
    description: str
    language: str = "en-us"
    last_build_date: datetime | None = None
    ttl_minutes: int | None = Field(default=None, ge=1)


class FeedItemMapper(Protocol[T]):
    """Map a source-specific record to a generic ``FeedItem``."""

    def __call__(self, source: T, /) -> FeedItem: ...


def map_to_feed_items(
    sources: Iterable[T],
    mapper: Callable[[T], FeedItem],
) -> list[FeedItem]:
    """Map an iterable of source records into feed items."""
    return [mapper(source) for source in sources]


def sort_feed_items(
    items: Sequence[FeedItem],
    *,
    reverse: bool = True,
) -> list[FeedItem]:
    """Sort feed items by publication date."""
    return sorted(items, key=lambda item: item.pub_date, reverse=reverse)
