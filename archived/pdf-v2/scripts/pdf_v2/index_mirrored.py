#!/usr/bin/env python3
"""Index mirrored content into ChromaDB for semantic search.

Recursively chunks website content and embeds into ChromaDB.
Supports incremental updates and full rebuilds.
Includes LLM auto-tagging with strict guardrails.
"""

import hashlib
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

import yaml
import chromadb
from chromadb.config import Settings
from dotenv import load_dotenv

load_dotenv()

# Get paths
BASE_DIR = Path(__file__).parent.parent.parent
DATA_DIR = BASE_DIR / "data"
DB_DIR = BASE_DIR / "db"
CONTENT_CACHE_DIR = DB_DIR / "content"
CHROMA_DIR = DB_DIR / "chroma"

# Chunk settings (based on RAG best practices: 400-512 tokens, ~10% overlap)
CHUNK_SIZE = 1000  # characters (~400 tokens)
CHUNK_OVERLAP = 100  # characters (~50 tokens)


def load_settings() -> dict:
    """Load scraping settings."""
    sources_path = DATA_DIR / "scraping_sources.yaml"
    if not sources_path.exists():
        return {}
    data = yaml.safe_load(sources_path.read_text())
    return data.get("settings", {})


def get_embedding(text: str) -> list[float]:
    """Get embedding for text."""
    import httpx
    
    base_url = os.getenv("LLM_BASE_URL", "http://100.89.168.11:6280/v1")
    api_key = os.getenv("LLM_API_KEY", "")
    model = os.getenv("EMBEDDING_MODEL", "embeddings")
    
    try:
        response = httpx.Client(
            base_url=base_url,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=30.0
        ).post("/embeddings", json={
            "model": model,
            "input": text
        })
        
        if response.status_code != 200:
            return None
            
        data = response.json()
        return data["data"][0]["embedding"]
    except Exception as e:
        print(f"  Embedding failed: {e}")
        return None


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Split text into overlapping chunks using recursive approach.
    
    Based on RAG best practices: 400-512 tokens with 10-20% overlap
    Using character count as proxy (~2 chars per token)
    """
    if not text:
        return []
    
    chunks = []
    separators = ["\n\n", "\n", ". ", "! ", "? ", "; ", ", ", " "]
    
    for sep in separators:
        if sep in text:
            parts = text.split(sep)
            if len(parts) > 1:
                break
    
    if len(parts) == 1:
        # No natural breaks - use fixed size
        parts = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size - overlap)]
    else:
        # Build chunks from parts, respecting size limit
        current = ""
        for part in parts:
            test = current + sep + part if current else part
            if len(test) > chunk_size:
                if current:
                    chunks.append(current.strip())
                    # Overlap - keep end of previous chunk
                    current = current[max(0, -overlap):] + sep + part
                else:
                    chunks.append(test[:chunk_size].strip())
                    current = test[max(0, chunk_size-overlap):]
            else:
                current = test
        
        if current.strip():
            chunks.append(current.strip())
    
    # Filter empty and very small chunks
    chunks = [c for c in chunks if len(c) > 50]
    
    return chunks


def extract_title_from_path(file_path: Path, content: str) -> str:
    """Extract a title from file path or content."""
    # From path
    if file_path.stem not in ["index", "content"]:
        return file_path.stem.replace("_", " ").replace("-", " ").title()
    
    # From content (first line)
    lines = content.split("\n")
    for line in lines[:5]:
        if len(line) > 10 and len(line) < 200:
            return line.strip()[:100]
    
    return "Untitled"


def create_chunk_id(domain: str, file_path: Path, chunk_index: int) -> str:
    """Create unique ID for a chunk."""
    base = f"{domain}_{file_path.stem}"
    return f"{base}_{chunk_index}"


def load_mirrored_content(domain: Optional[str] = None) -> dict:
    """Load all mirrored JSON files."""
    content_data = {}
    
    domains = [domain] if domain else [d.name for d in CONTENT_CACHE_DIR.iterdir() if d.is_dir()]
    
    for dom in domains:
        domain_dir = CONTENT_CACHE_DIR / dom
        if not domain_dir.exists():
            continue
        
        content_data[dom] = []
        
        for json_file in domain_dir.rglob("*.json"):
            # Skip special files
            if json_file.name.startswith("."):
                continue
            if json_file.name == "content.json":
                continue
            
            try:
                data = json.loads(json_file.read_text())
                content = data.get("content", "")
                url = data.get("url", "")
                
                if content and len(content) > 100:
                    content_data[dom].append({
                        "path": json_file.relative_to(CONTENT_CACHE_DIR),
                        "content": content,
                        "url": url,
                        "scraped_at": data.get("scraped_at", ""),
                        "word_count": data.get("word_count", 0),
                    })
            except Exception:
                pass
    
    return content_data


def get_existing_chunk_count(collection) -> int:
    """Get count of existing chunks."""
    try:
        return collection.count()
    except Exception:
        return 0


def llm_tag_content(content: str, jd_context: str = "") -> dict:
    """Use LLM to extract tags from content with strict guardrails.
    
    Returns: {direct_tags, transferable_tags, industries}
    """
    import httpx
    
    base_url = os.getenv("LLM_BASE_URL", "http://100:89.168.11:6280/v1")
    api_key = os.getenv("LLM_API_KEY", "")
    model = os.getenv("LLM_MODEL", "coder")
    
    system_prompt = """You are a career tagger. Your ONLY task is to extract 
    keywords from the provided text that are EXPLICITLY MENTIONED.

    RULES (STRICT):
    - Only extract keywords that ARE IN THE TEXT
    - Do NOT infer or fabricate skills not mentioned
    - Do NOT assume experience you can't verify
    - If nothing relevant, return "NONE"
    
    Output ONLY in this exact format:
    DIRECT_TAGS: [tag1, tag2, ...]
    TRANSFERABLE: [tag1, tag2, ...]
    INDUSTRIES: [tag1, tag2, ...]"""
    
    user_prompt = f"""Extract career-relevant keywords from this content:

{content[:1500]}

{'-' * 40}
Job context (for transferable matching): {jd_context[:500] if jd_context else 'None'}

Output:"""
    
    try:
        response = httpx.Client(
            base_url=base_url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            timeout=30.0
        ).post("/chat/completions", json={
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.2,
            "max_tokens": 200
        })
        
        if response.status_code != 200:
            return {"direct": [], "transferable": [], "industries": []}
        
        result = response.json()["choices"][0]["message"]["content"]
        
        tags = {"direct": [], "transferable": [], "industries": []}
        
        for line in result.split("\n"):
            line = line.strip()
            if line.startswith("DIRECT_TAGS:"):
                tags["direct"] = [t.strip() for t in line.split(":", 1)[1].split(",")][:10]
            elif line.startswith("TRANSFERABLE:"):
                tags["transferable"] = [t.strip() for t in line.split(":", 1)[1].split(",")][:10]
            elif line.startswith("INDUSTRIES:"):
                tags["industries"] = [t.strip() for t in line.split(":", 1)[1].split(",")][:10]
            
            if line == "NONE":
                return {"direct": [], "transferable": [], "industries": []}
        
        return tags
    except Exception as e:
        print(f"  LLM tagging failed: {e}")
        return {"direct": [], "transferable": [], "industries": []}


def index_content(
    domain: Optional[str] = None,
    rebuild: bool = False,
    use_llm_tags: bool = True,
    jd_context: str = ""
) -> dict:
    """Index mirrored content into ChromaDB."""
    
    # Get ChromaDB client
    chroma_client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    collection = chroma_client.get_or_create_collection(
        name="mirrored_content",
        metadata={"description": "Mirrored website content"}
    )
    
    existing_count = get_existing_chunk_count(collection)
    
    if not rebuild and existing_count > 0:
        print(f"  Already indexed: {existing_count} chunks")
        print(f"  Use --rebuild to re-index all content")
    
    # Load content
    print("\nLoading mirrored content...")
    content_data = load_mirrored_content(domain)
    
    total_chunks = 0
    indexed = 0
    tagged = 0
    
    for domain_name, files in content_data.items():
        print(f"\nProcessing {domain_name} ({len(files)} files)")
        
        for file_data in files:
            content = file_data["content"]
            file_path = file_data["path"]
            url = file_data.get("url", "")
            
            # Chunk the content
            chunks = chunk_text(content)
            print(f"  {file_path.name}: {len(chunks)} chunks")
            
            for i, chunk in enumerate(chunks):
                chunk_id = create_chunk_id(domain_name, file_path, i)
            
            for i, chunk in enumerate(chunks):
                chunk_id = create_chunk_id(domain_name, file_path, i)
                
                # Skip if exists and not rebuilding
                if not rebuild:
                    try:
                        existing = collection.get(ids=[chunk_id])
                        if existing.get("ids"):
                            total_chunks += 1
                            continue
                    except Exception:
                        pass
                
                # Get embedding
                embedding = get_embedding(chunk)
                if not embedding:
                    continue
                
                # Get LLM tags
                tags = {"direct": [], "transferable": [], "industries": []}
                if use_llm_tags:
                    tags = llm_tag_content(chunk, jd_context)
                    if tags["direct"] or tags["transferable"]:
                        tagged += 1
                
                # Determine type from path
                chunk_type = "content"
                if "posts" in str(file_path):
                    chunk_type = "post"
                elif "projects" in str(file_path):
                    chunk_type = "project"
                elif "resources" in str(file_path):
                    chunk_type = "resource"
                
                # Metadata
                metadata = {
                    "domain": domain_name,
                    "type": chunk_type,
                    "source_path": str(file_path),
                    "url": url,
                    "chunk_index": i,
                    "direct_tags": ",".join(tags["direct"]),
                    "transferable_tags": ",".join(tags["transferable"]),
                    "industries": ",".join(tags["industries"]),
                    "word_count": len(chunk.split()),
                }
                
                # Add to collection
                try:
                    collection.upsert(
                        ids=[chunk_id],
                        embeddings=[embedding],
                        documents=[chunk],
                        metadatas=[metadata]
                    )
                    indexed += 1
                except Exception as e:
                    print(f"  Failed to index {chunk_id}: {e}")
                
                total_chunks += 1
            
            print(f"  {file_path.name}: {len(chunks)} chunks")
    
    print(f"\n{'=' * 40}")
    print(f"Indexed: {indexed} new chunks")
    print(f"Total in DB: {collection.count()}")
    print(f"Auto-tagged: {tagged}")
    
    return {
        "indexed": indexed,
        "total": collection.count(),
        "tagged": tagged
    }


def search_mirrored(query: str, top_k: int = 5) -> list[dict]:
    """Search indexed content."""
    chroma_client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    collection = chroma_client.get_or_create_collection("mirrored_content")
    
    embedding = get_embedding(query)
    if not embedding:
        return []
    
    try:
        results = collection.query(
            query_embeddings=[embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"]
        )
        
        matches = []
        for i in range(len(results["ids"][0])):
            matches.append({
                "content": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i],
                "score": 1.0 - results["distances"][0][i] if results["distances"][0][i] is not None else 0
            })
        
        return matches
    except Exception:
        return []


def main():
    """CLI entry point."""
    import argparse
    parser = argparse.ArgumentParser(description="Index mirrored content")
    parser.add_argument("--domain", help="Index single domain")
    parser.add_argument("--rebuild", action="store_true", help="Rebuild index")
    parser.add_argument("--no-tags", action="store_true", help="Skip LLM tagging")
    parser.add_argument("--search", help="Search indexed content")
    parser.add_argument("--jd", help="Job description for context")
    args = parser.parse_args()
    
    print("=" * 50)
    print("Content Indexer - Mirrored to ChromaDB")
    print("=" * 50)
    print(f"Loaded API key: {os.getenv('LLM_API_KEY', '')[:10]}...")
    
    if args.search:
        print(f"\nSearching: {args.search}")
        results = search_mirrored(args.search)
        for r in results:
            print(f"\n--- Score: {r['score']:.3f} ---")
            print(f"Type: {r['metadata'].get('type')}")
            print(f"Source: {r['metadata'].get('source_path')}")
            print(f"Content: {r['content'][:200]}...")
    else:
        print("Starting indexing...")
        result = index_content(
            domain=args.domain,
            rebuild=args.rebuild,
            use_llm_tags=not args.no_tags,
            jd_context=args.jd or ""
        )
        print(f"\nDone: {result}")


if __name__ == "__main__":
    main()