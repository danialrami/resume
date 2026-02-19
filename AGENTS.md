# AGENTS

## Build / Lint / Test
- **Setup**: `./scripts/setup.sh` or `source .venv/bin/activate`
- **Build both**: `./scripts/build.sh` or `python scripts/build_all.py`
- **Build PDF only**: `./scripts/build_pdf.sh` or `python scripts/render_latex.py`
- **Build HTML only**: `./scripts/build_html.sh` or `python scripts/render_html.py`
- **Lint LaTeX**: Optional (pdflatex/xelatex will report errors)
- **Test**: Run build commands and inspect output files in `dist/`

## Code Style Guidelines

### YAML Data (`data/resume.yaml`)
- Use 2-space indentation
- Keep lines <80 chars
- Use descriptive keys with underscores or hyphens
- Date format: `"YYYY – YYYY"` or single year without quotes

### LaTeX Template (`templates/latex/resume.tex`)
- Follow standard LaTeX conventions
- 4-space indentation, lines <80 chars  
- Section titles Title Case
- Comments with `%`
- Output compiled to: `dist/pdf/resume.pdf`

### HTML Template (`templates/html/index.html`)
- Semantic HTML5 structure
- Mobile-first responsive design
- Accessibility considerations (ARIA labels, keyboard navigation)
- Interactive elements from `script.js` and `three_effects.js`
- Output: `dist/html/index.html`

## Architecture

```
data/resume.yaml
    ↓ (render_latex.py / render_html.py)
templates/latex/resume.tex  →  dist/pdf/resume.pdf (via xelatex)
templates/html/index.html   →  dist/html/index.html
```

## Dependencies

- Python 3.8+
- PyYAML 6.0+ (installed via requirements.txt)
- xelatex or pdflatex (for PDF generation)

For PDF generation:
- **xelatex** (recommended if using fontspec)
- **pdflatex** (fallback, may need to remove fontspec package)

## Adding New Features

1. Update `data/resume.yaml` with new data
2. Modify templates in respective `templates/` subdirectory
3. Rebuild using scripts or `python scripts/build_all.py`
4. Review outputs in `dist/`

## Migration Notes

This repository unifies two previous repositories:

- **generate-resume-pdf**: PDF-only resume generator using YAML → LaTeX
- **interactive-resume**: Interactive HTML5 resume with audio visualizations

The unified system uses:
- Single source of truth: `data/resume.yaml`
- Separate templates for print (LaTeX) and web (HTML)
- Shared Python build scripts for consistent generation
