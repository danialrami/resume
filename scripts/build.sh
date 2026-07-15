#!/bin/bash
# build.sh - Build the resume site (multi-lens HTML).
#
# NOTE: The old PDF pipelines (LaTeX + AI-tailored) are archived under archived/.
#       Tuned per-application resume PDFs are produced out-of-repo by
#       resume-builder-workspace; the deck PDF is hosted on Drive. This repo now
#       builds the website only.
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESUME_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
VENV_PYTHON="$RESUME_DIR/.venv/bin/python3"

cd "$RESUME_DIR"

echo "Building resume site..."
"$VENV_PYTHON" scripts/build_all.py

echo ""
echo "Build complete! Output in dist/html/ (/, /sound-design/, /infra/)."
