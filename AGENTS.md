# AGENTS

## Build / Lint / Test
- **Setup**: `./scripts/setup.sh` or `source .venv/bin/activate`
- **Build both**: `./scripts/build.sh` or `python scripts/build_all.py`
- **Build PDF only**: `./scripts/build_pdf.sh` or `python scripts/render_latex.py`
- **Build HTML only**: `./scripts/build_html.sh` or `python scripts/render_html.py`
- **Test**: Run build commands and inspect output files in `dist/`

## Code Style Guidelines

### YAML Data (`data/resume.yaml`)
- Use 2-space indentation
- Keep lines <80 chars
- Use descriptive keys with underscores
- Maintain consistent data types across sections

### LaTeX Template (`templates/latex/resume.tex`)
- Load only necessary packages
- 4-space indentation, lines <80 chars
- Section titles Title Case
- Comments with `%`
- Follow standard LaTeX conventions

### HTML Template (`templates/html/index.html`)
- Semantic HTML5 structure
- Consistent CSS variable usage
- Mobile-first responsive design
- Accessibility considerations (ARIA labels, keyboard navigation)

## Architecture

```
data/resume.yaml
    ↓
templates/latex/resume.tex  →  dist/pdf/resume.pdf (via pdflatex)
    ↓
templates/html/index.html   →  dist/html/index.html
```

## Adding New Features

1. Update `data/resume.yaml` with new data
2. Add template support in respective `templates/` subdirectory
3. Rebuild and verify output in `dist/`
4. Commit both source files and generated outputs

## Dependencies

- Python 3.8+ (venv included)
- PyYAML (installed via requirements.txt)
- PyPDF2 (for PDF operations, optional)

For PDF generation:
- MacTeX or TeX Live (system-level LaTeX distribution)
