#!/bin/bash
# build_html.sh - Build HTML resume only

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESUME_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Use venv Python
VENV_PYTHON="$RESUME_DIR/.venv/bin/python3"

cd "$RESUME_DIR"

echo "Building HTML resume..."
"$VENV_PYTHON" scripts/render_html.py

if [ -f "dist/html/index.html" ]; then
    echo "HTML generated: dist/html/index.html"
    
    # Copy PDF from assets if it exists
    if [ -f "assets/pdf/Ramirez-Daniel_resume.pdf" ]; then
        mkdir -p "dist/html/assets/pdf"
        cp "assets/pdf/Ramirez-Daniel_resume.pdf" "dist/html/assets/pdf/Ramirez-Daniel_resume.pdf"
        echo "PDF copied to: dist/html/assets/pdf/Ramirez-Daniel_resume.pdf"
    fi
    
    # Open in browser if on macOS
    if [[ "$OSTYPE" == "darwin"* ]]; then
        open dist/html/index.html
    fi
else
    echo "Error: HTML generation failed"
fi
