#!/usr/bin/env python3
"""Tag expander - use LLM to extract transferable tags from scraped content.

Given a job description and existing resume content, use LLM to:
1. Identify direct matches (existing tags)
2. Suggest transferable skills for adjacent roles
3. Highlight industry-adjacent keywords
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

import yaml
load_dotenv()

# Get paths
BASE_DIR = Path(__file__).parent.parent.parent
DATA_DIR = BASE_DIR / "data"
PROMPTS_DIR = BASE_DIR / "scripts" / "prompts"

LLM_BASE_URL = os.getenv("LLM_BASE_URL")
LLM_API_KEY = os.getenv("LLM_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")


SYSTEM_PROMPT = """You are a career profile tagger. Your task is to analyze resume content 
and job descriptions to identify relevant skills and keywords.

For each piece of content, identify:
1. DIRECT_TAGS: Keywords that directly match the content
2. TRANSFERABLE_TAGS: Skills that transfer to adjacent roles (e.g., "team-leadership" for managers)
3. INDUSTRIES: Industry keywords

IMPORTANT:
- Only suggest keywords that are actually present or clearly transferable
- Do NOT fabricate experiences
- Keep tags lowercase, hyphenated where appropriate
- Focus on actionable skills and competencies"""


def load_prompt(name: str) -> str:
    """Load prompt from prompts directory."""
    prompt_path = PROMPTS_DIR / f"{name}.md"
    if prompt_path.exists():
        return prompt_path.read_text()
    return ""


def load_scraped_content() -> str:
    """Load scraped content from web_content scraper."""
    from .web_content import extract_all_text
    return extract_all_text()


def call_llm(prompt: str, content: str, jd_context: str = "") -> str:
    """Call LLM with prompt."""
    import httpx
    
    user_prompt = f"""{prompt}

Job Description Context:
{jd_context[:500]}

Content to analyze:
{content[:2000]}

For each bullet or section, output in format:
BULLET: [original text]
DIRECT_TAGS: tag1, tag2
TRANSFERABLE_TAGS: tag1, tag2
INDUSTRIES: tag1, tag2

---
Output:"""
    
    client = httpx.Client(
        base_url=LLM_BASE_URL,
        headers={
            "Authorization": f"Bearer {LLM_API_KEY}",
            "Content-Type": "application/json"
        },
        timeout=60.0
    )
    
    response = client.post("/chat/completions", json={
        "model": LLM_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.3,
        "max_tokens": 1000
    })
    
    if response.status_code != 200:
        raise Exception(f"LLM call failed: {response.text}")
    
    return response.json()["choices"][0]["message"]["content"]


def load_resume_data() -> dict:
    """Load current resume data."""
    yaml_path = DATA_DIR / "resume.yaml"
    return yaml.safe_load(yaml_path.read_text())


def suggest_tags_for_job(jd_text: str, max_tags: int = 20) -> dict:
    """Given a job description, suggest tags to prioritize."""
    
    content = load_scraped_content()
    resume = load_resume_data()
    
    # Build content from resume
    resume_text = resume.get("profile", "")
    for exp in resume.get("experience", []):
        resume_text += "\n" + exp.get("company", "")
        for desc in exp.get("description", []):
            resume_text += "\n- " + desc
    
    # Call LLM for suggestions
    prompt = "Analyze and suggest relevant tags for this job description based on the resume content."
    
    try:
        result = call_llm(prompt, resume_text, jd_text)
    except Exception as e:
        print(f"  LLM call failed: {e}")
        return {}
    
    # Parse results (simple extraction)
    tags = {
        "direct": [],
        "transferable": [],
        "industries": []
    }
    
    for line in result.split("\n"):
        line = line.strip()
        if line.startswith("DIRECT_TAGS:"):
            tags["direct"] = [t.strip() for t in line.split(":", 1)[1].split(",") if t.strip()]
        elif line.startswith("TRANSFERABLE_TAGS:"):
            tags["transferable"] = [t.strip() for t in line.split(":", 1)[1].split(",") if t.strip()]
        elif line.startswith("INDUSTRIES:"):
            tags["industries"] = [t.strip() for t in line.split(":", 1)[1].split(",") if t.strip()]
    
    return tags


def enrich_resume_yaml(suggested_tags: dict) -> dict:
    """Add suggested tags to resume.yaml structure."""
    
    resume = load_resume_data()
    
    # For each experience, add placeholder for transferable tags
    # This is a one-time enrichment
    for exp in resume.get("experience", []):
        if "transferable" not in exp:
            # LLM would fill these in
            exp["transferable"] = []
    
    return resume


def generate_tag_report(jd_text: str) -> str:
    """Generate a tag report for a job description."""
    
    tags = suggest_tags_for_job(jd_text)
    
    report = ["# Tag Suggestions for Job", ""]
    
    if tags.get("direct"):
        report.append("## Direct Match Tags")
        report.extend([f"- {t}" for t in tags["direct"]])
        report.append("")
    
    if tags.get("transferable"):
        report.append("## Transferable Tags")
        report.extend([f"- {t}" for t in tags["transferable"]])
        report.append("")
    
    if tags.get("industries"):
        report.append("## Industry Tags")
        report.extend([f"- {t}" for t in tags["industries"]])
    
    return "\n".join(report)


def main():
    """CLI entry point."""
    import argparse
    parser = argparse.ArgumentParser(description="Tag expander for resume")
    parser.add_argument("--jd", default="", help="Job description text (or URL)")
    parser.add_argument("--report", action="store_true", help="Output tag report only")
    args = parser.parse_args()
    
    print("=" * 50)
    print("Tag Expander")
    print("=" * 50)
    
    if args.jd:
        if args.jd.startswith("http"):
            from .job_loader import load_jd
            jd_data = load_jd(args.jd)
            jd_text = jd_data.get("text", "")
        else:
            jd_text = args.jd
        
        if args.report:
            report = generate_tag_report(jd_text)
            print(report)
        else:
            tags = suggest_tags_for_job(jd_text)
            print(f"\nDirect: {tags.get('direct', [])}")
            print(f"Transferable: {tags.get('transferable', [])}")
            print(f"Industries: {tags.get('industries', [])}")
    else:
        print("Usage: --jd 'job description or URL' [--report]")


if __name__ == "__main__":
    main()