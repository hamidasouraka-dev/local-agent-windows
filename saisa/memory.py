"""Persistent memory system — lightweight JSON-based learning memory.

No heavy dependencies (no vector DB). Uses TF-IDF-like scoring for retrieval.
Stores learnings, project context, and user preferences across sessions.
"""

from __future__ import annotations

import json
import math
import re
import time
from collections import Counter
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

MEMORY_DIR = Path.home() / ".saisa" / "memory"


@dataclass
class MemoryEntry:
    id: str
    category: str  # "learning", "context", "preference", "error", "success"
    content: str
    tags: list[str] = field(default_factory=list)
    timestamp: float = 0.0
    relevance_score: float = 0.0
    access_count: int = 0

    def __post_init__(self) -> None:
        if self.timestamp == 0.0:
            self.timestamp = time.time()


class Memory:
    """JSON-based persistent memory with TF-IDF retrieval."""

    def __init__(self, memory_dir: Path | None = None) -> None:
        self._dir = memory_dir or MEMORY_DIR
        self._dir.mkdir(parents=True, exist_ok=True)
        self._index_path = self._dir / "index.json"
        self._entries: dict[str, MemoryEntry] = {}
        self._load()

    def _load(self) -> None:
        if self._index_path.exists():
            try:
                raw = json.loads(self._index_path.read_text(encoding="utf-8"))
                for entry_data in raw.get("entries", []):
                    entry = MemoryEntry(**entry_data)
                    self._entries[entry.id] = entry
            except Exception:
                pass

    def _save(self) -> None:
        data = {"entries": [asdict(e) for e in self._entries.values()]}
        self._index_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def store(self, category: str, content: str, tags: list[str] | None = None) -> str:
        """Store a memory entry. Returns the entry ID."""
        entry_id = f"mem_{int(time.time() * 1000)}"
        entry = MemoryEntry(
            id=entry_id,
            category=category,
            content=content,
            tags=tags or [],
        )
        self._entries[entry_id] = entry
        self._save()
        return entry_id

    def recall(self, query: str, top_k: int = 5, category: str | None = None) -> list[MemoryEntry]:
        """Retrieve the most relevant memories for a query."""
        query_tokens = _tokenize(query)
        if not query_tokens:
            return []

        scored: list[tuple[float, MemoryEntry]] = []
        for entry in self._entries.values():
            if category and entry.category != category:
                continue
            score = _similarity(query_tokens, _tokenize(entry.content))
            # boost by tag match
            for tag in entry.tags:
                if tag.lower() in query.lower():
                    score += 0.3
            # recency boost (newer = slightly higher)
            age_days = (time.time() - entry.timestamp) / 86400
            recency = 1.0 / (1.0 + math.log1p(age_days))
            score += recency * 0.1
            scored.append((score, entry))

        scored.sort(key=lambda x: x[0], reverse=True)
        results = []
        for score, entry in scored[:top_k]:
            if score > 0.05:
                entry.access_count += 1
                entry.relevance_score = score
                results.append(entry)

        if results:
            self._save()
        return results

    def forget(self, entry_id: str) -> bool:
        """Delete a specific memory."""
        if entry_id in self._entries:
            del self._entries[entry_id]
            self._save()
            return True
        return False

    def forget_category(self, category: str) -> int:
        """Delete all memories in a category."""
        to_delete = [eid for eid, e in self._entries.items() if e.category == category]
        for eid in to_delete:
            del self._entries[eid]
        if to_delete:
            self._save()
        return len(to_delete)

    def list_all(self, category: str | None = None, limit: int = 50) -> list[MemoryEntry]:
        """List stored memories."""
        entries = list(self._entries.values())
        if category:
            entries = [e for e in entries if e.category == category]
        entries.sort(key=lambda e: e.timestamp, reverse=True)
        return entries[:limit]

    @property
    def count(self) -> int:
        return len(self._entries)

    def stats(self) -> dict[str, Any]:
        categories = Counter(e.category for e in self._entries.values())
        return {
            "total_entries": len(self._entries),
            "categories": dict(categories),
            "memory_dir": str(self._dir),
        }


def _tokenize(text: str) -> list[str]:
    """Simple whitespace + punctuation tokenizer."""
    return [t.lower() for t in re.findall(r"\w+", text) if len(t) > 2]


def _similarity(query_tokens: list[str], doc_tokens: list[str]) -> float:
    """Simple TF-IDF-like cosine similarity."""
    if not doc_tokens:
        return 0.0
    query_set = set(query_tokens)
    doc_counter = Counter(doc_tokens)
    doc_len = len(doc_tokens)

    overlap = 0.0
    for token in query_set:
        if token in doc_counter:
            tf = doc_counter[token] / doc_len
            overlap += tf

    if overlap == 0:
        return 0.0
    return overlap / (math.sqrt(len(query_set)) * math.sqrt(len(set(doc_tokens))))
