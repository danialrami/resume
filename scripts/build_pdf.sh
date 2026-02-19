#!/bin/bash
# build_pdf.sh - Build PDF resume only

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESUME_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Use venv Python
VENV_PYTHON="$RESUME_DIR/.venv/bin/python3"

cd "$RESUME_DIR"

echo "Building PDF resume..."
"$VENV_PYTHON" scripts/render_latex.py

# Compile with pdflatex if available
if command -v pdflatex &> /dev/null; then
    cd dist/pdf
    pdflatex -interaction=nonstopmode resume.tex
    echo "PDF generated: dist/pdf/resume.pdf"
    cd "$RESUME_DIR"
else
    echo "Warning: pdflatex not found. Install MacTeX or TeX Live."
fi
