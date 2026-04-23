# PDF V2 Migration Plan: Dynamic Job-Description-Driven Resume Pipeline

## Executive Summary

Build a modular pipeline that takes a job description URL or text, uses semantic embeddings to match your skills/experience to the JD, applies LLM-guided rewriting with guardrails, iteratively compiles until content fits one page, and outputs a tailored PDF resume.

---

## Table of Contents

1. [Design Philosophy](#design-philosophy)
2. [Popular Tech Stacks](#popular-tech-stacks)
3. [Problems & Troubleshooting](#problems--troubleshooting)
4. [V1 Codebase Analysis](#v1-codebase-analysis)
5. [V2 Architecture](#v2-architecture)
6. [Implementation Plan](#implementation-plan)
7. [Configuration Reference](#configuration-reference)
8. [V3: Web Enrichment & Application History](#v3-web-enrichment--application-history)

---

## Design Philosophy

### Core Principles (From Gemini Conversation)

The foundational insight from our analysis: **LaTeX is a typesetting engine, not a content editor**. It places text exactly where it mathematically belongs, and if content exceeds spatial bounds, LaTeX will happily push to page two. It cannot inherently rewrite sentences or automatically drop bullets to fit a bounding box.

This leads to three architectural principles:

| Principle | Implementation |
|-----------|-------------|
| **1. LaTeX = Typesetting Only** | Keep LaTeX as the final rendering layer, not the logic layer |
| **2. Pipeline = Content Logic** | Python handles selection, trimming, rewriting |
| **3. Guardrails + Iteration** | Dual protection: LaTeX error + Python feedback loop |

### The V2 Philosophy

```
┌──────────────────────────────────────────────────────────────────┐
│  JOB DESCRIPTION                                          │
│  (URL or text)                                           │
└─────────────────────┬────────────────────────────────────┘
                      │
                      ▼
┌──────────────────────────────────────────────────────────────────┐
│  1. LOAD & PARSE                                          │
│  - Fetch URL or load text file                            │
│  - Extract text content                                   │
└─────────────────────┬────────────────────────────────────┘
                      │
                      ▼
┌──────────────────────────────────────────────────────────────────┐
│  2. SEMANTIC SEARCH                                     │
│  - Embed JD using your model                            │
│  - Query ChromaDB for relevant bullets                │
│  - Return scored results                              │
└─────────────────────┬────────────────────────────────────┘
                      │
                      ▼
┌──────────────────────────────────────────────────────────────────┐
│  3. CONTENT SELECTION                                   │
│  - Sort by relevance score                        │
│  - Apply pinned items first                        │
│  - Fill by priority score                             │
└─────────────────────┬────────────────────────────────────┘
                      │
                      ▼
┌──────────────────────────────────────────────────────────────────┐
│  4. LLM REWRITE (Guardrails)                                │
│  - Pass bullet + JD to LLM                                │
│  - Strict prompt: No fabrication, max 150 chars         │
│  - Output rewritten bullet                              │
└─────────────────────┬────────────────────────────────────┘
                      │
                      ▼
┌──────────────────────────────────────────────────────────────────┐
│  5. ITERATION LOOP                                       │
│  - Generate LaTeX                                      │
│  - Compile to PDF                                     │
│  - Check page count                                    │
│  - If page > 1: drop lowest priority, repeat          │
│  - Max 5 iterations, then truncate                   │
└─────────────────────┬────────────────────────────────────┘
                      │
                      ▼
┌──────────────────────────────────────────────────────────────────┐
│  6. OUTPUT                                             │
│  - 1-page PDF resume                                   │
│  - Tailored to job description                          │
└──────────────────────────────────────────────────────────────────┘
```

---

## Popular Tech Stacks

### Overview of Industry Approaches

Based on web research, here are the common patterns:

| Approach | Tools | Pros | Cons |
|----------|-------|------|------|
| **YAML → LaTeX → PDF** | PyYAML, Jinja2, xelatex | Simple, reliable | No tailoring |
| **JSON + AI Tailoring** | OpenAI GPT, LangChain, LaTeX | Dynamic content | Requires LLM |
| **Tag-based Selection** | YAML tags, Python filtering | Deterministic | Manual tagging effort |
| **Semantic + Iterative** | ChromaDB, embeddings, LLM, xelatex | Best fit for V2 | More complex |

### V2 Tech Stack Selection

| Component | Technology | Rationale |
|-----------|-----------|----------|
| **Content Store** | Expanded YAML + per-bullet metadata | Single source of truth, easily adjustable |
| **Vector DB** | ChromaDB (local, embedded) | Perfect for small scale (hundreds), zero infra |
| **Embedding Model** | Your existing model (via litellm) | Consistent with your stack |
| **LLM** | litellm (OpenAI-compatible) | Your instance at http://100.89.168.11:6280/v1 |
| **Tailoring** | LLM with strict prompts | Guardrails prevent fabrication |
| **Iteration** | Python while loop | Guaranteed termination |
| **PDF Generation** | xelatex | Same as V1 |

### Similar Open Source Projects

| Project | Key Insight |
|---------|------------|
| [AutoCustomizeResume](https://github.com/avishj/AutoCustomizeResume) | Uses "pinned" vs "optional" tags, iterates dropping lowest-scored content |
| [AI-Resume-Builder](https://github.com/abhineetgupta/ai-resume-builder) | Full pipeline: YAML → LLM tailoring → LaTeX → PDF |
| [simple-resume](https://github.com/athola/simple-resume) | ATS scoring, YAML-based |
| [jangwanAnkat/resume-builder](https://github.com/jangwanAnkit/resume-builder) | 4-stage AI pipeline: JD Analysis → Match → Tailor → Validate |

---

## Problems & Troubleshooting

### Common Issues in Dynamic Resume Generation

| Problem | Cause | Solution |
|---------|-------|---------|
| **Page overflow** | Too much content | Iteration loop drops lowest-priority items |
| **LaTeX compile fails** | Special characters unescaped | Already handled in v1 (`escape_latex()`) |
| **LLM fabricates experiences** | No guardrails in prompt | Strict prompts: "Do NOT invent new skills" |
| **Empty search results** | No matches in DB | Fall back to pinned items |
| **LLM API fails** | Network/availability | Skip rewriting, use original bullets |
| **Max iterations exceeded** | Pinned items too many | Reduce pinned count or template spacing |
| **ChromaDB not initialized** | First run | Run `db_manager.py rebuild` |

### LaTeX-Side Error (Guardrails)

Add to template to catch overflow:

```latex
\usepackage{atenddocument}

\AtEndDocument{%
    \ifnum\value{page}>1%
        \PackageError{ResumeLength}{Resume exceeds one page!}{%
            Check pinned items - they may be too numerous.%
        }%
    \fi%
}%
```

### Character Limit Enforcement

Gemini's Method C: Establish a character threshold

1. Create a full one-page resume manually
2. Count characters (~2800 for typical)
3. Enforce in Python before LaTeX:

```python
MAX_CHARS = 2800

def enforce_char_limit(content: list[str]) -> list[str]:
    total = sum(len(bullet) for bullet in content)
    while total > MAX_CHARS and content:
        content.pop()  # Remove lowest priority
        total = sum(len(bullet) for bullet in content)
    return content
```

---

## V1 Codebase Analysis

### Current Architecture

```
data/resume.yaml
    │
    ▼
scripts/render_latex.py  →  templates/latex/resume.tex  ──▶  dist/pdf/resume.pdf
    │                            (template with placeholders)
    │                                      
    └── Jinja2-style string replacement
```

### V1 Components

| File | Purpose |
|------|---------|
| `data/resume.yaml` | Master content (single file) |
| `scripts/render_latex.py` | Generates LaTeX from YAML |
| `templates/latex/resume.tex` | Template with `RESUME_*` placeholders |
| `scripts/build_all.py` | Orchestrates HTML + PDF build |

### V1 Limitations

- **Static content**: No job-description tailoring
- **Single output**: Cannot generate role-specific versions
- **No smart selection**: All content always included
- **No iteration**: Relies on manual content adjustment

### V1 Strengths (To Preserve)

| Component | Keep? | Why |
|-----------|-------|-----|
| YAML data structure | Yes | Single source of truth |
| LaTeX escaping | Yes | Critical for special chars |
| Template styling | Yes | Professional look |
| xelatex compilation | Yes | Reliable output |

---

## V2 Architecture

### New Directory Structure

```
resume/
├── .env                         # Environment variables (API keys, endpoints)
├── .gitignore                   # Ignore .env, db/, dist/
├── db/                         # NEW: Semantic embeddings
│   ├── chroma/                # ChromaDB persistent storage
│   └── db_manager.py           # DB initialization & management
├── data/
│   └── resume.yaml             # EXPANDED: per-bullet metadata
├── scripts/
│   ├── pdf_v2/             # NEW: V2 pipeline
│   │   ├── __init__.py
│   │   ├── config.py        # Configuration from .env
│   │   ├── job_loader.py  # JD fetching (URL/text)
│   │   ├── semantic_search.py  # ChromaDB lookup
│   │   ├── content_selector.py  # Relevance ranking
│   │   ├── llm_rewriter.py   # LLM bullet rewrite
│   │   ├── iteration_loop.py  # Compile-check-trim
│   │   ├── render_tailored.py  # LaTeX render
│   │   └── pipeline.py   # Main orchestration
│   ├── render_latex.py    # V1 (unchanged)
│   └── render_html.py      # V1 (unchanged)
├── templates/
│   ├── latex/
│   │   ├── resume.tex    # V1 (unchanged)
│   │   └── resume_tailored.tex  # NEW: Template for tailored
│   └── html/             # V1 (unchanged)
└── docs/
    └── pdf-v2-migration/
        └── README.md    # This documentation
```

### Data Model (Expanded YAML)

```yaml
# Example: data/resume.yaml (expanded format)

experience:
  - company: Hinge Health
    role: Sound Designer (Contract)
    dates: "May 2022 – July 2024"
    bullets:
      - content: "Designed interaction sounds for mobile health applications serving 70k+ daily users"
        tags: [mobile, UX, health-tech, sound-design]
        priority: 10         # 1-10 scale, 10 = keep first
        pinned: true     # Never auto-drop
      - content: "Built custom implementation pipelines using Wwise integrated with Unity"
        tags: [wwise, unity, pipeline]
        priority: 8
        pinned: false
      - content: "Collaborated with UX designers to map user journeys"
        tags: [UX, collaboration]
        priority: 7
        pinned: false
      - content: "Implemented A/B testing framework that achieved 18% increase"
        tags: [A/B-testing, metrics]
        priority: 9
        pinned: false

projects:
  - name: Mobile App Sound Design
    description:
      - content: "Created cohesive sonic identity for health tech app"
        tags: [branding, mobile]
        priority: 8
        pinned: false

skills:
  - category: Audio Software
    list: [Wwise, FMOD]
    # Skills can also have tags for semantic matching
```

### Key Design: Modular Tags

Tags serve multiple purposes:

1. **Semantic matching**: Used for ChromaDB embeddings
2. **Filtering**: Can filter by category (experience vs project)
3. **Priority**: 1-10 scale for iteration selection
4. **Pinned items**: Excluded from auto-dropping

Tags are fully additive - you can add new tags anytime without breaking existing code.

---

## Implementation Plan

### Phase 1: Configuration & Infrastructure ( Evening 1 )

1.1 Create `.env` file with litellm configuration

1.2 Create `.gitignore` entry for `.env`, `db/chroma/`

1.3 Create `scripts/pdf_v2/config.py` to load from `.env`

1.4 Test litellm connection

### Phase 2: Data Model & DB (Evening 1-2)

2.1 Expand `data/resume.yaml` format with bullet metadata

2.2 Create `scripts/pdf_v2/db_manager.py`:

```python
# db_manager.py - ChromaDB initialization
def init_db():
    """Initialize ChromaDB and create schema."""
    
def add_bullet(id, content, metadata):
    """Add single bullet to DB."""
    
def rebuild_db():
    """Full rebuild from YAML."""
```

2.3 Test embedding insertion and search

### Phase 3: Core Pipeline Components (Evening 2)

3.1 `job_loader.py` - Fetch/parse JDs

3.2 `semantic_search.py` - Query ChromaDB

3.3 `content_selector.py` - Priority-based selection

3.4 `llm_rewriter.py` - Guardrailed LLM calls

### Phase 4: Iteration Loop & Rendering (Evening 2-3)

4.1 `iteration_loop.py` - Compile, check, drop

4.2 `render_tailored.py` - LaTeX output for tailored

4.3 Add one-page error to LaTeX template

### Phase 5: Integration (Evening 3)

5.1 `pipeline.py` - Orchestrate all components

5.2 Add CLI entry point

5.3 Test end-to-end with sample JD

### Phase 6: Refinement (Ongoing)

- Tune priority scores based on results
- Add more tags to bullets
- Adjust character limits
- Handle edge cases

---

## Configuration Reference

### Environment Variables (.env)

```bash
# ====== PATHS ======
DATA_PATH=data/resume.yaml
DB_PATH=db/chroma
OUTPUT_PATH=dist/pdf/tailored_resume.pdf

# ====== LLM CONFIG ======
LLM_BASE_URL=http://100.89.168.11:6280/v1
LLM_API_KEY=your-api-key-here
LLM_MODEL=gpt-4o-mini  # or your model

# ====== EMBEDDINGS ======
EMBEDDING_MODEL=text-embedding-3-small  # or your model
EMBEDDING_DIM=1536

# ====== PIPELINE ======
MAX_ITERATIONS=5
MAX_BULLETS=12
MAX_BULLET_CHARS=150

# ====== LATEX ======
LATEX_COMPILER=xelatex
```

### Config Loading

```python
# scripts/pdf_v2/config.py

from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

BASE_DIR = Path(__file__).parent.parent.parent
DATA_DIR = BASE_DIR / os.getenv("DATA_PATH", "data")
DB_DIR = BASE_DIR / os.getenv("DB_PATH", "db/chroma")
OUTPUT_DIR = BASE_DIR / os.getenv("OUTPUT_PATH", "dist/pdf")

LLM_BASE_URL = os.getenv("LLM_BASE_URL")
LLM_API_KEY = os.getenv("LLM_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", 1536))

MAX_ITERATIONS = int(os.getenv("MAX_ITERATIONS", 5))
MAX_BULLETS = int(os.getenv("MAX_BULLETS", 12))
MAX_BULLET_CHARS = int(os.getenv("MAX_BULLET_CHARS", 150))

LATEX_COMPILER = os.getenv("LATEX_COMPILER", "xelatex")
```

---

## Usage

### Initialize DB

```bash
python -m scripts.pdf_v2.db_manager rebuild
```

### Run Pipeline

```bash
# From URL
python -m scripts.pdf_v2.pipeline --jd "https://careers.example.com/job/123"

# From text file
python -m scripts.pdf_v2.pipeline --jd job-posting.txt

# From URL with custom output
python -m scripts.pdf_v2.pipeline --jd "https://..." --output dist/pdf/role-resume.pdf

# Skip LLM rewriting (for testing)
python -m scripts.pdf_v2.pipeline --jd job-posting.txt --no-rewrite
```

---

## Dependencies

```bash
# requirements.txt additions
chromadb>=0.4.22
python-dotenv>=1.0.0
click>=8.1.0
beautifulsoup4>=4.12.0
lxml>=4.9.0
requests>=2.31.0
pypdf2>=3.0.0  # or pypdf
```

---

## Environment Setup

1. Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

2. Fill in `.env` with your values:

```bash
# LLM config
LLM_BASE_URL=http://100.89.168.11:6280/v1
LLM_API_KEY=your-api-key

# Model settings
LLM_MODEL=gpt-4o-mini
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIM=1536
```

3. Rebuild the database:

```bash
python -m scripts.pdf_v2.db_manager rebuild
```

4. Run the pipeline:

```bash
python -m scripts.pdf_v2.pipeline --jd job-posting.txt
```

---

## Module Reference

| Module | Purpose |
|--------|---------|
| `config.py` | Configuration loading from `.env` |
| `job_loader.py` | Fetch JDs from URLs/text files |
| `semantic_search.py` | ChromaDB integration |
| `content_selector.py` | Relevance ranking & selection |
| `llm_rewriter.py` | Guardrailed LLM rewriting |
| `iteration_loop.py` | Compile → check → drop loop |
| `render_tailored.py` | LaTeX generation |
| `db_manager.py` | DB initialization & rebuild |
| `pipeline.py` | Main orchestration |

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| LaTeX compile fails | Check template syntax, ensure xelatex installed |
| Page count wrong | Install poppler-utils for pdfinfo, or use PyPDF2 |
| LLM connection fails | Verify `LLM_BASE_URL` and `LLM_API_KEY` in `.env` |
| ChromaDB errors | Run `python -m scripts.pdf_v2.db_manager rebuild` |
| Empty search results | Add more tags to bullets in `resume.yaml` |

---

## V3: Web Enrichment & Application History

*This section documents Version 3 features: web content scraping, application history tracking, and enhanced tagging.*

### V3 Overview

```
Job Description
       │
       ▼
┌─────────────────────────────────────────────────────────┐
│ 1. SCRAPING: Check data/scraping_sources.yaml          │
│    → Scrape new/stale sites from daniel-ramirez.io     │
│    → Save to db/content/{domain}/                     │
└─────────────────────┬───────────────────────────────────┘
                     ▼
┌─────────────────────────────────────────────────────────┐
│ 2. ENRICHMENT: LLM extracts transferable   │
│    tags from scraped content                  │
│    → Update data/resume.yaml                │
│    → Rebuild ChromaDB                       │
└─────────────────────┬───────────────────────────────────┘
                     ▼
┌─────────────────────────────────────────────────────────┐
│ 3. SELECTION: Enhanced scoring          │
│    Direct (1.0x) + Transferable (0.7x) │
│    + Web Context Boost                       │
└─────────────────────┬───────────────────────────────────┘
                     ▼
┌─────────────────────────────────────────────────────────┐
│ 4. APPLICATION HISTORY (Optional)      │
│    → Check prior applications              │
│    → Log new applications             │
│    → Enable similarity search         │
└─────────────────────┬───────────────────────────────────┘
                     ▼
       ▼
   Generated Resume
```

### New Components

| Component | Script | Purpose |
|-----------|--------|---------|
| Web Scraper | `scripts/pdf_v2/web_content.py` | Scrape daniel-ramirez.io → subsites |
| Tag Expander | `scripts/pdf_v2/tag_expander.py` | LLM-assisted tag generation |
| Application History | `scripts/pdf_v2/history.py` | Track applications |
| Vision Validation | Updated `validator.py` | Using LLM_VISION_MODEL |

---

### Data Sources (from daniel-ramirez.io)

```yaml
# data/scraping_sources.yaml

sources:
  - url: https://daniel-ramirez.io
    type: directory
    description: Central link directory
    parse_mode: extract_links
  
  - url: https://lufs.audio
    type: main_site
    description: Main portfolio
  
  - url: https://portfolio.lufs.audio  
    type: portfolio
    description: Detailed portfolio work
    
  - url: https://danialrami.com
    type: personal
    description: Personal site
    
  - url: https://github.com/danialrami
    type: github
    description: Public repos via GitHub API
```

**Note:** LinkedIn skipped for now - content available on other sites.

---

### Application History DB

**Purpose:** Track generated resumes for:
- Semantic similarity to avoid duplicate applications
- Logging of what was sent to each job
- Future analytics on application success

**Storage:** ChromaDB (flexible, feature-rich)

**Schema:**
```python
{
    "id": "job_url_hash",
    "job_url": "https://...",
    "job_title": "Stage Coordinator",
    "applied_date": "2026-04-23",
    "pdf_path": "dist/pdf/v2/tailored_san_antonio.pdf",
    "match_score": 0.85,
    "status": "applied",  # applied/interested/not-fit
    "notes": ""
}
```

---

### Enhanced Content Model

```yaml
# Enhanced bullet format with multi-field tagging

experience:
  - company: LUFS Audio
    role: Sound Designer
    dates: "July 2024 – Present"
    summary: "Lead sound designer for Hinge Health, xAI, Meta, Roblox"
    description:
      - Lead sound designer for tech clients...
    tags:           # Direct role keywords
      - wwise
      - mobile-audio
    transferable:    # KEY: Keywords for adjacent roles
      - client-coordination
      - team-leadership
      - project-management
    industries:     # Industry-specific
      - tech
      - health-tech
```

---

### Pipeline Flow (Updated)

```
1. LOAD JOB DESCRIPTION
   └─ Load JD from URL or text file
   
2. CHECK HISTORY (NEW)
   └─ If already applied: warn user, show prior score
   └─ If new: continue
   
3. SCRAPE (if stale)
   └─ Check data/scraping_sources.yaml
   └─ Scrape new/stale sites → db/content/
   
4. SEMANTIC SEARCH  
   └─ Query ChromaDB with enhanced content
   
5. CONTENT SELECTION (Enhanced)
   └─ Score: direct (1.0x) + transferable (0.7x)
   
6. LLM REWRITE
   └─ Guardrailed bullet rewriting
   
7. ITERATION LOOP
   └─ Compile → check → drop → repeat
   
8. VALIDATION
   ├─ Simple: Regex check for RESUME_* placeholders
   └─ Vision: LLM_VISION_MODEL (if enabled)
   
9. SAVE HISTORY (NEW)
   └─ Log application to ChromaDB
   
10. OUTPUT PDF
```

---

### Configuration (.env)

```bash
# ====== SCRAPING ======
SCRAPING_SOURCES=data/scraping_sources.yaml
CONTENT_CACHE_DIR=db/content

# ====== LLM CONFIG ======
LLM_BASE_URL=http://100.89.168.11:6280/v1
LLM_API_KEY=your-api-key
LLM_MODEL=coder
LLM_VISION_MODEL=vision  # Vision-capable model

# ====== APPLICATION HISTORY ======
HISTORY_DB_ENABLED=true
HISTORY_DB_PATH=db/history

# ====== VALIDATION ======
VALIDATION_ENABLED=true
VALIDATION_VISION_ENABLED=false  # Set true when ready
```

---

### New Scripts Usage

```bash
# Scrape and enrich content (one-time)
python -m scripts.pdf_v2.web_content scrape

# Rebuild ChromaDB with enriched data
python -m scripts.pdf_v2.db_manager rebuild

# Check application history
python -m scripts.pdf_v2.history check "https://jobposting.url"

# Run full pipeline
python -m scripts.pdf_v2.pipeline --jd "https://jobposting.url"
```

---

### File Structure (V3)

```
resume/
├── data/
│   ├── resume.yaml
│   └── scraping_sources.yaml   # NEW
├── db/
│   ├── chroma/               # Resume embeddings
│   ├── content/              # NEW: Scraped content per site
│   │   ├── daniel-ramirez.io/
│   │   ├── lufs.audio/
│   │   └── github.com/
│   └── history/              # NEW: Application tracking
├── scripts/
│   ├── pdf_v2/
│   │   ├── web_content.py   # NEW
│   │   ├── tag_expander.py  # NEW
│   │   ├── history.py       # NEW
│   │   └── ...
│   └── prompts/
│       └── extract_profile.md # NEW
└── docs/
    └── pdf-v2-migration/
```

---

## References

- Web scraping: BeautifulSoup, requests
- GitHub API: https://api.github.com/users/{username}/repos
- ChromaDB for embeddings: docs.trychroma.com
- [LUFS Blog Pipeline](https://github.com/danialramirez/lufs-blog-pipeline) - Web scraping patterns
- Previous sections document V1-V2 features

---

## Appendix: Technical Details

### LaTeX-Side Error (Guardrails)

The template includes a one-page enforcement check:

```latex
\AtEndDocument{%
    \ifnum\value{page}>1%
        \PackageError{ResumeLength}{Resume exceeds one page!}{}%
    \fi%
}%
```

### ChromaDB Schema

```python
{
    "id": "hinge_health_0",
    "embedding": [0.1, -0.3, ...],  # 1536-dim
    "metadata": {
        "content": "Bullet text...",
        "company": "Hinge Health",
        "category": "experience",
        "tags": "mobile,UX,health-tech",
        "priority": 8,
        "pinned": "false"
    }
}
```

### litellm Integration

The pipeline uses your litellm instance at `http://100.89.168.11:6280/v1` for both embeddings and chat completion.