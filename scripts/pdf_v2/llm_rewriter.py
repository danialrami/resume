"""LLM rewriter with guardrails using litellm."""

import httpx
from typing import Optional
from .config import (
    LLM_BASE_URL,
    LLM_API_KEY,
    LLM_MODEL,
    MAX_BULLET_CHARS,
)


SYSTEM_PROMPT = """You are a resume bullet point rewriter. Your task is to rewrite 
resume bullet points to highlight transferable skills relevant to the job description.

RULES:
- Do NOT invent new skills, metrics, or experiences
- Do NOT exceed {max_chars} characters
- Maintain formal, action-oriented tone
- Highlight transferable skills if exact match unavailable
- If no connection possible, return "UNCHANGED" 

Output ONLY the rewritten bullet, or "UNCHANGED" if no rewrite needed."""


USER_PROMPT_TEMPLATE = """Job Description (excerpt):
{jd_text}

Resume Bullet to Rewrite:
{bullet}

Rewrite to highlight relevance:"""


def rewrite_bullet(
    bullet: str,
    jd_text: str,
    model: str = None,
    max_chars: int = MAX_BULLET_CHARS
) -> str:
    """
    Rewrite a single bullet point for job relevance.
    
    Uses strict guardrails to prevent fabrication.
    """
    if model is None:
        model = LLM_MODEL
    
    system_prompt = SYSTEM_PROMPT.format(max_chars=max_chars)
    
    user_prompt = USER_PROMPT_TEMPLATE.format(
        jd_text=jd_text[:1000],
        bullet=bullet
    )
    
    response = call_llm(system_prompt, user_prompt, model)
    
    if response.strip() == "UNCHANGED":
        return bullet
    
    return response.strip()


def rewrite_all_bullets(
    bullets: list[dict],
    jd_text: str,
    model: str = None,
    max_chars: int = MAX_BULLET_CHARS
) -> list[dict]:
    """
    Rewrite all bullets in a list.
    
    Returns list of dicts with original and rewritten content.
    """
    if model is None:
        model = LLM_MODEL
    
    results = []
    
    for bullet_item in bullets:
        original = bullet_item.get("content", "")
        
        try:
            rewritten = rewrite_bullet(original, jd_text, model, max_chars)
        except Exception as e:
            print(f"  Warning: LLM rewrite failed for bullet: {e}")
            rewritten = original
        
        results.append({
            "original": original,
            "rewritten": rewritten,
            "id": bullet_item.get("id"),
            "metadata": bullet_item.get("metadata", {}),
            "was_rewritten": rewritten != original
        })
    
    return results


def call_llm(
    system_prompt: str,
    user_prompt: str,
    model: str = None
) -> str:
    """
    Call LLM via litellm-compatible API.
    """
    if model is None:
        model = LLM_MODEL
    
    client = httpx.Client(
        base_url=LLM_BASE_URL,
        headers={
            "Authorization": f"Bearer {LLM_API_KEY}",
            "Content-Type": "application/json"
        },
        timeout=30.0
    )
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    response = client.post("/chat/completions", json={
        "model": model,
        "messages": messages,
        "temperature": 0.3,
        "max_tokens": 200
    })
    
    if response.status_code != 200:
        raise Exception(f"LLM call failed: {response.text}")
    
    data = response.json()
    content = data["choices"][0]["message"]["content"]
    
    return content


def test_connection() -> bool:
    """Test LLM connection."""
    try:
        call_llm(
            "You are a test assistant.",
            "Reply with exactly: TEST_OK",
            LLM_MODEL
        )
        return True
    except Exception as e:
        print(f"LLM connection test failed: {e}")
        return False