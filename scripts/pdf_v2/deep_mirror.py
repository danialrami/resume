#!/usr/bin/env python3
"""Deep Mirror - Recursive website mirroring.

Mirrors complete website content into structured JSON files.
Uses BFS queue-based crawling with configurable depth limits.
"""

import hashlib
import json
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Optional
from urllib.parse import urljoin, urlparse

import requests
import yaml
from bs4 import BeautifulSoup
from urllib3.exceptions import InsecureRequestWarning

# Suppress InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

BASE_DIR = Path(__file__).parent.parent.parent
DATA_DIR = BASE_DIR / "data"
DB_DIR = BASE_DIR / "db"
CONTENT_CACHE_DIR = DB_DIR / "content"


def load_settings() -> dict:
    """Load scraping settings."""
    sources_path = DATA_DIR / "scraping_sources.yaml"
    if not sources_path.exists():
        return {}
    data = yaml.safe_load(sources_path.read_text())
    return data.get("settings", {})


def load_sources() -> list[dict]:
    """Load scraping sources."""
    sources_path = DATA_DIR / "scraping_sources.yaml"
    if not sources_path.exists():
        return []
    data = yaml.safe_load(sources_path.read_text())
    return [s for s in data.get("sources", []) if s.get("enabled", True)]


def get_domain(url: str) -> str:
    """Extract domain for folder naming."""
    parsed = urlparse(url)
    domain = parsed.netloc or parsed.path.split("/")[0]
    return domain.replace("www.", "").replace(".", "_")


def ensure_domain_dir(domain: str) -> Path:
    """Ensure domain folder exists."""
    domain_dir = CONTENT_CACHE_DIR / domain
    domain_dir.mkdir(parents=True, exist_ok=True)
    return domain_dir


def should_exclude(url: str, exclude_patterns: list) -> bool:
    """Check if URL matches exclude patterns."""
    for pattern in exclude_patterns:
        if re.search(pattern, url):
            return True
    return False


def normalize_url(url: str, base_url: str = "") -> str:
    """Normalize and clean URL."""
    if not url:
        return ""
    # Handle relative URLs
    if url.startswith("/"):
        url = base_url + url
    elif url.startswith("./"):
        url = base_url + url[1:]
    # Remove fragments
    if "#" in url:
        url = url.split("#")[0]
    # Remove trailing slashes for consistency
    url = url.rstrip("/")
    if url and not url.startswith("http"):
        return ""
    return url


def extract_links(html: str, base_url: str, domain: str) -> list[str]:
    """Extract all internal links from HTML."""
    soup = BeautifulSoup(html, "lxml")
    links = []
    
    for a in soup.find_all("a", href=True):
        href = a.get("href", "")
        href = normalize_url(href, base_url)
        if not href:
            continue
        # Only same domain links
        parsed = urlparse(href)
        if parsed.netloc and domain in get_domain(href):
            links.append(href)
        elif not parsed.netloc:
            # Relative link on same domain
            links.append(href)
    
    return list(set(links))


def extract_main_content(html: str) -> str:
    """Extract main content, removing nav/footer/scripts."""
    soup = BeautifulSoup(html, "lxml")
    
    # Remove unwanted elements
    for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form", "iframe"]):
        tag.decompose()
    
    # Try common content containers
    content = None
    for selector in ["main", "article", "[role='main']", ".content", "#content", ".post-content", ".article-content"]:
        content = soup.select_one(selector)
        if content and len(content.get_text(strip=True)) > 100:
            break
    
    # Fallback to body
    if not content:
        body = soup.find("body")
        if body:
            content = body
    
    if not content:
        return ""
    
    # Clean and extract text
    text = content.get_text(separator="\n", strip=True)
    
    # Remove excessive whitespace
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    text = "\n".join(lines)
    
    return text[:50000] if text else ""  # Limit to 50k chars


def fetch_page(url: str, timeout: int = 30) -> Optional[tuple[str, int]]:
    """Fetch a single page. Returns (html, status_code) or None on failure."""
    try:
        response = requests.get(
            url,
            timeout=timeout,
            headers={"User-Agent": "Mozilla/5.0 (compatible; ResumeBot/1.0)"},
            verify=False
        )
        response.raise_for_status()
        return response.text, response.status_code
    except Exception as e:
        print(f"  Failed to fetch {url}: {e}")
        return None


def get_path_from_url(url: str, base_url: str) -> Path:
    """Convert URL to file path within domain folder."""
    parsed = urlparse(url)
    base = urlparse(base_url)
    
    # Get path, remove base path, add .json
    path = parsed.path
    if path == "/" or not path:
        path = "/index"
    else:
        path = path.rstrip("/")
    
    # Remove leading base path
    if base.path != "/":
        if path.startswith(base.path):
            path = path[len(base.path):]
    
    # Handle query strings - convert to clean paths
    if parsed.query:
        # Convert query to file-friendly name
        path = path + "_" + re.sub(r'[^\w\-_]', '_', parsed.query)
    
    # Ensure .json extension
    if not path.endswith(".json"):
        path = path + ".json"
    
    # Clean path
    path = re.sub(r'/+', '/', path)
    
    return Path(path.lstrip("/"))


def mirror_site(
    base_url: str,
    domain: str,
    max_depth: int = 3,
    exclude_patterns: list = None,
    rate_limit: float = 1.5,
    resume: bool = False
) -> dict:
    """Mirror a website deeply using BFS."""
    
    exclude_patterns = exclude_patterns or []
    domain_dir = ensure_domain_dir(domain)
    
    # Track visited URLs
    visited_file = domain_dir / ".visited.json"
    visited = set()
    if resume and visited_file.exists():
        try:
            visited = set(json.loads(visited_file.read_text()))
            print(f"  Resuming - {len(visited)} already visited")
        except Exception:
            pass
    
    # Known URLs queue (BFS)
    queue = [(base_url, 0)]  # (url, depth)
    pages_saved = 0
    pages_failed = 0
    
    print(f"\nMirroring {base_url} (max_depth={max_depth})")
    print(f"  Domain: {domain}")
    
    base_domain = get_domain(base_url)
    
    while queue:
        url, depth = queue.pop(0)
        
        # Check if already visited
        if url in visited:
            continue
        
        # Check depth limit
        if depth > max_depth:
            print(f"  Skipping (depth {depth} > {max_depth}): {url}")
            continue
        
        # Check exclude patterns
        if should_exclude(url, exclude_patterns):
            print(f"  Excluding: {url}")
            visited.add(url)
            continue
        
        # Mark as visited
        visited.add(url)
        
        # Rate limit
        if pages_saved > 0:
            time.sleep(rate_limit)
        
        # Fetch page
        result = fetch_page(url)
        if not result:
            pages_failed += 1
            continue
        
        html, status_code = result
        
        # Extract content
        content = extract_main_content(html)
        
        if not content:
            print(f"  No content: {url}")
            continue
        
        # Determine save path
        save_path = get_path_from_url(url, base_url)
        
        # Create directory structure
        full_path = domain_dir / save_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save content
        page_data = {
            "url": url,
            "scraped_at": datetime.now().isoformat(),
            "status_code": status_code,
            "depth": depth,
            "content": content,
            "word_count": len(content.split()),
        }
        
        full_path.write_text(json.dumps(page_data, indent=2))
        pages_saved += 1
        
        print(f"  [{depth}] {save_path} ({len(content.split())} words)")
        
        # Add new links to queue (up to max_depth)
        if depth < max_depth:
            links = extract_links(html, base_url, base_domain)
            for link in links:
                if link not in visited:
                    queue.append((link, depth + 1))
    
    # Save visited tracking
    visited_file.write_text(json.dumps(list(visited)))
    
    print(f"\n  Done: {pages_saved} pages saved, {pages_failed} failed")
    
    return {
        "pages_saved": pages_saved,
        "pages_failed": pages_failed,
        "total_visited": len(visited)
    }


def mirror_github(username: str, max_repos: int = 50) -> dict:
    """Mirror GitHub repositories using API."""
    import requests
    
    domain = get_domain(f"https://github.com/{username}")
    domain_dir = ensure_domain_dir(domain)
    
    print(f"\nMirroring GitHub: {username}")
    
    try:
        response = requests.get(
            f"https://api.github.com/users/{username}/repos",
            params={"sort": "updated", "per_page": min(max_repos, 100)},
            timeout=30
        )
        response.raise_for_status()
        repos = response.json()
    except Exception as e:
        print(f"  GitHub API failed: {e}")
        return {}
    
    # Save full repo list
    repo_data = {
        "scraped_at": datetime.now().isoformat(),
        "username": username,
        "repositories": []
    }
    
    for repo in repos[:max_repos]:
        repo_data["repositories"].append({
            "name": repo.get("name"),
            "description": repo.get("description"),
            "language": repo.get("language"),
            "topics": repo.get("topics", []),
            "stars": repo.get("stargazers_count", 0),
            "forks": repo.get("forks_count", 0),
            "url": repo.get("html_url"),
            "homepage": repo.get("homepage"),
            "updated": repo.get("updated_at"),
            "created": repo.get("created_at"),
        })
    
    output_file = domain_dir / "repositories.json"
    output_file.write_text(json.dumps(repo_data, indent=2))
    
    print(f"  Saved {len(repo_data['repositories'])} repositories")
    
    return {"repos_saved": len(repo_data["repositories"])}


def mirror_all(resume: bool = False) -> dict:
    """Mirror all enabled sources."""
    sources = load_sources()
    settings = load_settings()
    
    rate_limit = settings.get("rate_limit_delay", 1.5)
    
    results = {}
    
    for source in sources:
        url = source["url"]
        source_type = source.get("type", "website")
        
        print(f"\n{'=' * 50}")
        print(f"Source: {url} ({source_type})")
        print(f"{'=' * 50}")
        
        domain = get_domain(url)
        
        if source_type == "github":
            username = url.split("/")[-1]
            max_repos = source.get("max_repos", 50)
            result = mirror_github(username, max_repos)
        
        else:
            max_depth = source.get("max_depth", 3)
            exclude = source.get("exclude", [])
            result = mirror_site(
                url, domain, max_depth, exclude, rate_limit, resume
            )
        
        results[domain] = result
    
    return results


def main():
    """CLI entry point."""
    import argparse
    parser = argparse.ArgumentParser(description="Deep website mirror")
    parser.add_argument("--domain", help="Mirror single domain only")
    parser.add_argument("--resume", action="store_true", help="Resume interrupted mirror")
    parser.add_argument("--force", action="store_true", help="Force re-scrape all")
    args = parser.parse_args()
    
    print("=" * 50)
    print("Deep Mirror - Website Content Scraper")
    print("=" * 50)
    
    if args.domain:
        # Mirror single domain
        sources = load_sources()
        settings = load_settings()
        
        for source in sources:
            if get_domain(source["url"]) == args.domain:
                url = source["url"]
                domain = get_domain(url)
                max_depth = source.get("max_depth", 3)
                exclude = source.get("exclude", [])
                rate_limit = settings.get("rate_limit_delay", 1.5)
                
                if source.get("type") == "github":
                    mirror_github(url.split("/")[-1])
                else:
                    mirror_site(url, domain, max_depth, exclude, rate_limit, args.resume)
                break
    else:
        mirror_all(args.resume)
    
    print("\n" + "=" * 50)
    print("Done!")


if __name__ == "__main__":
    main()