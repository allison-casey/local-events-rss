"""Generic RSS 2.0 channel and item models shared across feed modules."""

from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from collections.abc import Callable, Iterable, Sequence
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


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
    items: list[FeedItem]


class RssChannel(ABC, BaseModel):
    events: list[RssEvent]

    @abstractmethod
    def to_feed_channel(self) -> FeedChannel:
        pass


class RssEvent(ABC, BaseModel):
    @abstractmethod
    def to_feed_item(self) -> FeedItem:
        pass


def sort_feed_items(
    items: Sequence[FeedItem],
    *,
    reverse: bool = True,
) -> list[FeedItem]:
    """Sort feed items by publication date."""
    return sorted(items, key=lambda item: item.pub_date, reverse=reverse)
