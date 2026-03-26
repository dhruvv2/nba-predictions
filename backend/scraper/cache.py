"""In-memory cache with TTL + persistent disk cache for historical (past-season) data."""

import json
import os
import time
from typing import Any

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")


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


class DiskCache:
    """Persistent JSON cache for data that doesn't change (past seasons)."""

    def __init__(self):
        os.makedirs(DATA_DIR, exist_ok=True)

    def _path(self, key: str) -> str:
        safe_key = key.replace("/", "_").replace("\\", "_")
        return os.path.join(DATA_DIR, f"{safe_key}.json")

    def get(self, key: str) -> Any | None:
        path = self._path(key)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return None

    def set(self, key: str, value: Any) -> None:
        path = self._path(key)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(value, f)

    def has(self, key: str) -> bool:
        return os.path.exists(self._path(key))
