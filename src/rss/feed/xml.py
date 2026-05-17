"""Render RSS 2.0 XML from generic feed models."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from email.utils import format_datetime
from pathlib import Path
from xml.etree import ElementTree as ET

from rss.feed.types import FeedChannel, FeedItem


def format_rss_datetime(value: datetime) -> str:
    """Format a datetime in RFC 822 style for RSS ``pubDate`` elements."""
    return format_datetime(value, usegmt=False)


def render_rss_feed(channel: FeedChannel, items: Sequence[FeedItem]) -> str:
    """Render a complete RSS 2.0 document."""
    root = ET.Element("rss", version="2.0")
    channel_element = _append_channel(root, channel)
    for item in items:
        _append_item(channel_element, item)
    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ")
    body = ET.tostring(root, encoding="unicode")
    return f'<?xml version="1.0" encoding="UTF-8"?>\n{body}'


def write_rss_feed(
    path: Path,
    channel: FeedChannel,
    items: Sequence[FeedItem],
) -> None:
    """Write an RSS 2.0 document to disk."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_rss_feed(channel, items), encoding="utf-8")


def _append_channel(root: ET.Element, channel: FeedChannel) -> ET.Element:
    channel_element = ET.SubElement(root, "channel")
    _set_text(channel_element, "title", channel.title)
    _set_text(channel_element, "link", str(channel.link))
    _set_text(channel_element, "description", channel.description)
    _set_text(channel_element, "language", channel.language)
    if channel.last_build_date is not None:
        _set_text(
            channel_element,
            "lastBuildDate",
            format_rss_datetime(channel.last_build_date),
        )
    if channel.ttl_minutes is not None:
        _set_text(channel_element, "ttl", str(channel.ttl_minutes))
    return channel_element


def _append_item(channel_element: ET.Element, item: FeedItem) -> None:
    item_element = ET.SubElement(channel_element, "item")
    _set_text(item_element, "title", item.title)
    _set_text(item_element, "link", str(item.link))
    _set_text(item_element, "description", item.description)
    _set_text(item_element, "pubDate", format_rss_datetime(item.pub_date))
    guid_element = ET.SubElement(item_element, "guid")
    guid_element.text = item.guid
    if not item.guid_is_permalink:
        guid_element.set("isPermaLink", "false")
    for category in item.categories:
        _set_text(item_element, "category", category)
    if item.enclosure is not None:
        attributes = {
            "url": str(item.enclosure.url),
            "type": item.enclosure.mime_type,
        }
        if item.enclosure.length is not None:
            attributes["length"] = str(item.enclosure.length)
        ET.SubElement(item_element, "enclosure", attrib=attributes)


def _set_text(parent: ET.Element, tag: str, text: str) -> None:
    element = ET.SubElement(parent, tag)
    element.text = text
