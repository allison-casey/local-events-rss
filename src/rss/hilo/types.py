"""Pydantic models for Hi-Lo Liquor Market events."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class HiloLocation(StrEnum):
    """Store locations listed on the Hi-Lo locations page."""

    LONG_BEACH = "Long Beach"
    COSTA_MESA = "Costa Mesa"
    CULVER_CITY = "Culver City"


class HiloEvent(BaseModel):
    """One in-store event at a Hi-Lo location."""

    model_config = ConfigDict(frozen=True)

    event_id: str = Field(description="Stable identifier used for upserts.")
    location: HiloLocation
    title: str
    description: str
    schedule_label: str = Field(
        description="Raw schedule text from the page, e.g. 'Saturday 04:00pm – 07:00pm'."
    )
    month_label: str = Field(description="Month name from the page, e.g. 'May'.")
    day: int = Field(ge=1, le=31)
    start_at: datetime
    end_at: datetime
    image_url: HttpUrl | None = None
