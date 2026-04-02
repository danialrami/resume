#!/bin/bash
# deploy.sh - Build and deploy resume to hostinger branch
# 
# IMPORTANT: The main branch contains ONLY source code (templates, scripts, data).
#            The dist/ folder is built locally and deployed to hostinger branch only.
#            Never commit dist/ to main - it's in .gitignore.
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
echo "Checking for source code changes..."
echo "============================================"

git add -A
git reset dist/ 2>/dev/null || true

STAGED=$(git diff --cached --name-only 2>/dev/null | wc -l | tr -d ' ')
UNSTAGED=$(git diff --name-only 2>/dev/null | wc -l | tr -d ' ')

if [ "$STAGED" -eq 0 ] && [ "$UNSTAGED" -eq 0 ]; then
    echo "No source code changes to commit."
else
    echo "Committing source code changes..."
    git commit -m "Production build $(date +'%Y-%m-%d %H:%M:%S')"
    echo "Pushing source changes to origin main..."
    git push origin main
fi

echo ""
echo "============================================"
echo "Deploying to hostinger branch..."
echo "============================================"

echo "Creating clean deploy from dist/html..."
TEMP_DIR=$(mktemp -d)
cp -r dist/html/* "$TEMP_DIR/"

cd "$TEMP_DIR"
git init
git add -A
git commit -m "Deploy $(date +'%Y-%m-%d %H:%M:%S')"

# Add remote
GIT_REPO=$(git -C "$RESUME_DIR" remote get-url origin)
git remote add origin "$GIT_REPO"

echo "Pushing to origin $DEPLOY_BRANCH..."
git push origin HEAD:$DEPLOY_BRANCH --force

cd "$RESUME_DIR"
rm -rf "$TEMP_DIR"

echo ""
echo "============================================"
echo "Deployment complete!"
echo "============================================"
echo "Hostinger branch updated with latest build."
echo ""
echo "NOTE: The hostinger branch contains ONLY the built website."
echo "      Source code remains on the main branch."
