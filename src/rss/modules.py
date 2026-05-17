"""Registry of feed source modules (hilo, ...)."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

import typer

from rss.hilo import ops as hilo_ops
from rss.hilo.types import HiloLocation


class FeedModule(Protocol):
    name: str

    def scrape(self, **kwargs: Any) -> None: ...

    def sync(self, **kwargs: Any) -> None: ...

    def list_events(self, **kwargs: Any) -> None: ...


@dataclass(frozen=True, slots=True)
class HiloFeedModule:
    name: str = "hilo"

    def scrape(
        self,
        *,
        locations: list[HiloLocation] | None = None,
        output: Path | None = None,
    ) -> None:
        hilo_ops.scrape(locations=locations, output=output)

    def sync(
        self,
        *,
        locations: list[HiloLocation] | None = None,
        store_path: Path | None = None,
    ) -> None:
        hilo_ops.sync(locations=locations, store_path=store_path)

    def list_events(
        self,
        *,
        locations: list[HiloLocation] | None = None,
        store_path: Path | None = None,
        limit: int = 20,
    ) -> None:
        hilo_ops.list_events(locations=locations, store_path=store_path, limit=limit)


_MODULES: dict[str, FeedModule] = {
    "hilo": HiloFeedModule(),
}


def available_modules() -> tuple[str, ...]:
    return tuple(sorted(_MODULES))


def resolve_modules(names: list[str] | None) -> list[FeedModule]:
    if not names:
        return [_MODULES[name] for name in available_modules()]
    modules: list[FeedModule] = []
    for name in names:
        try:
            modules.append(_MODULES[name])
        except KeyError as exc:
            raise typer.BadParameter(
                f"Unknown module {name!r}. Choose from: {', '.join(available_modules())}"
            ) from exc
    return modules


def iter_modules(names: list[str] | None = None) -> Iterator[FeedModule]:
    yield from resolve_modules(names)
