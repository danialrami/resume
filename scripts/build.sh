#!/bin/bash
# build.sh - Build both PDF and HTML resumes

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESUME_DIR="$(dirname "$SCRIPT_DIR")"

# Use venv Python
VENV_PYTHON="$RESUME_DIR/.venv/bin/python3"

echo "Building resume..."
"$VENV_PYTHON" "$RESUME_DIR/scripts/build_all.py"

# Check if LaTeX build is desired
if command -v pdflatex &> /dev/null; then
    echo ""
    echo "LaTeX installed - generating PDF..."
    
    if [ -f "$RESUME_DIR/dist/pdf/resume.tex" ]; then
        cd "$RESUME_DIR/dist/pdf"
        pdflatex -interaction=nonstopmode resume.tex
        echo "PDF generated: $RESUME_DIR/dist/pdf/resume.pdf"
    else
        echo "Warning: dist/pdf/resume.tex not found. Run build_all first."
    fi
else
    echo ""
    echo "LaTeX not found. Install MacTeX or TeX Live for PDF generation."
    echo "Skipped PDF compilation (HTML only)."
fi
