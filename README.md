# Unified Resume Repository

A single-source-of-truth resume system that generates both PDF and interactive HTML versions with audio samples.

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
# or: source .venv/bin/activate
```

2. Build both outputs:
```bash
./scripts/build_all.py
# or: python scripts/build_all.py
```

3. Build HTML only:
```bash
./scripts/build_html.sh
```

4. Build PDF only:
```bash
./scripts/build_pdf.sh
```

## Deployment

To build and deploy to the `hostinger` branch:
```bash
./scripts/deploy.sh
```

This will:
1. Build both PDF and HTML outputs
2. Convert audio files to OPUS format (~11x smaller)
3. Commit changes to main branch
4. Push to origin
5. Deploy HTML to `hostinger` branch for hosting

## Audio Files

### Local Audio (Default)
Place high-quality WAV files in `assets/audio/`. During build:
- Files are converted to OPUS format (~11x compression)
- Dropdown in the HTML shows sample names with durations
- Works offline when served locally

### URL-based Audio
To load audio from a CDN or external URL:
```bash
AUDIO_BASE_URL="https://cdn.example.com/audio" ./scripts/build_all.py
```

### Audio Requirements
- **Browser compatibility**: OPUS is supported in all modern browsers
- **HTTP required**: Audio visualizations require the site to be served via HTTP
- Opening `dist/html/index.html` directly (file://) will play audio but without visualizations

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
│       ├── styles.css           # Styles
│       ├── script.js            # Interactive scripts
│       └── three_effects.js     # Three.js effects
├── assets/
│   └── audio/                   # High-quality source audio (WAV)
├── dist/
│   ├── pdf/
│   │   └── resume.pdf           # Generated PDF
│   └── html/
│       └── index.html           # Generated HTML with OPUS audio
├── scripts/
│   ├── build_all.py             # Build both PDF and HTML
│   ├── build_html.sh            # Build HTML only
│   ├── build_pdf.sh             # Build PDF only
│   ├── deploy.sh                # Build and deploy to hostinger
│   ├── render_latex.py          # PDF generator
│   └── render_html.py           # HTML generator
└── docs/
    └── README.md                # This file
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
- Edit `templates/latex/resume.tex`
- Use `xelatex` to compile: `cd dist/pdf && xelatex resume.tex`

### HTML (Interactive)
- Edit `templates/html/` files
- For full functionality, serve via HTTP:
  ```bash
  cd dist/html && python3 -m http.server 8080
  ```

## Dependencies

- Python 3.8+
- PyYAML 6.0+
- xelatex or pdflatex (for PDF)
- ffmpeg (for audio conversion to OPUS)

## Development

1. Update `data/resume.yaml`
2. Add/modify audio files in `assets/audio/` (WAV format recommended)
3. Run: `./scripts/build_all.py`
4. Check outputs in `dist/`
5. Test with: `cd dist/html && python3 -m http.server 8080`

## License

MIT
