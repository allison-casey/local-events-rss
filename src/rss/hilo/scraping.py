"""Scrape Hi-Lo Liquor Market location events from hiloliquor.com."""

from __future__ import annotations

import hashlib
import re
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Final

import httpx
import pendulum
from bs4 import BeautifulSoup, Tag

from rss.hilo.types import DEFAULT_TIMEZONE, HiloChannel, HiloEvent, HiloLocation

DEFAULT_LOCATIONS_URL: Final[str] = "https://hiloliquor.com/locations/"
_EVENT_ITEM_CLASS: Final[str] = "item-single-bar"
_TIME_RANGE_RE: Final[re.Pattern[str]] = re.compile(
    r"(?P<weekday>\w+)\s+"
    r"(?P<start>\d{1,2}:\d{2}(?:am|pm))\s*[–\-]\s*"
    r"(?P<end>\d{1,2}:\d{2}(?:am|pm))"
    r"(?:\s+Pacific)?",
    re.IGNORECASE,
)
_MONTH_DAY_RE: Final[re.Pattern[str]] = re.compile(
    r"^(?P<month>[A-Za-z]+)$",
)
_DAY_RE: Final[re.Pattern[str]] = re.compile(
    r"^(?P<day>\d{1,2})$",
)


@dataclass(frozen=True, slots=True)
class _RawEventFields:
    location: HiloLocation
    month_label: str
    day: int
    schedule_label: str
    title: str
    description: str
    image_url: str | None


def fetch_locations_html(
    url: str = DEFAULT_LOCATIONS_URL,
    *,
    client: httpx.Client | None = None,
) -> str:
    """Download the locations page HTML."""
    if client is not None:
        response = client.get(url, follow_redirects=True)
        response.raise_for_status()
        return response.text

    with httpx.Client(timeout=30.0) as owned:
        response = owned.get(url, follow_redirects=True)
        response.raise_for_status()
        return response.text


def parse_locations_html(html: str) -> BeautifulSoup:
    """Parse locations page HTML into a BeautifulSoup document."""
    return BeautifulSoup(html, "html.parser")


def iter_location_event_elements(
    soup: BeautifulSoup,
    location: HiloLocation,
) -> Iterator[Tag]:
    """Yield event list item elements for a single store location."""
    location_heading = _find_location_heading(soup, location)
    events_heading = _find_following_events_heading(location_heading)
    yield from _iter_event_items_until_next_section(events_heading)


def scrape_location_events(
    location: HiloLocation,
    *,
    url: str = DEFAULT_LOCATIONS_URL,
    client: httpx.Client | None = None,
    timezone: str = DEFAULT_TIMEZONE,
) -> list[HiloEvent]:
    """Fetch and parse all events for one Hi-Lo location."""
    return scrape_location_channel(
        location,
        url=url,
        client=client,
        timezone=timezone,
    ).events


def scrape_location_channel(
    location: HiloLocation,
    *,
    url: str = DEFAULT_LOCATIONS_URL,
    client: httpx.Client | None = None,
    timezone: str = DEFAULT_TIMEZONE,
    soup: BeautifulSoup | None = None,
) -> HiloChannel:
    """Fetch and parse a Hi-Lo channel for one store location."""
    if soup is None:
        html = fetch_locations_html(url, client=client)
        soup = parse_locations_html(html)
    return _channel_from_soup(soup, location, timezone=timezone)


def scrape_location_channels(
    locations: list[HiloLocation],
    *,
    url: str = DEFAULT_LOCATIONS_URL,
    client: httpx.Client | None = None,
    timezone: str = DEFAULT_TIMEZONE,
) -> list[HiloChannel]:
    """Fetch the locations page once and parse channels for each location."""
    html = fetch_locations_html(url, client=client)
    soup = parse_locations_html(html)
    return [
        _channel_from_soup(soup, location, timezone=timezone) for location in locations
    ]


def _channel_from_soup(
    soup: BeautifulSoup,
    location: HiloLocation,
    *,
    timezone: str,
) -> HiloChannel:
    now = pendulum.now(timezone)
    events = [
        _to_hilo_event(raw, now=now, timezone=timezone)
        for raw in (
            _parse_event_element(element, location)
            for element in iter_location_event_elements(soup, location)
        )
    ]
    return HiloChannel.for_location(location, events)


def build_event_id(
    location: HiloLocation, title: str, start_at: pendulum.DateTime
) -> str:
    """Build a stable event identifier for upserts."""
    payload = f"{location.value}|{title}|{start_at.to_iso8601_string()}"
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


def _find_location_heading(soup: BeautifulSoup, location: HiloLocation) -> Tag:
    for heading in soup.find_all("h2"):
        if heading.get_text(strip=True) == location.value:
            return heading
    raise ValueError(f"Location section not found: {location.value}")


def _find_following_events_heading(location_heading: Tag) -> Tag:
    for heading in location_heading.find_all_next("h2"):
        if heading.get_text(strip=True) == "Events":
            return heading
    raise ValueError("Events section not found after location heading")


def _iter_event_items_until_next_section(events_heading: Tag) -> Iterator[Tag]:
    for element in events_heading.find_all_next():
        if element.name == "h2" and element is not events_heading:
            return
        if element.name != "li":
            continue
        classes = element.get("class") or []
        if _EVENT_ITEM_CLASS in classes:
            yield element


def _parse_event_element(element: Tag, location: HiloLocation) -> _RawEventFields:
    month_label, day = _parse_month_day(element)
    schedule_label = _text_from_selector(element, "p[class*='tracking-customSix']")
    description = _optional_text_from_selector(element, "p.my-2")
    title = _parse_title(element, description=description)
    image = element.find("img")
    image_url = str(image.get("src")) if image else None
    if isinstance(image_url, str) and not image_url.strip():
        image_url = None
    return _RawEventFields(
        location=location,
        month_label=month_label,
        day=day,
        schedule_label=schedule_label,
        title=title,
        description=description,
        image_url=image_url,
    )


def _parse_month_day(element: Tag) -> tuple[str, int]:
    month_paragraph: str | None = None
    day_value: int | None = None
    for paragraph in element.find_all("p"):
        text = paragraph.get_text(strip=True)
        if not text:
            continue
        if month_paragraph is None and _MONTH_DAY_RE.match(text):
            month_paragraph = text
            continue
        day_match = _DAY_RE.match(text)
        if day_match is not None:
            day_value = int(day_match.group("day"))
    if month_paragraph is None or day_value is None:
        raise ValueError("Could not parse month and day from event element")
    return month_paragraph, day_value


def _parse_title(element: Tag, *, description: str) -> str:
    """Parse event title, falling back when the primary heading is empty."""
    title = _optional_text_from_selector(element, "p.text-3xl")
    if title:
        return title
    if description:
        first_sentence = description.split(".", 1)[0].strip()
        return first_sentence or description[:120].strip()
    image = element.find("img")
    if image is not None:
        alt = (image.get("alt") or "").strip()
        if alt:
            return alt
    raise ValueError("Could not parse event title from element")


def _text_from_selector(element: Tag, selector: str) -> str:
    text = _optional_text_from_selector(element, selector)
    if not text:
        matched = element.select_one(selector)
        if matched is None:
            raise ValueError(f"Missing element for selector: {selector}")
        raise ValueError(f"Empty text for selector: {selector}")
    return text


def _optional_text_from_selector(element: Tag, selector: str) -> str:
    matched = element.select_one(selector)
    if matched is None:
        return ""
    return matched.get_text(strip=True)


def _to_hilo_event(
    raw: _RawEventFields,
    *,
    now: pendulum.DateTime,
    timezone: str,
) -> HiloEvent:
    start_at, end_at = parse_schedule(
        raw.month_label,
        raw.day,
        raw.schedule_label,
        now=now,
        timezone=timezone,
    )
    event_id = build_event_id(raw.location, raw.title, start_at)
    return HiloEvent.model_validate(
        {
            "event_id": event_id,
            "location": raw.location,
            "title": raw.title,
            "description": raw.description,
            "start_at": start_at,
            "end_at": end_at,
            "image_url": raw.image_url,
        }
    )


def parse_schedule(
    month_label: str,
    day: int,
    schedule_label: str,
    *,
    now: pendulum.DateTime,
    timezone: str,
) -> tuple[pendulum.DateTime, pendulum.DateTime]:
    """Parse page date fragments into timezone-aware start and end datetimes."""
    match = _TIME_RANGE_RE.match(schedule_label.strip())
    if match is None:
        raise ValueError(f"Unrecognized schedule label: {schedule_label!r}")

    month = pendulum.parse(month_label, strict=False)
    if not isinstance(month, pendulum.DateTime):
        raise ValueError(f"Unrecognized month label: {month_label!r}")

    year = _infer_year(month.month, day, now=now)
    start = _parse_time_on_date(
        year=year,
        month=month.month,
        day=day,
        time_text=match.group("start"),
        timezone=timezone,
    )
    end = _parse_time_on_date(
        year=year,
        month=month.month,
        day=day,
        time_text=match.group("end"),
        timezone=timezone,
    )
    if end <= start:
        end = end.add(days=1)
    return start, end


def _infer_year(month: int, day: int, *, now: pendulum.DateTime) -> int:
    """Choose the calendar year whose month/day is closest to the scrape date."""
    best_year = now.year
    best_distance = _days_from_now(now.replace(month=month, day=day), now=now)
    for year in (now.year - 1, now.year, now.year + 1):
        candidate = now.replace(year=year, month=month, day=day)
        distance = _days_from_now(candidate, now=now)
        if distance < best_distance:
            best_distance = distance
            best_year = year
    return best_year


def _days_from_now(candidate: pendulum.DateTime, *, now: pendulum.DateTime) -> int:
    return abs(candidate.diff(now).in_days())


def _parse_time_on_date(
    *,
    year: int,
    month: int,
    day: int,
    time_text: str,
    timezone: str,
) -> pendulum.DateTime:
    parsed = pendulum.from_format(
        f"{year}-{month:02d}-{day:02d} {time_text.lower()}",
        "YYYY-M-D h:mma",
        tz=timezone,
    )
    if not isinstance(parsed, pendulum.DateTime):
        raise ValueError(f"Could not parse time: {time_text!r}")
    return parsed
