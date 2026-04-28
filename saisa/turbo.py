"""Turbo mode — connection pooling, response cache, and fast-path inference."""

from __future__ import annotations

import hashlib
import json
import time
from collections import OrderedDict
from dataclasses import dataclass
from typing import Any


@dataclass
class CacheEntry:
    response: str
    timestamp: float
    hits: int = 0


class ResponseCache:
    """LRU cache for identical prompts — avoids re-sending the same query."""

    def __init__(self, max_entries: int = 128, ttl_seconds: int = 600) -> None:
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._max = max_entries
        self._ttl = ttl_seconds
        self.total_hits = 0
        self.total_misses = 0

    def _key(self, messages: list[dict[str, Any]]) -> str:
        raw = json.dumps(messages, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(raw.encode()).hexdigest()[:32]

    def get(self, messages: list[dict[str, Any]]) -> str | None:
        key = self._key(messages)
        entry = self._cache.get(key)
        if entry is None:
            self.total_misses += 1
            return None
        if time.time() - entry.timestamp > self._ttl:
            del self._cache[key]
            self.total_misses += 1
            return None
        entry.hits += 1
        self.total_hits += 1
        self._cache.move_to_end(key)
        return entry.response

    def put(self, messages: list[dict[str, Any]], response: str) -> None:
        key = self._key(messages)
        self._cache[key] = CacheEntry(response=response, timestamp=time.time())
        if len(self._cache) > self._max:
            self._cache.popitem(last=False)

    def stats(self) -> dict[str, Any]:
        total = self.total_hits + self.total_misses
        return {
            "entries": len(self._cache),
            "hits": self.total_hits,
            "misses": self.total_misses,
            "hit_rate": f"{(self.total_hits / total * 100):.1f}%" if total > 0 else "N/A",
        }


class ConnectionPool:
    """Reusable httpx client pool for provider connections."""

    def __init__(self) -> None:
        self._clients: dict[str, Any] = {}

    def get_client(self, base_url: str, timeout: float = 300.0) -> Any:
        import httpx

        if base_url not in self._clients:
            self._clients[base_url] = httpx.Client(
                base_url=base_url,
                timeout=httpx.Timeout(timeout, connect=10.0),
                limits=httpx.Limits(
                    max_connections=10,
                    max_keepalive_connections=5,
                    keepalive_expiry=30.0,
                ),
                http2=False,
            )
        return self._clients[base_url]

    def close_all(self) -> None:
        for client in self._clients.values():
            try:
                client.close()
            except Exception:
                pass
        self._clients.clear()


# Global singletons
_cache = ResponseCache()
_pool = ConnectionPool()


def get_cache() -> ResponseCache:
    return _cache


def get_pool() -> ConnectionPool:
    return _pool
