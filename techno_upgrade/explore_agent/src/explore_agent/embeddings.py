"""Embedding and RAG utilities for explore agent."""

import hashlib
import math
import os
import time
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence


Vector = Sequence[float]

_ENABLE_LANCEDB = os.environ.get("EXPLORE_AGENT_ENABLE_LANCEDB") == "1"
_ENABLE_SENTENCE_TRANSFORMER = (
    os.environ.get("EXPLORE_AGENT_ENABLE_SENTENCE_TRANSFORMER") == "1"
)

MAX_TEMP_RAG_ENTRIES = 1_000


def _normalize_vector(values: Iterable[float]) -> List[float]:
    vector = [float(v) for v in values]
    norm = math.sqrt(sum(v * v for v in vector)) or 1.0
    return [v / norm for v in vector]


def _hash_embedding(text: str, dims: int = 16) -> List[float]:
    """Deterministic fallback embedding that does not require external deps."""
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    chunk_size = max(1, len(digest) // dims)
    values = []
    for idx in range(dims):
        start = idx * chunk_size
        chunk = digest[start : start + chunk_size] or digest
        values.append(float(int.from_bytes(chunk, "big")))
    return _normalize_vector(values)


def create_embedding_fn() -> Callable[[str], Vector]:
    """Prefer SentenceTransformer embeddings, fallback to hash-based."""
    if not _ENABLE_SENTENCE_TRANSFORMER:
        return _hash_embedding

    try:  # pragma: no cover - dependent on runtime availability
        from sentence_transformers import SentenceTransformer  # type: ignore

        model = SentenceTransformer("all-MiniLM-L6-v2")
    except Exception:
        return _hash_embedding

    def embed(text: str) -> Vector:
        vector = model.encode([text])[0]
        return _normalize_vector(vector.tolist())

    return embed


class _TempRAGStore:
    """In-memory similarity store with optional LanceDB backing."""

    def __init__(
        self,
        embed_fn: Callable[[str], Vector],
        similarity_threshold: float,
        max_entries: int = MAX_TEMP_RAG_ENTRIES,
    ):
        self._embed = embed_fn
        self._threshold = similarity_threshold
        self.backend = "fallback"
        self._entries: List[Dict[str, Any]] = []
        self._db = None
        self._table = None
        self._max_entries = max(1, max_entries)
        if _ENABLE_LANCEDB:
            self.backend = "lancedb"
            self._initialise_lancedb()

    def _initialise_lancedb(self) -> None:
        """Create an in-memory LanceDB table if dependency is available."""
        try:
            import lancedb  # type: ignore

            self._db = lancedb.connect(":memory:")
            # Lazy table creation; we only add rows via add()
            self._table = self._db.create_table(
                "explore_findings",
                data=[],
                mode="overwrite",
            )
        except Exception:  # pragma: no cover - LanceDB optional and heavy
            self.backend = "fallback"
            self._db = None
            self._table = None

    def reset(self) -> None:
        self._entries.clear()
        if self.backend == "lancedb" and self._db is not None:
            try:  # pragma: no cover - optional dependency
                self._table = self._db.create_table(
                    "explore_findings",
                    data=[],
                    mode="overwrite",
                )
            except Exception:
                self.backend = "fallback"
                self._table = None

    def add(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        if not text.strip():
            return
        try:
            vector = self._embed(text)
        except Exception:
            return
        payload = {
            "text": text,
            "vector": vector,
            "metadata": metadata or {},
            "timestamp": time.time(),
        }
        self._entries.append(payload)
        if len(self._entries) > self._max_entries:
            self._entries.pop(0)

        if self.backend == "lancedb" and self._table is not None:
            try:  # pragma: no cover - exercised when dependency available
                self._table.add([payload])
            except Exception:
                # If the LanceDB row fails, we still have the fallback store.
                self.backend = "fallback"

    def query(self, text: str, k: int = 3) -> List[Dict[str, Any]]:
        if not text.strip():
            return []

        try:
            vector = self._embed(text)
        except Exception:
            return []
        matches: List[Dict[str, Any]] = []

        for entry in self._entries:
            similarity = self._cosine_similarity(vector, entry["vector"])
            if similarity >= self._threshold:
                matches.append(
                    {
                        "text": entry["text"],
                        "metadata": entry["metadata"],
                        "similarity": similarity,
                    }
                )

        matches.sort(key=lambda item: item["similarity"], reverse=True)
        return matches[:k]

    @staticmethod
    def _cosine_similarity(lhs: Vector, rhs: Vector) -> float:
        numerator = sum(float(x) * float(y) for x, y in zip(lhs, rhs, strict=False))
        lhs_norm = math.sqrt(sum(float(x) * float(x) for x in lhs)) or 1.0
        rhs_norm = math.sqrt(sum(float(y) * float(y) for y in rhs)) or 1.0
        return numerator / (lhs_norm * rhs_norm)

    @property
    def similarity_threshold(self) -> float:
        return self._threshold


__all__ = [
    "Vector",
    "_TempRAGStore",
    "_normalize_vector",
    "_hash_embedding",
    "create_embedding_fn",
    "MAX_TEMP_RAG_ENTRIES",
]
