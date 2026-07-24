#!/bin/bash
# deploy.sh — DEPRECATED.
#
# The old flow force-pushed dist/html to a `hostinger` branch from a local machine.
# Deployment is now the website-portability pipeline: CI builds + verifies on push
# to main and publishes the proven artifact to the agnostic `site` branch, which
# the host (Cloudflare Pages / Hostinger) subscribes to. See README "Deployment".
#
# This script now only does the local half — build + prove — so you can eyeball the
# artifact before pushing. It intentionally does NOT push anything.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESUME_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$RESUME_DIR"

echo "deploy.sh is deprecated — running the local build + verify only."
echo "To ship: commit + push to main; CI publishes the verified artifact to 'site'."
echo ""

bash scripts/build
python3 scripts/verify

echo ""
echo "Artifact proven in dist/html/. Push to main to release."
