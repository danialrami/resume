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

if git branch --list | grep -q "$DEPLOY_BRANCH"; then
    echo "Removing existing $DEPLOY_BRANCH branch..."
    git branch -D "$DEPLOY_BRANCH"
fi

echo "Splitting dist/html to $DEPLOY_BRANCH branch..."
git add dist/html --force
if ! git subtree split --prefix dist/html -b "$DEPLOY_BRANCH"; then
    echo "Subtree split failed."
    git reset HEAD dist/html
    exit 1
fi
git reset HEAD dist/html

echo "Force pushing to origin $DEPLOY_BRANCH..."
if ! git push origin "$DEPLOY_BRANCH:hostinger" --force; then
    echo "Failed to push to hostinger branch."
    git branch -D "$DEPLOY_BRANCH"
    exit 1
fi

git branch -D "$DEPLOY_BRANCH"

echo ""
echo "============================================"
echo "Deployment complete!"
echo "============================================"
echo "Hostinger branch updated with latest build."
