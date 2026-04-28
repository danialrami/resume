# AGENTS

## Build / Lint / Test
- **Setup**: `./scripts/setup.sh` or `source .venv/bin/activate`
- **Build HTML**: `./scripts/build_all.py` or `./scripts/build_html.sh`
- **Deploy to hostinger**: `./scripts/deploy.sh`
- **Test**: Run build commands and inspect output files in `dist/html/`

## Code Style Guidelines

### YAML Data (`data/resume.yaml`)
- Use 2-space indentation
- Keep lines <80 chars
- Use descriptive keys with underscores or hyphens
- Date format: `"YYYY – YYYY"` or single year without quotes

### HTML Template (`templates/html/index.html`)
- Semantic HTML5 structure
- Mobile-first responsive design
- Accessibility considerations (ARIA labels, keyboard navigation)
- Interactive elements from `script.js` and `three_effects.js`
- Output: `dist/html/index.html`

## Architecture

```
data/resume.yaml
    ↓ (render_html.py)
templates/html/index.html   →  dist/html/index.html

assets/audio/*.wav → (build) → dist/html/assets/audio/*.opus (~11x smaller)
assets/pdf/resume.pdf → (build) → dist/html/assets/pdf/resume.pdf
```

## Audio Pipeline

### Local Audio (Default)
- Place WAV files in `assets/audio/`
- Build script converts to OPUS format using ffmpeg
- OPUS files are included in `dist/html/assets/audio/`

### URL-based Audio
Set `AUDIO_BASE_URL` environment variable:
```bash
AUDIO_BASE_URL="https://cdn.example.com/audio" ./scripts/build_all.py
```

### Browser Limitations
- **file:// protocol**: Audio plays but visualizations don't work (Web Audio API security)
- **HTTP/HTTPS**: Full functionality including visualizations
- **Format**: OPUS supported in all modern browsers

## PDF Download

- Place PDF file in `assets/pdf/resume.pdf`
- Build script copies it to `dist/html/assets/pdf/resume.pdf`
- Website header includes "Download PDF" button linking to the PDF

## Dependencies

- Python 3.8+
- PyYAML 6.0+ (installed via requirements.txt)
- ffmpeg (for OPUS audio conversion)

## Adding New Features

1. Update `data/resume.yaml` with new data
2. Add/modify audio files in `assets/audio/` (WAV recommended)
3. Update PDF in `assets/pdf/resume.pdf` (for download button)
4. Modify HTML template in `templates/html/`
5. Rebuild using `./scripts/build_all.py`
6. Review outputs in `dist/`

## Deployment

The `deploy.sh` script:
1. Builds HTML output
2. Converts audio to OPUS (~11x compression)
3. Copies PDF to dist folder
4. Commits to main branch
5. Pushes to origin
6. Splits and deploys HTML to `hostinger` branch

## Archived Components

PDF generation components have been archived to `archived/` directory:
- `archived/pdf-v1/`: Original LaTeX-based PDF generation
- `archived/pdf-v2/`: AI-driven tailored PDF pipeline

The new PDF system is located at `~/repos/resume-builder-workspace` using Gotenberg API.
