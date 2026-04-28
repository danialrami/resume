"""Semantic search using ChromaDB."""

import chromadb
from chromadb.config import Settings
from typing import Optional
import uuid

from .config import DB_PATH, EMBEDDING_MODEL, get_embeddings


COLLECTION_NAME = "resume_bullets"


def get_client():
    """Get ChromaDB client."""
    return chromadb.PersistentClient(path=str(DB_PATH))


def get_or_create_collection():
    """Get or create the resume bullets collection."""
    client = get_client()
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"description": "Resume bullet points with metadata"}
    )


def add_bullet(
    bullet_id: str,
    content: str,
    company: str = "",
    category: str = "experience",
    tags: list[str] = None,
    priority: int = 5,
    pinned: bool = False
):
    """
    Add a single bullet to the database.
    
    Args:
        bullet_id: Unique identifier (e.g., "hinge_health_1")
        content: Bullet text content
        company: Company name
        category: experience|project|skill
        tags: List of tags
        priority: 1-10 priority score
        pinned: Never auto-drop
    """
    if tags is None:
        tags = []
    
    collection = get_or_create_collection()
    embedding = get_embeddings([content])[0]
    
    collection.upsert(
        ids=[bullet_id],
        embeddings=[embedding],
        documents=[content],
        metadatas=[{
            "content": content,
            "company": company,
            "category": category,
            "tags": ",".join(tags),
            "priority": priority,
            "pinned": str(pinned).lower()
        }]
    )


def search(query: str, n_results: int = 15) -> list[dict]:
    """
    Search for relevant bullets.
    
    Args:
        query: Job description text
        n_results: Number of results to return
    
    Returns:
        List of dicts with content, metadata, and distance scores
    """
    collection = get_or_create_collection()
    
    query_embedding = get_embeddings([query])[0]
    
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        include=["documents", "metadatas", "distances"]
    )
    
    formatted = []
    
    for i in range(len(results["ids"][0])):
        formatted.append({
            "id": results["ids"][0][i],
            "content": results["documents"][0][i],
            "distance": results["distances"][0][i],
            "metadata": results["metadatas"][0][i],
            "relevance_score": 1.0 - results["distances"][0][i]
        })
    
    return formatted


def delete_bullet(bullet_id: str):
    """Delete a bullet from the database."""
    collection = get_or_create_collection()
    collection.delete(ids=[bullet_id])


def clear_collection():
    """Clear all bullets (for rebuilding)."""
    try:
        client = get_client()
        client.delete_collection(name=COLLECTION_NAME)
    except Exception:
        pass


def get_all_bullets() -> list[dict]:
    """Get all bullets in the database."""
    collection = get_or_create_collection()
    
    results = collection.get(
        include=["documents", "metadatas"]
    )
    
    formatted = []
    for i in range(len(results["ids"])):
        formatted.append({
            "id": results["ids"][i],
            "content": results["documents"][i],
            "metadata": results["metadatas"][i]
        })
    
    return formatted