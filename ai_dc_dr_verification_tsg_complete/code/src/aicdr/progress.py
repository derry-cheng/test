"""Small optional progress-wrapper fallback for minimal reproduction images."""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from typing import Any


class _FallbackProgress:
    """Keep long runs functional when the optional tqdm wheel is unavailable."""

    def __init__(self, iterable: Iterable[Any] | None = None, **_: Any) -> None:
        self._iterable = iterable

    def __iter__(self) -> Iterator[Any]:
        if self._iterable is None:
            return iter(())
        return iter(self._iterable)

    def update(self, _: int = 1) -> None:
        return None

    def close(self) -> None:
        return None


try:  # pragma: no cover - exercised when the optional dependency is installed
    from tqdm.auto import tqdm as progress  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - minimal CI/reproduction images
    progress = _FallbackProgress


__all__ = ["progress"]
