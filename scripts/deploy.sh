#!/bin/bash
# deploy.sh - Build and deploy resume to hostinger branch
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESUME_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$RESUME_DIR"

DEPLOY_BRANCH="hostinger"
VENV_PYTHON="$RESUME_DIR/.venv/bin/python3"

echo "============================================"
echo "Building resume for production deployment..."
echo "============================================"
echo ""
echo "NOTE: Audio files are automatically converted to OPUS format (~11x smaller)"
echo "      Set AUDIO_BASE_URL env var to use URL-based audio instead"
echo ""

"$VENV_PYTHON" scripts/build_all.py

echo ""
echo "============================================"
echo "Committing changes to main branch..."
echo "============================================"

git add -A
if git diff --cached --quiet && git diff --quiet; then
    echo "No changes to commit."
else
    git commit -m "Production build $(date +'%Y-%m-%d %H:%M:%S')"
    echo "Pushing to origin main..."
    git push origin main
fi

echo ""
echo "============================================"
echo "Deploying to hostinger branch..."
echo "============================================"

echo "Splitting dist/html to $DEPLOY_BRANCH branch..."
TEMP_BRANCH="temp-$(date +%s)"
git add dist/html --force
git commit -m "Deploy $(date +'%Y-%m-%d %H:%M:%S')" || true

if ! git subtree split --prefix dist/html -b "$TEMP_BRANCH"; then
    echo "Subtree split failed."
    git reset HEAD dist/html
    git reset --soft HEAD~1 2>/dev/null || true
    exit 1
fi

echo "Force pushing to origin $DEPLOY_BRANCH..."
if ! git push origin "$TEMP_BRANCH:hostinger" --force; then
    echo "Failed to push to hostinger branch."
    git branch -D "$TEMP_BRANCH" 2>/dev/null || true
    git reset --soft HEAD~1 2>/dev/null || true
    exit 1
fi

git branch -D "$TEMP_BRANCH" 2>/dev/null || true
git reset --soft HEAD~1 2>/dev/null || true

echo ""
echo "============================================"
echo "Deployment complete!"
echo "============================================"
echo "Hostinger branch updated with latest build."
