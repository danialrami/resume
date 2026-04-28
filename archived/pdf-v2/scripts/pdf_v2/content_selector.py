"""Content selector - Relevance scoring and selection."""

from typing import Optional
from .config import MAX_BULLETS


def select_content(
    search_results: list[dict],
    max_bullets: int = MAX_BULLETS
) -> list[dict]:
    """
    Select content based on relevance scores and priorities.
    
    Priority order:
    1. Pinned items (always included)
    2. By relevance score
    3. By priority metadata
    
    Args:
        search_results: Results from semantic search
        max_bullets: Maximum bullets to select
    
    Returns:
        Selected bullets with selection order
    """
    pinned = []
    ranked = []
    
    for item in search_results:
        metadata = item.get("metadata", {})
        is_pinned = metadata.get("pinned", "false") == "true"
        priority = int(metadata.get("priority", 5))
        
        item["priority"] = priority
        item["is_pinned"] = is_pinned
        
        if is_pinned:
            pinned.append(item)
        else:
            ranked.append(item)
    
    ranked.sort(key=lambda x: (
        x.get("relevance_score", 0),
        x.get("priority", 0)
    ), reverse=True)
    
    selected = pinned.copy()
    
    remaining_slots = max_bullets - len(selected)
    if remaining_slots > 0:
        selected.extend(ranked[:remaining_slots])
    
    for i, item in enumerate(selected):
        item["selection_order"] = i + 1
    
    return selected


def find_lowest_priority_item(content: list[dict]) -> Optional[dict]:
    """
    Find the lowest priority non-pinned item.
    
    Used by iteration loop to drop items when page overflows.
    """
    candidates = [item for item in content if not item.get("is_pinned", False)]
    
    if not candidates:
        return None
    
    candidates.sort(key=lambda x: (x.get("priority", 0), x.get("relevance_score", 0)))
    
    return candidates[0]


def drop_item(content: list[dict], item_id: str) -> list[dict]:
    """Remove an item by ID."""
    return [item for item in content if item.get("id") != item_id]


def format_for_latex(selected: list[dict]) -> list[dict]:
    """
    Format selected content for LaTeX rendering.
    
    Groups by company/experience for proper rendering.
    """
    by_company = {}
    
    for item in selected:
        company = item.get("metadata", {}).get("company", "Other")
        
        if company not in by_company:
            by_company[company] = []
        
        by_company[company].append({
            "content": item["content"],
            "priority": item.get("priority", 5),
            "is_pinned": item.get("is_pinned", False)
        })
    
    return by_company