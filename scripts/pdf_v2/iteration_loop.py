"""Iteration loop - Compile, check page count, drop lowest priority."""

import subprocess
from pathlib import Path
from typing import Optional, Tuple, List, Any

try:
    from PyPDF2 import PdfReader
except ImportError:
    try:
        from pypdf import PdfReader
    except ImportError:
        PdfReader = None

from .config import (
    LATEX_COMPILER,
    OUTPUT_DIR,
    MAX_ITERATIONS,
    BASE_DIR,
)
from .content_selector import find_lowest_priority_item


def compile_latex(tex_path: Path, output_dir: Path) -> Tuple[bool, str]:
    """Compile LaTeX to PDF."""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    result = subprocess.run(
        [LATEX_COMPILER, "-interaction=nonstopmode", str(tex_path)],
        cwd=output_dir,
        capture_output=True,
        text=True,
        timeout=60
    )
    
    if result.returncode == 0:
        return True, ""
    
    error = result.stderr[-500:] if result.stderr else "Unknown error"
    return False, error


def get_page_count(pdf_path: Path) -> int:
    """Get page count from PDF."""
    if not pdf_path.exists():
        return 0
    
    if PdfReader is None:
        return 0
    
    try:
        reader = PdfReader(str(pdf_path))
        return len(reader.pages)
    except Exception:
        return 0


def compile_and_check(tex_path: Path, output_dir: Path) -> Tuple[bool, int, Path]:
    """Compile LaTeX and check page count."""
    pdf_path = tex_path.with_suffix(".pdf")
    
    success, error = compile_latex(tex_path, output_dir)
    
    if not success:
        print(f"  LaTeX compile error: {error}")
        return False, 0, pdf_path
    
    page_count = get_page_count(pdf_path)
    
    return True, page_count, pdf_path


def iterative_compile(
    content: List[Any],
    tex_path: Path,
    template_path: Path,
    output_dir: Path = None,
    max_iterations: int = MAX_ITERATIONS
) -> Tuple[Path, int]:
    """Main iteration loop."""
    if output_dir is None:
        output_dir = tex_path.parent
    
    current_content = content.copy()
    
    from .render_tailored import generate_latex
    
    for iteration in range(max_iterations):
        tex_file = generate_latex(current_content, template_path, tex_path)
        
        success, page_count, pdf_path = compile_and_check(tex_file, output_dir)
        
        if success and page_count == 1:
            print(f"✓ Compiled in {iteration + 1} iteration(s)")
            return pdf_path, iteration + 1
        
        if page_count > 1:
            candidate = find_lowest_priority_item(current_content)
            if candidate:
                content_id = candidate.get("id", "unknown")
                print(f"  Iteration {iteration + 1}: Dropping '{content_id}' (pages: {page_count})")
                current_content = [
                    item for item in current_content
                    if item.get("id") != content_id
                ]
            else:
                print(f"  No items to drop (pinned only)")
                break
        else:
            if not success:
                print(f"  Compile failed, using partial output")
            break
    
    print(f"⚠ Max iterations reached")
    
    if current_content:
        tex_file = generate_latex(current_content, template_path, tex_path)
        success, _, pdf_path = compile_and_check(tex_file, output_dir)
        if success:
            return pdf_path, iteration + 1
    
    return tex_path.with_suffix(".pdf"), iteration + 1