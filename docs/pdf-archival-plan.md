# PDF Archival Implementation Plan

## Overview
Archive all PDF generation components from this repository while preserving the interactive HTML website functionality. The new PDF system has moved to `~/repos/resume-builder-workspace` which uses Gotenberg API with Markdown.

## Goals
1. Remove PDF generation code (LaTeX V1 + AI-driven V2 pipeline)
2. Preserve HTML website building functionality
3. Keep `data/resume.yaml` for HTML site
4. Add "Download PDF" button to website header (links to local PDF in assets)
5. Maintain clean git history with archived files accessible in `archived/`

## Implementation Steps

### Step 1: Create Archive Directory Structure
```
archived/
├── pdf-v1/
│   ├── scripts/
│   └── templates/
├── pdf-v2/
│   ├── scripts/
│   └── docs/
└── README.md
```

### Step 2: Move PDF V1 Components to `archived/pdf-v1/`
- `scripts/render_latex.py` → `archived/pdf-v1/scripts/`
- `scripts/build_pdf.sh` → `archived/pdf-v1/scripts/`
- `templates/latex/` → `archived/pdf-v1/templates/`

### Step 3: Move PDF V2 Components to `archived/pdf-v2/`
- `scripts/pdf_v2/` → `archived/pdf-v2/scripts/`
- `scripts/prompts/` → `archived/pdf-v2/scripts/`
- `docs/pdf-v2-migration/` → `archived/pdf-v2/docs/`
- `data/scraping_sources.yaml` → `archived/pdf-v2/data/`

### Step 4: Clean Up Generated/Regenerable Content
- Delete `dist/pdf/` directory (generated output)
- Delete `db/` directory (ChromaDB - can be rebuilt from archive if needed)

### Step 5: Update Build Scripts
- `scripts/build_all.py`:
  - Remove PDF build logic
  - Keep only HTML build functionality
  - Remove PDF-related imports and functions

### Step 6: Update `AGENTS.md`
- Remove PDF-related build commands
- Remove PDF architecture diagram
- Remove PDF dependencies section
- Update architecture to show only HTML pipeline:
  ```
  data/resume.yaml
      ↓ (render_html.py)
  templates/html/index.html → dist/html/index.html
  ```

### Step 7: Update `requirements.txt`
- Remove PDF-specific dependencies:
  - `PyPDF2>=3.0` (used by PDF V2)
  - Any other PDF-related packages
- Keep `PyYAML>=6.0` (needed for HTML rendering)

### Step 8: Add PDF Download Button to Website
1. Create `assets/pdf/` directory
2. User will manually place current PDF resume there
3. Update `templates/html/index.html`:
   - Add download button in header
   - Link to `assets/pdf/resume.pdf`
4. Update `scripts/build_all.py` or `scripts/build_html.sh`:
   - Copy `assets/pdf/resume.pdf` to `dist/html/assets/pdf/`

### Step 9: Git Operations
1. Commit archive plan: `docs/pdf-archival-plan.md`
2. Implement changes
3. Commit archiving: "Archive PDF components, keep website only"
4. Verify HTML build still works

## Files to Keep (Website Only)
- `data/resume.yaml` (source data)
- `templates/html/` (HTML template, JS, CSS)
- `scripts/render_html.py` (HTML renderer)
- `scripts/build_html.sh` (HTML build script)
- `scripts/build_all.py` (modified - HTML only)
- `assets/audio/` (audio files for website)
- `dist/html/` (HTML output)

## Files to Archive
- `scripts/render_latex.py` → `archived/pdf-v1/scripts/`
- `scripts/build_pdf.sh` → `archived/pdf-v1/scripts/`
- `templates/latex/` → `archived/pdf-v1/templates/`
- `scripts/pdf_v2/` → `archived/pdf-v2/scripts/`
- `scripts/prompts/` → `archived/pdf-v2/scripts/`
- `docs/pdf-v2-migration/` → `archived/pdf-v2/docs/`
- `data/scraping_sources.yaml` → `archived/pdf-v2/data/`

## Files to Delete (Regenerable)
- `dist/pdf/` (entire directory)
- `db/` (entire directory)

## Notes
- User will manually add PDF to `assets/pdf/resume.pdf`
- Build script will copy PDF to `dist/html/assets/pdf/` for deployment
- `.env` file kept if needed for other purposes, otherwise can be archived
- Git history preserves all moved files if needed to restore
