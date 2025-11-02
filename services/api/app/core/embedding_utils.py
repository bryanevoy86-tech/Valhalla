"""
Local embedding utilities for semantic search.
Provides deterministic pseudo-embeddings without external API calls.
NOT semantic quality - replace with real embedding model (OpenAI, Cohere) later.
"""

import hashlib
import math
import os
from typing import List


def _hash_f32(s: str) -> float:
    """Hash a string chunk to a float in [-1, 1]."""
    h = hashlib.sha256(s.encode("utf-8")).digest()
    # Use 4 bytes -> unsigned int -> map to [-1, 1]
    n = int.from_bytes(h[:4], "big", signed=False)
    f = (n % 2000000) / 1000000.0 - 1.0
    return max(-1.0, min(1.0, f))


def local_embed(text: str, dim: int | None = None) -> List[float]:
    """
    Cheap, deterministic pseudo-embedding for development/testing.
    
    Args:
        text: Input text to embed
        dim: Vector dimension (defaults to EMBEDDING_DIM env var or 256)
    
    Returns:
        L2-normalized float vector of length dim
    
    WARNING: This is NOT a semantic embedding! It's deterministic and position-based.
    Documents with similar text structure (not meaning) may have similar vectors.
    Replace with a real embedding model for production use.
    """
    if dim is None:
        dim = int(os.getenv("EMBEDDING_DIM", "256"))
    
    if not text:
        return [0.0] * dim
    
    # Chunk text roughly into dim segments
    step = max(1, len(text) // dim)
    vec = []
    
    for i in range(0, len(text), step):
        if len(vec) >= dim:
            break
        chunk = text[i:i+step]
        vec.append(_hash_f32(chunk))
    
    # Pad if short
    while len(vec) < dim:
        vec.append(0.0)
    
    # L2 normalize
    norm = math.sqrt(sum(x*x for x in vec)) or 1.0
    return [x / norm for x in vec[:dim]]


def embed_text(text: str) -> List[float]:
    """
    Main embedding function with provider abstraction.
    
    Args:
        text: Input text to embed
    
    Returns:
        Embedding vector as list of floats
    
    Future: Add OpenAI, Cohere, or other providers via EMBEDDING_PROVIDER setting.
    """
    provider = os.getenv("EMBEDDING_PROVIDER", "local")
    
    if provider == "local":
        return local_embed(text)
    
    # Future: plug external providers here
    # elif provider == "openai":
    #     return openai_embed(text)
    # elif provider == "cohere":
    #     return cohere_embed(text)
    
    # Fallback to local if provider not implemented
    return local_embed(text)
