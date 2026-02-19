# Architecture Document

## Current State Analysis

### generate-resume-pdf
- **YAML-driven** with LaTeX template system
- Uses `yaml-resume` package + pdflatex
- Clean separation: `resume.yaml` → template → PDF
- Static, ATS-friendly output

### interactive-resume  
- **HTML/JS/CSS** with Three.js and Web Audio API
- Resume data hardcoded in HTML
- Audio-reactive 3D visualizations
- Scroll-based animations and effects

## Unified Architecture Plan

```
┌─────────────────────────────────────────────────────────────┐
│                    data/resume.yaml                         │
│              (Single Source of Truth)                       │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┴──────────────┐
        │                             │
        ▼                             ▼
┌─────────────────┐         ┌──────────────────────┐
│  YAML Parser    │         │   YAML Parser        │
│  (shared)       │         │   (shared)           │
└────────┬────────┘         └──────────────┬─────────┘
         │                                 │
         ▼                                 ▼
┌──────────────────────┐    ┌──────────────────────┐
│ LaTeX Template       │    │ HTML Template        │
│ templates/latex/     │    │ templates/html/      │
│ - resume.tex         │    │ - index.html         │
│ - Style: Print/ATS   │    │ - Style: Interactive │
└──────────┬───────────┘    └──────────────┬─────────┘
           │                                │
           ▼                                ▼
    ┌──────────────┐                ┌──────────────┐
    │ pdflatex     │                │  Browser     │
    │ dist/pdf/    │                │  HTML Render │
    └──────────────┘                └──────────────┘
```

## Data Flow

1. **Data Entry**: Single `data/resume.yaml` file
2. **Processing**: YAML parser reads data once
3. **Template Substitution**: Two separate templates render from same data
4. **Output Generation**:
   - PDF: LaTeX → pdflatex → static document
   - HTML: Template + JS/CSS → interactive web page

## Template Design Principles

### LaTeX Template (Print/ATS Focus)
- Single column, vertical layout
- Standard resume sections
- ATS-friendly formatting
- Optimized for paper/print

### HTML Template (Interactive Focus)
- Multi-section scroll navigation
- Audio visualization components
- Three.js 3D scene
- Mobile-responsive design
- Brand-specific interactivity

## Next Steps

1. ✅ Design unified YAML schema covering all data needs
2. ✅ Create LaTeX template with LUFS branding
3. ✅ Create HTML template with interactivity structure
4. ⏳ Build shared YAML-to-output pipeline (partial)
5. ⏳ Copy and adapt content from both repos
6. ⏳ Test build pipeline with sample data

## Implementation Checklist

- [x] Repository structure created
- [x] Unified YAML schema designed
- [x] LaTeX template with variables
- [x] HTML template with placeholders
- [ ] Python build scripts complete
- [ ] CSS styling ported
- [ ] JavaScript files configured
- [ ] Test build with sample data
- [ ] Generate sample outputs to dist/

## Migration Strategy

1. **Phase 1: Data Unification**
   - Copy content from both repos to `data/resume.yaml`
   - Ensure all data is accessible in one place

2. **Phase 2: Template Integration**
   - Complete LaTeX template with all sections
   - Complete HTML template with all interactive elements

3. **Phase 3: Build Pipeline**
   - Test PDF generation
   - Test HTML generation
   - Fix any issues

4. **Phase 4: Automation**
   - Create npm scripts for easy building
   - Set up CI/CD if needed

5. **Phase 5: Output Customization**
   - Fine-tune LaTeX for print
   - Fine-tune HTML for web
