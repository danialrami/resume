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
    
    base_dir = Path(__file__).parent.parent
    data_path = base_dir / 'data' / 'resume.yaml'
    
    if not data_path.exists():
        print(f"Error: YAML file not found at {data_path}")
        sys.exit(1)
    
    # Load data
    import yaml
    with open(data_path, 'r') as f:
        data = yaml.safe_load(f)
    
    print(f"Loaded resume data for: {data['name']}")
    
    # Generate outputs
    latex_output = generate_latex(data)
    html_output = generate_html(data)
    
    print(f"LaTeX output: {latex_output}")
    print(f"HTML output: {html_output}")
    print("Build complete!")

if __name__ == '__main__':
    build_all()
