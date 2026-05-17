"""Shared RSS 2.0 feed types, XML rendering, and feed generation."""

from rss.feed._register import register_builtin_modules
from rss.feed.build import build_feeds, iter_data_stores
from rss.feed.paths import ALL_FEED_PATH, DATA_DIR, FEEDS_DIR, store_feed_path
from rss.feed.registry import load_channel, registered_modules, register_module
from rss.feed.types import (
    FeedChannel,
    FeedEnclosure,
    FeedItem,
    RssChannel,
    RssEvent,
    sort_feed_items,
)
from rss.feed.xml import format_rss_datetime, render_rss_feed, write_rss_feed

register_builtin_modules()

__all__ = [
    "ALL_FEED_PATH",
    "DATA_DIR",
    "FEEDS_DIR",
    "FeedChannel",
    "FeedEnclosure",
    "FeedItem",
    "RssChannel",
    "RssEvent",
    "build_feeds",
    "format_rss_datetime",
    "iter_data_stores",
    "load_channel",
    "register_module",
    "registered_modules",
    "render_rss_feed",
    "sort_feed_items",
    "store_feed_path",
    "write_rss_feed",
]
