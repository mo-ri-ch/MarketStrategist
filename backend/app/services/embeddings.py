"""
Embeddings Service.

Generates semantic vector embeddings for text using the OpenAI API.
Falls back to a deterministic mock embedding when the API key is unavailable,
enabling fully offline operation with consistent hash-based unit vectors.
"""

import os
import math
import hashlib
import logging
from typing import List

logger = logging.getLogger("market-strategist-embeddings")

VECTOR_DIMENSION = 1536  # Matches OpenAI text-embedding-3-small / ada-002


def generate_mock_embedding(text: str) -> List[float]:
    """
    Generate a deterministic, normalized mock embedding vector from a text string.

    Uses SHA-256 hashing to seed a reproducible set of floats, then L2-normalizes
    the result so it behaves like a real unit embedding for cosine similarity math.
    """
    seed = text.strip().lower()
    vector: List[float] = []

    for i in range(VECTOR_DIMENSION):
        chunk = f"{seed}:{i}"
        digest = hashlib.sha256(chunk.encode("utf-8")).hexdigest()
        # Convert first 8 hex chars (32 bits) to a float in (-1, 1)
        raw = int(digest[:8], 16)
        vector.append((raw / 0xFFFFFFFF) * 2 - 1)

    # L2 normalize so cosine similarity works properly
    norm = math.sqrt(sum(x * x for x in vector))
    if norm > 0:
        vector = [x / norm for x in vector]

    return vector


def get_embeddings(text: str) -> List[float]:
    """
    Generate a semantic embedding vector for the given text.

    Uses OpenAI's text-embedding-3-small model when OPENAI_API_KEY is
    set in the environment, otherwise returns a deterministic mock vector.

    Args:
        text: The input text string to embed.

    Returns:
        A list of 1536 floats representing the embedding vector.
    """
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        logger.debug("OPENAI_API_KEY not set — using mock embedding fallback.")
        return generate_mock_embedding(text)

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=text,
        )
        return response.data[0].embedding
    except Exception as e:
        logger.error(f"OpenAI embeddings API call failed: {e}. Falling back to mock embedding.")
        return generate_mock_embedding(text)


def get_embeddings_batch(texts: List[str]) -> List[List[float]]:
    """
    Generate embeddings for a list of texts in one API call (when possible).

    Args:
        texts: List of input text strings.

    Returns:
        List of embedding vectors, one per input text.
    """
    if not texts:
        return []

    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        logger.debug("OPENAI_API_KEY not set — using mock embedding fallback for batch.")
        return [generate_mock_embedding(t) for t in texts]

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=texts,
        )
        # Sort by index to preserve order
        sorted_data = sorted(response.data, key=lambda d: d.index)
        return [d.embedding for d in sorted_data]
    except Exception as e:
        logger.error(f"OpenAI batch embeddings API call failed: {e}. Falling back to mock embeddings.")
        return [generate_mock_embedding(t) for t in texts]
