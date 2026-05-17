"""Build RSS XML feeds from JSON stores under ``data/``."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pendulum

from rss.feed.paths import ALL_FEED_PATH, DATA_DIR, FEEDS_DIR, store_feed_path
from rss.feed.registry import load_channel, registered_modules
from rss.feed.types import FeedChannel, FeedItem, sort_feed_items
from rss.feed.xml import write_rss_feed

ALL_FEED_TITLE = "All Events"
ALL_FEED_DESCRIPTION = "Combined events from all local feed sources."
ALL_FEED_LINK = "feeds/all.xml"


def iter_data_stores(data_dir: Path = DATA_DIR) -> Iterator[tuple[str, Path]]:
    """Yield ``(module_name, json_path)`` for each store under ``data/<module>/``."""
    if not data_dir.is_dir():
        return
    for module_dir in sorted(data_dir.iterdir()):
        if not module_dir.is_dir():
            continue
        if module_dir.name not in registered_modules():
            continue
        for store_path in sorted(module_dir.glob("*.json")):
            yield module_dir.name, store_path


def build_feeds(
    *,
    data_dir: Path = DATA_DIR,
    feeds_dir: Path = FEEDS_DIR,
    upcoming_only: bool = False,
) -> list[Path]:
    """Write per-store feeds and a combined ``all.xml`` feed under ``feeds/``."""
    written: list[Path] = []
    all_items: list[FeedItem] = []

    for module_name, store_path in iter_data_stores(data_dir):
        channel = load_channel(module_name, store_path)
        feed_channel = channel.to_feed_channel(upcoming_only=upcoming_only)
        output_path = store_feed_path(module_name, store_path)
        write_rss_feed(output_path, feed_channel, feed_channel.items)
        written.append(output_path)
        all_items.extend(feed_channel.items)

    all_path = ALL_FEED_PATH if feeds_dir == FEEDS_DIR else feeds_dir / "all.xml"
    combined = FeedChannel(
        title=ALL_FEED_TITLE,
        link=ALL_FEED_LINK,
        description=ALL_FEED_DESCRIPTION,
        last_build_date=pendulum.now(),
        items=sort_feed_items(all_items),
    )
    write_rss_feed(all_path, combined, combined.items)
    written.append(all_path)
    return written
