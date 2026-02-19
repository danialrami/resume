# Unified Resume Repository

A single-source-of-truth resume system that generates both PDF and interactive HTML versions.

## Architecture

```
data/resume.yaml
    ↓
templates/latex/resume.tex  →  dist/pdf/resume.pdf
    ↓
templates/html/index.html   →  dist/html/
```

## Quick Start

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Build both outputs:
```bash
python scripts/build_all.py
```

3. Build PDF only:
```bash
python scripts/generate_pdf.py  # TODO: create this
```

4. Build HTML only:
```bash
python scripts/generate_html.py  # TODO: create this
```

## File Structure

```
resume/
├── data/
│   └── resume.yaml              # Single source of truth
├── templates/
│   ├── latex/
│   │   └── resume.tex           # LaTeX template
│   └── html/
│       ├── index.html           # HTML template
│       ├── styles.css           # Styles (copied from interactive-resume)
│       ├── script.js            # Interactive scripts
│       └── three_effects.js     # Three.js effects
├── dist/
│   ├── pdf/
│   │   └── resume.tex           # Generated LaTeX
│   └── html/
│       └── index.html           # Generated HTML
├── scripts/
│   ├── build_all.py             # Main build script
│   ├── render_latex.py          # PDF generator
│   └── render_html.py           # HTML generator
└── docs/
    ├── README.md                # This file
    └── architecture.md          # Design decisions
```

## YAML Schema

The `data/resume.yaml` file contains all resume data with sections for:

- **name**: Your name
- **title/job-title**: Professional title
- **contact**: Email, phone, social links
- **profile**: Professional summary
- **experience**: Work history with bullets
- **skills**: Categorized skill groups
- **education**: Academic background
- **certifications**: Professional certifications
- **projects**: Technical projects

## Template Customization

### LaTeX (PDF)
-edit `templates/latex/resume.tex`
- Use `pdflatex` to compile: `pdflatex -interaction=nonstopmode dist/pdf/resume.tex`

### HTML (Interactive)
- Edit `templates/html/index.html` and associated files
- View directly in browser: `open dist/html/index.html`

## Migration Notes

This repository was created by unifying:
- `generate-resume-pdf`: PDF-only resume generator
- `interactive-resume`: Audio/visual interactive resume

Both repositories are now source-controlled here with:
- YAML as the single data source
- Separate templates for print and interactive outputs
- Shared build pipeline

## Development

1. Update `data/resume.yaml`
2. Run: `python scripts/build_all.py`
3. Check outputs in `dist/`

## License

Same as original repositories.
