"""Simple in-memory cache with TTL to avoid hammering basketball-reference.com."""

import time
from typing import Any


class Cache:
    def __init__(self, ttl_seconds: int = 3600):
        self._store: dict[str, tuple[Any, float]] = {}
        self._ttl = ttl_seconds

    def get(self, key: str) -> Any | None:
        if key in self._store:
            value, timestamp = self._store[key]
            if time.time() - timestamp < self._ttl:
                return value
            del self._store[key]
        return None

    def set(self, key: str, value: Any) -> None:
        self._store[key] = (value, time.time())

    def clear(self) -> None:
        self._store.clear()
