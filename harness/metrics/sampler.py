from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable, Iterable, TypeVar


T = TypeVar("T")


@dataclass(frozen=True)
class Sample:
    monotonic_time: float
    value: object


def sample_until(
    probe: Callable[[], T],
    predicate: Callable[[T], bool],
    timeout_seconds: float,
    interval_seconds: float,
) -> list[Sample]:
    samples: list[Sample] = []
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        value = probe()
        samples.append(Sample(time.monotonic(), value))
        if predicate(value):
            break
        time.sleep(interval_seconds)
    return samples


def stagger(items: Iterable[T], interval_seconds: float) -> Iterable[T]:
    for item in items:
        yield item
        if interval_seconds > 0:
            time.sleep(interval_seconds)
