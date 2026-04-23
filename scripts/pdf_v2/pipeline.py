"""Main pipeline orchestration."""

import click
import sys
from pathlib import Path

from .config import (
    BASE_DIR,
    OUTPUT_DIR,
    MAX_BULLETS,
    MAX_ITERATIONS,
    test_connection as test_llm,
)
from .job_loader import load_jd, extract_keywords
from .semantic_search import search
from .content_selector import select_content
from .llm_rewriter import rewrite_all_bullets
from .iteration_loop import iterative_compile


@click.command()
@click.option(
    "--jd", 
    required=True, 
    help="Job description URL or .txt file path"
)
@click.option(
    "--output", 
    default="dist/pdf/tailored_resume.pdf",
    help="Output PDF path"
)
@click.option(
    "--max-bullets", 
    default=12,
    help="Maximum bullets before iteration"
)
@click.option(
    "--no-rewrite",
    is_flag=True,
    help="Skip LLM rewriting"
)
def main(jd: str, output: str, max_bullets: int, no_rewrite: bool):
    """Main pipeline entry point."""
    
    print("=" * 50)
    print("PDF V2 Pipeline - Dynamic Resume Generation")
    print("=" * 50)
    
    print(f"\n[1/5] Loading job description...")
    try:
        jd_data = load_jd(jd)
        jd_text = jd_data["text"]
        
        if jd_data.get("source_type") == "url":
            print(f"  Loaded from URL: {jd_data['url']}")
        else:
            print(f"  Loaded from file: {jd}")
        
        if len(jd_text) < 100:
            print(f"  ERROR: JD text too short ({len(jd_text)} chars)")
            sys.exit(1)
    except Exception as e:
        print(f"  ERROR: Failed to load JD: {e}")
        sys.exit(1)
    
    print(f"\n[2/5] Searching for relevant content...")
    search_results = search(jd_text, n_results=max_bullets + 5)
    print(f"  Found {len(search_results)} relevant bullets")
    
    if not search_results:
        print("  WARNING: No search results, using fallback")
        from .semantic_search import get_all_bullets
        search_results = get_all_bullets()[:max_bullets]
    
    print(f"\n[3/5] Selecting content...")
    selected = select_content(search_results, max_bullets=max_bullets)
    print(f"  Selected {len(selected)} bullets")
    
    if not no_rewrite:
        print(f"\n[4/5] Rewriting bullets with LLM...")
        try:
            test_llm()
            print("  LLM connection OK")
            
            for i, item in enumerate(selected[:5]):
                print(f"  Rewriting bullet {i+1}/5...")
            
            rewritten = rewrite_all_bullets(selected, jd_text)
            
            rewritten_count = sum(1 for r in rewritten if r.get("was_rewritten"))
            print(f"  Rewrote {rewritten_count} bullets")
            
            content_for_latex = [
                {"content": r["rewritten"], "metadata": r["metadata"], "id": r["id"]}
                for r in rewritten
            ]
        except Exception as e:
            print(f"  WARNING: LLM rewrite failed: {e}")
            print("  Using original bullets")
            content_for_latex = selected
    else:
        content_for_latex = selected
    
    print(f"\n[5/5] Compiling with iteration loop...")
    output_path = BASE_DIR / output
    template_path = BASE_DIR / "templates" / "latex" / "resume_tailored.tex"
    tex_path = output_path.with_suffix(".tex")
    
    if not template_path.exists():
        print("  WARNING: Template not found, using default")
        template_path = None
    
    try:
        pdf_path, iterations = iterative_compile(
            content_for_latex,
            tex_path,
            template_path or output_path.with_suffix(".tex"),
            OUTPUT_DIR,
            MAX_ITERATIONS
        )
        
        if pdf_path.exists():
            import shutil
            shutil.copy(pdf_path, output_path)
            print(f"\n✓ Success! Output: {output_path}")
        else:
            print(f"\n✗ Error: PDF not generated")
            sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()