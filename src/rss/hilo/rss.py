"""Map Hi-Lo channels to generic RSS feed models."""

from __future__ import annotations

from rss.feed.types import FeedChannel, FeedItem
from rss.hilo.types import HiloChannel, HiloEvent, HiloLocation


def build_hilo_channel(
    location: HiloLocation,
    events: list[HiloEvent] | None = None,
) -> HiloChannel:
    """Build a Hi-Lo channel for one store location."""
    return HiloChannel.for_location(location, events)


def hilo_channel_to_feed(
    channel: HiloChannel,
    *,
    upcoming_only: bool = False,
) -> tuple[FeedChannel, list[FeedItem]]:
    """Render a Hi-Lo channel as generic RSS channel metadata and items."""
    feed_channel = channel.to_feed_channel(upcoming_only=upcoming_only)
    return feed_channel, feed_channel.items
