#!/bin/bash
# build_html.sh - Build the multi-lens HTML resume.
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESUME_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
VENV_PYTHON="$RESUME_DIR/.venv/bin/python3"

cd "$RESUME_DIR"

echo "Building HTML resume (multi-lens)..."
"$VENV_PYTHON" scripts/build_all.py

if [ -f "dist/html/index.html" ]; then
    echo "HTML generated:"
    echo "  dist/html/index.html               (/)"
    echo "  dist/html/sound-design/index.html  (/sound-design/)"
    echo "  dist/html/infra/index.html         (/infra/)"

    # Open in browser if on macOS
    if [[ "$OSTYPE" == "darwin"* ]]; then
        open dist/html/index.html
    fi
else
    echo "Error: HTML generation failed"
    exit 1
fi
