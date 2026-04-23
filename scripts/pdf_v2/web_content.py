#!/usr/bin/env python3
"""Web content scraper for profile enrichment.

Scrape websites from data/scraping_sources.yaml to enrich ChromaDB.
Outputs to db/content/{domain}/ for caching.
"""

import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import requests
import yaml
from bs4 import BeautifulSoup

# Get paths from system
BASE_DIR = Path(__file__).parent.parent.parent
DATA_DIR = BASE_DIR / "data"
DB_DIR = BASE_DIR / "db"


GITHUB_API = "https://api.github.com"
CONTENT_CACHE_DIR = DB_DIR / "content"


def get_sources() -> list[dict]:
    """Load scraping sources from config."""
    sources_path = DATA_DIR / "scraping_sources.yaml"
    if not sources_path.exists():
        return []
    
    data = yaml.safe_load(sources_path.read_text())
    return [s for s in data.get("sources", []) if s.get("enabled", True)]


def get_domain(url: str) -> str:
    """Extract domain from URL for folder naming."""
    parsed = urlparse(url)
    domain = parsed.netloc or parsed.path.split("/")[0]
    return domain.replace("www.", "").replace(".", "_")


def ensure_cache_dir(domain: str) -> Path:
    """Ensure cache directory exists for domain."""
    cache_dir = CONTENT_CACHE_DIR / domain
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def is_stale(domain: str, max_age_days: int = 7) -> bool:
    """Check if cached content is stale."""
    cache_dir = CONTENT_CACHE_DIR / domain
    cache_file = cache_dir / "content.json"
    
    if not cache_file.exists():
        return True
    
    try:
        mtime = cache_file.stat().st_mtime
        age_days = (datetime.now().timestamp() - mtime) / 86400
        return age_days > max_age_days
    except Exception:
        return True


def fetch_url(url: str, timeout: int = 30) -> Optional[str]:
    """Fetch URL and return text content."""
    try:
        response = requests.get(url, timeout=timeout, headers={
            "User-Agent": "Mozilla/5.0 (compatible; ResumeBot/1.0)"
        })
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"  Failed to fetch {url}: {e}")
        return None


def extract_links_from_directory(html: str, base_url: str) -> list[str]:
    """Extract links from directory page."""
    soup = BeautifulSoup(html, "lxml")
    links = []
    
    for a in soup.find_all("a", href=True):
        href = a.get("href", "")
        if href.startswith("http"):
            links.append(href)
        elif href.startswith("/"):
            links.append(f"{base_url}{href}")
    
    return list(set(links))


def scrape_full_site(url: str, domain: str) -> dict:
    """Scrape full website content."""
    html = fetch_url(url)
    if not html:
        return {}
    
    soup = BeautifulSoup(html, "lxml")
    
    # Remove unwanted elements
    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()
    
    # Extract text content
    text = soup.get_text(separator="\n", strip=True)
    
    # Clean up text
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    text = "\n".join(lines)
    
    # Basic metadata
    meta = {
        "url": url,
        "domain": domain,
        "scraped_at": datetime.now().isoformat(),
        "word_count": len(text.split()),
    }
    
    return {
        "meta": meta,
        "content": text,
        "url": url,
    }


def scrape_github(username: str) -> dict:
    """Scrape GitHub using public API."""
    try:
        response = requests.get(
            f"{GITHUB_API}/users/{username}/repos",
            params={"sort": "updated", "per_page": 20},
            timeout=30
        )
        response.raise_for_status()
        repos = response.json()
    except Exception as e:
        print(f"  GitHub API failed: {e}")
        return {}
    
    repo_data = []
    for repo in repos:
        repo_data.append({
            "name": repo.get("name"),
            "description": repo.get("description"),
            "language": repo.get("language"),
            "topics": repo.get("topics", []),
            "stars": repo.get("stargazers_count", 0),
            "url": repo.get("html_url"),
            "updated": repo.get("updated_at"),
        })
    
    meta = {
        "url": f"https://github.com/{username}",
        "domain": get_domain(f"https://github.com/{username}"),
        "scraped_at": datetime.now().isoformat(),
        "repo_count": len(repo_data),
    }
    
    content_lines = []
    for repo in repo_data:
        lines = [f"## {repo['name']}"]
        if repo.get("description"):
            lines.append(f"  {repo['description']}")
        if repo.get("language"):
            lines.append(f"  Language: {repo['language']}")
        if repo.get("topics"):
            lines.append(f"  Topics: {', '.join(repo['topics'])}")
        if repo.get("stars"):
            lines.append(f"  Stars: {repo['stars']}")
        content_lines.append("\n".join(lines))
    
    return {
        "meta": meta,
        "content": "\n\n".join(content_lines),
        "repositories": repo_data,
    }


def scrape_all(force: bool = False) -> dict:
    """Scrape all enabled sources."""
    sources = get_sources()
    results = {}
    
    for source in sources:
        url = source["url"]
        source_type = source.get("type", "website")
        domain = get_domain(url)
        
        print(f"\nScraping: {url} ({source_type})")
        
        # Check if stale (skip if not forcing and content is fresh)
        if not force and not is_stale(domain):
            print(f"  Skipping - content is fresh")
            continue
        
        cache_dir = ensure_cache_dir(domain)
        scraped_data = {}
        
        if source_type == "directory":
            # Parse directory to get subsites
            html = fetch_url(url)
            if html:
                links = extract_links_from_directory(html, url)
                scraped_data = {
                    "meta": {
                        "url": url,
                        "domain": domain,
                        "scraped_at": datetime.now().isoformat(),
                        "links_discovered": len(links),
                    },
                    "content": f"Found {len(links)} linked sites:\n" + "\n".join(f"- {l}" for l in links),
                    "discovered_links": links,
                }
                
        elif source_type == "github":
            # GitHub uses API
            username = url.split("/")[-1]
            scraped_data = scrape_github(username)
        
        else:
            # Regular website
            scraped_data = scrape_full_site(url, domain)
        
        # Save to cache
        if scraped_data:
            cache_file = cache_dir / "content.json"
            cache_file.write_text(json.dumps(scraped_data, indent=2))
            print(f"  Saved to {cache_dir.name}/ ({scraped_data.get('meta', {}).get('word_count', 0)} words)")
            results[domain] = scraped_data
        else:
            print(f"  No content scraped")
    
    return results


def get_scraped_content(domain: Optional[str] = None) -> list[dict]:
    """Get all scraped content, optionally filtered by domain."""
    if not CONTENT_CACHE_DIR.exists():
        return []
    
    results = []
    for subdir in CONTENT_CACHE_DIR.iterdir():
        if subdir.is_dir():
            if domain and subdir.name != domain:
                continue
            
            content_file = subdir / "content.json"
            if content_file.exists():
                try:
                    data = json.loads(content_file.read_text())
                    results.append(data)
                except Exception:
                    pass
    
    return results


def extract_all_text() -> str:
    """Get all scraped text combined."""
    content = get_scraped_content()
    texts = []
    for c in content:
        if c.get("content"):
            texts.append(c["content"])
    return "\n\n---\n\n".join(texts)


def main():
    """CLI entry point."""
    import argparse
    parser = argparse.ArgumentParser(description="Scrape web content for profile")
    parser.add_argument("--force", action="store_true", help="Force re-scraping")
    args = parser.parse_args()
    
    print("=" * 50)
    print("Web Content Scraper")
    print("=" * 50)
    
    results = scrape_all(force=args.force)
    
    total_words = sum(
        c.get("meta", {}).get("word_count", 0) 
        for c in results.values()
    )
    print(f"\nTotal: {len(results)} sites, {total_words} words")


if __name__ == "__main__":
    main()