#!/bin/bash
# serve.sh - Build (optional) and serve the HTML resume locally

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESUME_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
VENV_PYTHON="$RESUME_DIR/.venv/bin/python3"
SERVE_DIR="$RESUME_DIR/dist/html"
PORT=8080
DO_BUILD=true
WATCH=false

usage() {
    echo "Usage: $0 [--no-build] [--watch]"
    echo ""
    echo "Options:"
    echo "  --no-build   Skip the build step"
    echo "  --watch      Rebuild automatically when source files change"
    exit 0
}

for arg in "$@"; do
    case "$arg" in
        --no-build) DO_BUILD=false ;;
        --watch)    WATCH=true ;;
        -h|--help)  usage ;;
    esac
done

build() {
    echo "Building..."
    cd "$RESUME_DIR"
    "$VENV_PYTHON" scripts/build_all.py
}

if $DO_BUILD; then
    build
fi

if [ ! -d "$SERVE_DIR" ]; then
    echo "Error: $SERVE_DIR does not exist. Run without --no-build first."
    exit 1
fi

cleanup() {
    echo ""
    echo "Stopping server..."
    if [ -n "$SERVER_PID" ]; then
        kill "$SERVER_PID" 2>/dev/null || true
    fi
    exit 0
}
trap cleanup SIGINT SIGTERM

echo "Serving at http://localhost:$PORT"
cd "$SERVE_DIR"
python3 -m http.server "$PORT" &>/dev/null &
SERVER_PID=$!

if [[ "$OSTYPE" == "darwin"* ]]; then
    open "http://localhost:$PORT"
fi

if $WATCH; then
    echo "Watching for changes in data/ and templates/ (Ctrl+C to stop)..."
    while true; do
        sleep 2
        LATEST_BUILD=$(find "$RESUME_DIR/dist/html" -maxdepth 1 -name "*.html" -printf '%T@\n' 2>/dev/null | sort -n | tail -1)
        LATEST_SOURCE=$(find "$RESUME_DIR/data" "$RESUME_DIR/templates" -type f -printf '%T@\n' 2>/dev/null | sort -n | tail -1)
        if [ -n "$LATEST_SOURCE" ] && [ -n "$LATEST_BUILD" ]; then
            if [ "$(echo "$LATEST_SOURCE > $LATEST_BUILD" | bc 2>/dev/null)" = "1" ] || \
               [ "$(echo "$LATEST_SOURCE > $LATEST_BUILD" | python3 -c 'import sys; print(int(float(sys.stdin.read().strip()) > 0))' 2>/dev/null)" = "1" ]; then
                echo "Changes detected, rebuilding..."
                build
                echo "Watching for changes..."
            fi
        fi
    done &
fi

wait "$SERVER_PID"
