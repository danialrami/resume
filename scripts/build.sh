#!/bin/bash
# build.sh - Build both PDF and HTML resumes

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESUME_DIR="$(dirname "$SCRIPT_DIR")"

# Use venv Python
VENV_PYTHON="$RESUME_DIR/.venv/bin/python3"

cd "$RESUME_DIR"

echo "Building resume..."
"$VENV_PYTHON" scripts/build_all.py

# Compile with xelatex (required for fontspec)
COMPILE_CMD="xelatex"
if ! command -v xelatex &> /dev/null; then
    COMPILE_CMD="pdflatex"
    echo "Warning: xelatex not found, trying pdflatex..."
fi

cd dist/pdf
$COMPILE_CMD -interaction=nonstopmode resume.tex
echo "PDF generated: $RESUME_DIR/dist/pdf/resume.pdf"
cd "$RESUME_DIR"

echo ""
echo "Build complete!"
