# Copyright 2026 Luis Gustavo Vaz <me@rastrian.dev>
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

from __future__ import annotations

import time


class _BucketState:
    __slots__ = ("remaining", "reset_at")

    def __init__(self, remaining: int, reset_at: float) -> None:
        self.remaining = remaining
        self.reset_at = reset_at


class RateLimitTracker:
    def __init__(self) -> None:
        self._buckets: dict[str, _BucketState] = {}

    def update(self, bucket: str, remaining: int, reset_at: float) -> None:
        self._buckets[bucket] = _BucketState(remaining=remaining, reset_at=reset_at)

    def is_limited(self, bucket: str) -> bool:
        state = self._buckets.get(bucket)
        if state is None:
            return False
        if state.remaining <= 0 and time.monotonic() < state.reset_at:
            return True
        return False

    def wait_time(self, bucket: str) -> float:
        state = self._buckets.get(bucket)
        if state is None:
            return 0.0
        remaining = state.reset_at - time.monotonic()
        return max(0.0, remaining)
