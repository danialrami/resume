#!/usr/bin/env python3
"""
Build script for generating both PDF and HTML resumes from YAML data.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from render_latex import generate_latex
from render_html import generate_html


def build_all():
    """Build both PDF and HTML resumes."""
    print("Building resume...")
    print("""
NOTE: 
- Audio files are automatically converted to OPUS format (~11x compression)
- Audio visualizations require the site to be served via HTTP
- Opening dist/html/index.html directly (file://) will play audio but without visualizations
- For full functionality, serve via HTTP: cd dist/html && python3 -m http.server 8080
- On Hostinger (or any web server), everything works including visualizations
- Set AUDIO_BASE_URL environment variable to load audio from a CDN/URL instead of local files
""")

    base_dir = Path(__file__).parent.parent
    data_path = base_dir / "data" / "resume.yaml"

    if not data_path.exists():
        print(f"Error: YAML file not found at {data_path}")
        sys.exit(1)

    # Load data
    import yaml

    with open(data_path, "r") as f:
        data = yaml.safe_load(f)

    print(f"Loaded resume data for: {data['name']}")

    # Generate outputs
    latex_output = generate_latex(data)
    html_output = generate_html(data)

    print(f"LaTeX output: {latex_output}")
    print(f"HTML output: {html_output}")
    print("Build complete!")


if __name__ == "__main__":
    build_all()
