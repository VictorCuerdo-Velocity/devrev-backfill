from typing import Any, Optional
from datetime import datetime, timedelta

class CacheEntry:
    def __init__(self, value: Any, ttl: int):
        self.value = value
        self.expiry = datetime.now() + timedelta(seconds=ttl)

    def is_expired(self) -> bool:
        return datetime.now() > self.expiry

class Cache:
    def __init__(self, ttl: int = 3600):
        self._store = {}
        self.ttl = ttl

    def get(self, key: str) -> Optional[Any]:
        entry = self._store.get(key)
        if entry and not entry.is_expired():
            return entry.value
        if entry:
            del self._store[key]
        return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        self._store[key] = CacheEntry(value, ttl or self.ttl)

    def clear_expired(self) -> None:
        expired = [k for k, v in self._store.items() if v.is_expired()]
        for k in expired:
            del self._store[k]