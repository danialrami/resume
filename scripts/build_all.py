#!/usr/bin/env python3
"""
Build the multi-lens HTML resume.

Reads data/site.yaml (route slugs + per-lens data files + deck config) and emits a
static page per route into dist/html/ (/, /sound-design/, /infra/), each carrying the
persistent-audio shell + the client-side lens router. See render_html.build_site.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from render_html import build_site


def build_all():
    print("Building multi-lens HTML resume...")
    outputs = build_site()
    print(f"Build complete — {len(outputs)} lens page(s) in dist/html/.")


if __name__ == "__main__":
    build_all()
