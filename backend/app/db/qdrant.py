"""
Qdrant Vector Database Client & Collection Initialization.

Supports live connection to a running Qdrant instance or falls back
gracefully to an in-memory MockQdrantClient for offline/local testing.
"""

import os
import math
import logging
import hashlib
from typing import List, Dict, Any, Optional

logger = logging.getLogger("market-strategist-qdrant")

COLLECTION_NAME = "competitor_intelligence"
VECTOR_DIMENSION = 1536  # OpenAI text-embedding-3-small / ada-002 dimension


# ---------------------------------------------------------------------------
# Mock Client (used when Qdrant is not available)
# ---------------------------------------------------------------------------
class _MockPoint:
    def __init__(self, id: str, vector: List[float], payload: Dict[str, Any]):
        self.id = id
        self.vector = vector
        self.payload = payload
        self.score: float = 0.0


class MockQdrantClient:
    """
    In-memory Qdrant replacement. Supports upsert and cosine-similarity
    search with basic payload filtering by company_id.
    """

    def __init__(self):
        self._collections: Dict[str, List[_MockPoint]] = {}
        logger.warning("MockQdrantClient initialized — running in offline mode without a live Qdrant instance.")

    def recreate_collection(self, collection_name: str, vectors_config: Any):
        self._collections[collection_name] = []
        logger.info(f"[Mock] Collection '{collection_name}' created/reset.")

    def collection_exists(self, collection_name: str) -> bool:
        return collection_name in self._collections

    def upsert(self, collection_name: str, points: List[Any]):
        if collection_name not in self._collections:
            self._collections[collection_name] = []
        for point in points:
            # Remove any existing point with the same id
            self._collections[collection_name] = [
                p for p in self._collections[collection_name] if p.id != point.id
            ]
            self._collections[collection_name].append(
                _MockPoint(id=point.id, vector=point.vector, payload=point.payload)
            )
        logger.info(f"[Mock] Upserted {len(points)} points into '{collection_name}'.")

    def search(
        self,
        collection_name: str,
        query_vector: List[float],
        limit: int = 5,
        query_filter: Optional[Any] = None,
        with_payload: bool = True,
    ) -> List[_MockPoint]:
        points = self._collections.get(collection_name, [])

        # Apply simple company_id filter
        if query_filter and hasattr(query_filter, "must"):
            for condition in query_filter.must:
                if hasattr(condition, "key") and condition.key == "company_id":
                    filter_value = condition.match.value
                    points = [p for p in points if p.payload.get("company_id") == filter_value]

        # Compute cosine similarity
        def cosine(a: List[float], b: List[float]) -> float:
            dot = sum(x * y for x, y in zip(a, b))
            norm_a = math.sqrt(sum(x * x for x in a))
            norm_b = math.sqrt(sum(x * x for x in b))
            if norm_a == 0 or norm_b == 0:
                return 0.0
            return dot / (norm_a * norm_b)

        scored = []
        for p in points:
            p.score = cosine(query_vector, p.vector)
            scored.append(p)

        scored.sort(key=lambda x: x.score, reverse=True)
        return scored[:limit]


# ---------------------------------------------------------------------------
# Live Qdrant Client
# ---------------------------------------------------------------------------
def _build_live_client():
    """Try to create a live QdrantClient. Returns None on failure."""
    try:
        from qdrant_client import QdrantClient
        from app.config import settings
        url = os.getenv("QDRANT_URL", settings.QDRANT_URL)
        client = QdrantClient(url=url, timeout=5)
        # Test connectivity
        client.get_collections()
        logger.info(f"Connected to live Qdrant at {url}")
        return client
    except Exception as e:
        logger.warning(f"Could not connect to live Qdrant: {e}. Falling back to MockQdrantClient.")
        return None


# ---------------------------------------------------------------------------
# Global singleton
# ---------------------------------------------------------------------------
_client = None


def get_qdrant_client():
    """
    Returns the global Qdrant client (live or mock).
    Lazily initialized on first access.
    """
    global _client
    if _client is None:
        live = _build_live_client()
        _client = live if live is not None else MockQdrantClient()
    return _client


def init_qdrant_db():
    """
    Initialize Qdrant collections required for the platform.
    Creates the 'competitor_intelligence' collection if it does not exist.
    Safe to call multiple times (idempotent).
    """
    client = get_qdrant_client()

    try:
        if isinstance(client, MockQdrantClient):
            if not client.collection_exists(COLLECTION_NAME):
                client.recreate_collection(
                    collection_name=COLLECTION_NAME,
                    vectors_config=None,
                )
        else:
            from qdrant_client.models import VectorParams, Distance
            collections = [c.name for c in client.get_collections().collections]
            if COLLECTION_NAME not in collections:
                client.recreate_collection(
                    collection_name=COLLECTION_NAME,
                    vectors_config=VectorParams(
                        size=VECTOR_DIMENSION,
                        distance=Distance.COSINE,
                    ),
                )
                logger.info(f"Qdrant collection '{COLLECTION_NAME}' created successfully.")
            else:
                logger.info(f"Qdrant collection '{COLLECTION_NAME}' already exists.")
    except Exception as e:
        logger.error(f"Failed to initialize Qdrant collection: {e}")
        raise
