#!/usr/bin/env python3
"""Application history - track generated resumes and applications.

Uses ChromaDB to store:
- Job URL, title, date applied
- Generated PDF path
- Match score from semantic search
- Status: applied/interested/not-fit
- Notes for follow-up

Provides semantic search over past applications to:
- Detect duplicate applications
- Find similar past applications
- Analyze application patterns
"""

import hashlib
import os
from datetime import datetime
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

import yaml
import chromadb
from chromadb.config import Settings

load_dotenv()

# Get paths
BASE_DIR = Path(__file__).parent.parent.parent
DATA_DIR = BASE_DIR / "data"
DB_DIR = BASE_DIR / "db"

LLM_BASE_URL = os.getenv("LLM_BASE_URL")
LLM_API_KEY = os.getenv("LLM_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")


HISTORY_DB_DIR = DB_DIR / "history"


def ensure_history_dir():
    """Ensure history directory exists."""
    HISTORY_DB_DIR.mkdir(parents=True, exist_ok=True)


def get_history_client() -> chromadb.PersistentClient:
    """Get ChromaDB client for history."""
    ensure_history_dir()
    return chromadb.PersistentClient(path=str(HISTORY_DB_DIR))


def get_history_collection():
    """Get or create history collection."""
    client = get_history_client()
    return client.get_or_create_collection(
        name="application_history",
        metadata={"description": "Resume applications and generated PDFs"}
    )


def hash_url(url: str) -> str:
    """Generate hash for job URL."""
    return hashlib.sha256(url.encode()).hexdigest()[:16]


def add_application(
    job_url: str,
    job_title: str = "",
    pdf_path: str = "",
    match_score: float = 0.0,
    status: str = "applied",
    notes: str = ""
) -> bool:
    """Log a new application."""
    
    collection = get_history_collection()
    
    app_id = hash_url(job_url)
    applied_date = datetime.now().isoformat()
    
    metadata = {
        "job_url": job_url,
        "job_title": job_title,
        "applied_date": applied_date,
        "pdf_path": pdf_path,
        "match_score": match_score,
        "status": status,
        "notes": notes,
    }
    
    # Add embedding for semantic search if we have content
    content = f"{job_title} {job_url}"
    try:
        embedding = get_embeddings([content])[0]
    except Exception:
        embedding = None
    
    try:
        collection.upsert(
            ids=[app_id],
            documents=[content],
            embeddings=[embedding] if embedding else None,
            metadatas=[metadata]
        )
        return True
    except Exception as e:
        print(f"  Failed to add application: {e}")
        return False


def check_application(job_url: str) -> Optional[dict]:
    """Check if already applied to a job."""
    
    collection = get_history_collection()
    app_id = hash_url(job_url)
    
    try:
        result = collection.get(ids=[app_id])
        if result.get("ids") and result["ids"]:
            return {
                "job_url": result["metadatas"][0].get("job_url"),
                "job_title": result["metadatas"][0].get("job_title"),
                "applied_date": result["metadatas"][0].get("applied_date"),
                "match_score": result["metadatas"][0].get("match_score"),
                "status": result["metadatas"][0].get("status"),
                "pdf_path": result["metadatas"][0].get("pdf_path"),
            }
    except Exception:
        pass
    
    return None


def update_status(job_url: str, status: str, notes: str = "") -> bool:
    """Update application status."""
    
    existing = check_application(job_url)
    if not existing:
        return False
    
    # Remove and re-add with new status
    collection = get_history_collection()
    app_id = hash_url(job_url)
    
    try:
        collection.delete(ids=[app_id])
        
        metadata = {
            "job_url": job_url,
            "job_title": existing.get("job_title", ""),
            "applied_date": existing.get("applied_date", ""),
            "pdf_path": existing.get("pdf_path", ""),
            "match_score": existing.get("match_score", 0.0),
            "status": status,
            "notes": notes,
        }
        
        collection.upsert(
            ids=[app_id],
            documents=[existing.get("job_title", job_url)],
            metadatas=[metadata]
        )
        return True
    except Exception as e:
        print(f"  Failed to update status: {e}")
        return False


def find_similar_jobs(query: str, top_k: int = 5) -> list[dict]:
    """Find similar past applications by semantic search."""
    
    collection = get_history_collection()
    
    try:
        embedding = get_embeddings([query])[0]
    except Exception:
        return []
    
    try:
        results = collection.query(
            query_embeddings=[embedding],
            n_results=top_k,
            include=["metadatas", "distances"]
        )
        
        similar = []
        for i in range(len(results.get("ids", [[]])[0])):
            similar.append({
                "job_url": results["metadatas"][0][i].get("job_url"),
                "job_title": results["metadatas"][0][i].get("job_title"),
                "applied_date": results["metadatas"][0][i].get("applied_date"),
                "status": results["metadatas"][0][i].get("status"),
                "similarity": 1.0 - results["distances"][0][i],
            })
        
        return similar
    except Exception:
        return []


def list_applications(status: Optional[str] = None, limit: int = 20) -> list[dict]:
    """List all applications."""
    
    collection = get_history_collection()
    
    try:
        results = collection.get(include=["metadatas"])
        
        apps = []
        for i in range(len(results.get("ids", []))):
            app = {
                "job_url": results["metadatas"][i].get("job_url"),
                "job_title": results["metadatas"][i].get("job_title"),
                "applied_date": results["metadatas"][i].get("applied_date"),
                "status": results["metadatas"][i].get("status"),
                "match_score": results["metadatas"][i].get("match_score"),
            }
            
            if status is None or app["status"] == status:
                apps.append(app)
            
            if len(apps) >= limit:
                break
        
        return apps
    except Exception:
        return []


def get_stats() -> dict:
    """Get application statistics."""
    apps = list_applications(limit=1000)
    
    return {
        "total": len(apps),
        "applied": sum(1 for a in apps if a.get("status") == "applied"),
        "interested": sum(1 for a in apps if a.get("status") == "interested"),
        "not_fit": sum(1 for a in apps if a.get("status") == "not-fit"),
    }


def main():
    """CLI entry point."""
    import argparse
    parser = argparse.ArgumentParser(description="Application history")
    
    subparsers = parser.add_subparsers(dest="command")
    
    # Check command
    check_parser = subparsers.add_parser("check", help="Check if applied")
    check_parser.add_argument("url", help="Job URL")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List applications")
    list_parser.add_argument("--status", help="Filter by status")
    list_parser.add_argument("--limit", type=int, default=20)
    
    # Stats command
    subparsers.add_parser("stats", help="Show statistics")
    
    # Update command
    update_parser = subparsers.add_parser("update", help="Update status")
    update_parser.add_argument("url", help="Job URL")
    update_parser.add_argument("status", help="Status: applied/interested/not-fit")
    update_parser.add_argument("--notes", default="")
    
    args = parser.parse_args()
    
    print("=" * 50)
    print("Application History")
    print("=" * 50)
    
    if args.command == "check":
        result = check_application(args.url)
        if result:
            print(f"\nAlready applied!")
            print(f"  Title: {result.get('job_title')}")
            print(f"  Date: {result.get('applied_date')}")
            print(f"  Score: {result.get('match_score')}")
            print(f"  Status: {result.get('status')}")
        else:
            print("\nNot previously applied")
    
    elif args.command == "list":
        apps = list_applications(status=args.status, limit=args.limit)
        print(f"\n{lenapps} applications")
        for app in apps:
            print(f"  - {app.get('job_title', 'Untitled')}")
            print(f"    {app.get('job_url')}")
            print(f"    Status: {app.get('status')} | Score: {app.get('match_score')}")
    
    elif args.command == "stats":
        stats = get_stats()
        print(f"\nStatistics:")
        print(f"  Total: {stats['total']}")
        print(f"  Applied: {stats['applied']}")
        print(f"  Interested: {stats['interested']}")
        print(f"  Not Fit: {stats['not_fit']}")
    
    elif args.command == "update":
        success = update_status(args.url, args.status, args.notes)
        if success:
            print(f"Updated status to: {args.status}")
        else:
            print("Failed to update")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()