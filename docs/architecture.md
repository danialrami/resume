# Architecture Document

## Overview

A single-source-of-truth resume system that generates both PDF and interactive HTML versions from `data/resume.yaml`.

## Architecture

```
data/resume.yaml
    ↓
scripts/render_latex.py → dist/pdf/resume.tex → (xelatex) → dist/pdf/resume.pdf
    ↓
scripts/render_html.py  → dist/html/index.html (+ assets)

assets/audio/*.wav → (ffmpeg) → dist/html/assets/audio/*.opus (~11x compression)
```

## Components

### Data Layer
- **`data/resume.yaml`**: Single source of truth for all resume data
- Schema includes: name, title, contact, profile, experience, skills, education, certifications, projects

### Build Scripts
- **`scripts/render_latex.py`**: Generates LaTeX from YAML data
- **`scripts/render_html.py`**: Generates HTML from YAML data, converts audio
- **`scripts/build_all.py`**: Orchestrates both builds
- **`scripts/deploy.sh`**: Builds and deploys to `hostinger` branch

### Templates
- **`templates/latex/resume.tex`**: LaTeX template with placeholders
- **`templates/html/`**: HTML, CSS, JS files for interactive resume

### Assets
- **`assets/audio/`**: High-quality source audio (WAV files, not committed)
- **`dist/html/assets/audio/`**: Compressed OPUS files (committed to deploy branch)

## Audio Pipeline

### Build-time Conversion
1. Scan `assets/audio/` for WAV/MP3/FLAC files
2. Convert to OPUS format using ffmpeg (`libopus`, 192kbps)
3. Copy to `dist/html/assets/audio/`
4. Generate dropdown HTML with sample names and durations

### Runtime Loading
- **Local mode** (default): Load from `assets/audio/*.opus`
- **URL mode**: Set `AUDIO_BASE_URL` env var to load from CDN

### Browser Compatibility
- OPUS supported in Chrome, Firefox, Safari, Edge
- Audio visualizations require HTTP (not file://)

## Deployment

The `deploy.sh` script:
1. Runs `build_all.py` (converts audio to OPUS)
2. Commits changes to `main` branch
3. Uses `git subtree split` to extract `dist/html/` to temp branch
4. Force pushes to `hostinger` branch on origin

## File Sizes

| File Type | Typical Size | Notes |
|-----------|--------------|-------|
| WAV       | 30-110 MB    | Source files (not committed) |
| OPUS      | 2-10 MB      | ~11x smaller, browser-compatible |
| HTML/CSS/JS | <1 MB      | Template files |

## Dependencies

| Tool | Purpose |
|------|---------|
| Python 3.8+ | Build scripts |
| PyYAML | YAML parsing |
| xelatex/pdflatex | PDF generation |
| ffmpeg | Audio conversion to OPUS |
