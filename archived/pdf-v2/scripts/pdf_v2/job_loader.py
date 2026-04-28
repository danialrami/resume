"""Job description loader - fetches JDs from URLs or text files."""

import re
from pathlib import Path
from typing import Optional
import requests
from bs4 import BeautifulSoup


def load_jd(source: str) -> dict:
    """
    Load job description from URL or text file.
    
    Args:
        source: URL (http://...) or file path (.txt, .md)
    
    Returns:
        dict with keys: text, url, source_type
    """
    if source.startswith("http://") or source.startswith("https://"):
        return fetch_jd_url(source)
    else:
        return load_jd_file(source)


def fetch_jd_url(url: str) -> dict:
    """
    Fetch and extract job description text from URL.
    
    Attempts to extract main content, filters out navigation,
    footers, etc.
    """
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
    except requests.RequestException as e:
        raise Exception(f"Failed to fetch URL: {e}")
    
    soup = BeautifulSoup(response.text, "lxml")
    
    text = extract_job_description(soup)
    
    return {
        "text": text,
        "url": url,
        "source_type": "url"
    }


def extract_job_description(soup: BeautifulSoup) -> str:
    """
    Extract main job description content from HTML.
    
    Strategies:
    1. Look for common job description containers
    2. Remove nav, footer, sidebar elements
    3. Extract text from remaining content
    """
    for unwanted in soup(["script", "style", "nav", "footer", "header"]):
        unwanted.decompose()
    
    selectors = [
        "[role='main']",
        ".job-description",
        "#job-description",
        ".content.job-details",
        "[data-testid='job-description']",
        "article",
        ".job-post",
        ".job-detail",
    ]
    
    for selector in selectors:
        element = soup.select_one(selector)
        if element:
            text = element.get_text(separator="\n", strip=True)
            if len(text) > 200:
                return clean_text(text)
    
    body = soup.find("body")
    if body:
        return clean_text(body.get_text(separator="\n", strip=True))
    
    return ""


def load_jd_file(file_path: str) -> dict:
    """Load job description from text file."""
    path = Path(file_path)
    
    if not path.exists():
        raise Exception(f"File not found: {file_path}")
    
    text = path.read_text(encoding="utf-8")
    
    return {
        "text": text,
        "url": str(path),
        "source_type": "file"
    }


def clean_text(text: str) -> str:
    """Clean extracted text."""
    lines = text.split("\n")
    cleaned = []
    
    for line in lines:
        line = line.strip()
        if len(line) > 20:
            cleaned.append(line)
    
    return "\n".join(cleaned)


def extract_keywords(jd_text: str) -> list[str]:
    """
    Extract keywords from job description.
    
    Simple extraction - can be enhanced with LLM.
    """
    words = re.findall(r"\b[A-Za-z][A-Za-z0-9+#]+\b", jd_text)
    
    stopwords = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
               "of", "with", "by", "from", "as", "is", "are", "was", "were", "be",
               "been", "have", "has", "had", "do", "does", "did", "will", "would",
               "could", "should", "may", "might", "must", "this", "that", "these",
               "those", "you", "your", "we", "our", "they", "their", "it", "its"}
    
    keywords = [w.lower() for w in words if w.lower() not in stopwords and len(w) > 2]
    
    from collections import Counter
    return [word for word, _ in Counter(keywords).most_common(30)]