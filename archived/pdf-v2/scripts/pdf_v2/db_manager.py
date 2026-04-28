"""Database manager for ChromaDB."""

import yaml
from pathlib import Path
import uuid
from typing import Optional

from .config import BASE_DIR, DATA_DIR
from .semantic_search import (
    get_client,
    clear_collection,
    add_bullet,
)


def get_data_path() -> Path:
    """Get path to resume.yaml."""
    data_path = DATA_DIR / "resume.yaml"
    if not data_path.exists():
        data_path = BASE_DIR / "data" / "resume.yaml"
    return data_path


def load_yaml() -> dict:
    """Load resume data from YAML."""
    data_path = get_data_path()
    return yaml.safe_load(data_path.read_text())


def generate_bullet_id(company: str, index: int, category: str = "experience") -> str:
    """Generate unique bullet ID."""
    company_slug = company.lower().replace(" ", "_")
    return f"{company_slug}_{category}_{index}"


def init_db():
    """Initialize database with schema."""
    get_client()
    print("Database initialized.")


def rebuild_db():
    """Rebuild database from YAML."""
    clear_collection()
    
    data = load_yaml()
    
    bullet_count = 0
    
    for exp in data.get("experience", []):
        company = exp.get("company", "")
        role = exp.get("role", "")
        dates = exp.get("dates", "")
        
        bullets = exp.get("description", [])
        
        if isinstance(bullets, list):
            for i, bullet in enumerate(bullets):
                if isinstance(bullet, str):
                    content = bullet
                elif isinstance(bullet, dict):
                    content = bullet.get("content", "")
                else:
                    content = str(bullet)
                
                bullet_id = generate_bullet_id(company, i)
                tags = extract_tags(content)
                priority = 5
                
                if isinstance(bullet, dict):
                    priority = bullet.get("priority", 5)
                
                add_bullet(
                    bullet_id=bullet_id,
                    content=content,
                    company=company,
                    category="experience",
                    tags=tags,
                    priority=priority,
                    pinned=False
                )
                bullet_count += 1
    
    for proj in data.get("projects", []):
        name = proj.get("name", "")
        description = proj.get("description", [])
        
        if isinstance(description, list):
            for i, desc in enumerate(description):
                if isinstance(desc, str):
                    content = desc
                elif isinstance(desc, dict):
                    content = desc.get("content", "")
                else:
                    content = str(desc)
                
                bullet_id = f"project_{name.lower().replace(' ', '_')}_{i}"
                tags = extract_tags(content)
                priority = 5
                
                if isinstance(desc, dict):
                    priority = desc.get("priority", 5)
                
                add_bullet(
                    bullet_id=bullet_id,
                    content=content,
                    company=name,
                    category="project",
                    tags=tags,
                    priority=priority,
                    pinned=False
                )
                bullet_count += 1
    
    print(f"Database rebuilt: {bullet_count} bullets indexed")


def extract_tags(content: str) -> list[str]:
    """Extract keywords as tags from content."""
    import re
    
    words = re.findall(r"\b[A-Za-z][A-Za-z0-9+#]+\b", content.lower())
    
    stopwords = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", 
                "for", "of", "with", "by", "from", "as", "is", "are", "was",
                "have", "has", "had", "do", "does", "did", "will", "would",
                "this", "that", "these", "those", "you", "your"}
    
    tech_terms = {"python", "lua", "wwise", "fmod", "unity", "unreal", "aws",
                  "gcp", "azure", "react", "node", "javascript", "typescript",
                  "sql", "nosql", "docker", "kubernetes", "api", "rest",
                  "graphql", "kafka", "rabbitmq", "redis", "postgres",
                  "mongodb", "elasticsearch", "kinesis", "s3", "lambda"}
    
    tags = []
    for word in words:
        if word in tech_terms or len(word) > 3:
            if word not in stopwords:
                tags.append(word)
    
    return list(set(tags))[:15]


def add_single_bullet(
    content: str,
    company: str,
    category: str = "experience",
    tags: list = None,
    priority: int = 5,
    pinned: bool = False
):
    """Add a single bullet manually."""
    bullet_id = f"manual_{uuid.uuid4().hex[:8]}"
    
    add_bullet(
        bullet_id=bullet_id,
        content=content,
        company=company,
        category=category,
        tags=tags or [],
        priority=priority,
        pinned=pinned
    )
    
    print(f"Added bullet: {bullet_id}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "rebuild":
        rebuild_db()
    else:
        init_db()
        print("Run 'python -m scripts.pdf_v2.db_manager rebuild' to index bullets")