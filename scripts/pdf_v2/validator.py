"""Validation module for PDF output."""

import re
from pathlib import Path
from typing import Optional

from .config import (
    VALIDATION_ENABLED,
    VALIDATION_VISION_ENABLED,
    REFERENCE_PDF,
    PROMPTS_DIR,
    LLM_BASE_URL,
    LLM_API_KEY,
    LLM_MODEL,
    get_llm_client,
)


def check_placeholders(tex_path: Path) -> tuple[bool, list[str]]:
    """
    Check for remaining placeholders in generated LaTeX.
    
    Returns:
        (is_valid: bool, issues: list[str])
    """
    if not tex_path.exists():
        return False, ["Generated .tex file not found"]
    
    content = tex_path.read_text()
    
    # Pattern for RESUME_* placeholders
    pattern = r'RESUME_[A-Z_]+'
    matches = re.findall(pattern, content)
    
    if matches:
        return False, [f"Placeholders remain: {', '.join(set(matches))}"]
    
    return True, []


def check_template_placeholders(template_path: Path) -> tuple[bool, list[str]]:
    """Check template itself for unexpanded placeholders."""
    if not template_path.exists():
        return True, []  # Skip if no custom template
    
    content = template_path.read_text()
    pattern = r'RESUME_[A-Z_]+'
    matches = re.findall(pattern, content)
    
    if matches:
        return False, [f"Template has unexpanded placeholders: {', '.join(set(matches))}"]
    
    return True, []


def simple_validate(tex_path: Path, template_path: Path) -> tuple[bool, list[str]]:
    """
    Simple regex-based validation.
    
    Returns:
        (is_valid: bool, issues: list[str])
    """
    issues = []
    
    # Check generated file
    valid, new_issues = check_placeholders(tex_path)
    if not valid:
        issues.extend(new_issues)
    
    # Check template (warning only)
    valid, new_issues = check_template_placeholders(template_path)
    if not valid:
        issues.extend(new_issues)
    
    return len(issues) == 0, issues


def load_prompt(name: str) -> str:
    """Load a prompt from the prompts directory."""
    prompt_path = PROMPTS_DIR / f"{name}.md"
    if prompt_path.exists():
        return prompt_path.read_text()
    return ""


def vision_validate(generated_pdf: Path, reference_pdf: Path) -> tuple[bool, str, str]:
    """
    Vision-based validation using LLM.
    
    Requires a vision-capable model.
    
    Returns:
        (is_valid: bool, feedback: str, suggestions: str)
    """
    prompt_template = load_prompt("validate_output")
    
    # TODO: Implement vision validation
    # This would require:
    # 1. Converting PDF to image(s)
    # 2. Sending to vision model with reference
    # 3. Parsing response
    
    return True, "", "Vision validation not yet implemented"


def validate(
    tex_path: Path,
    template_path: Path,
    generated_pdf: Optional[Path] = None
) -> tuple[bool, str]:
    """
    Main validation function.
    
    Workflow:
    1. Simple regex check for placeholders
    2. Vision check if enabled and regex passes
    
    Returns:
        (is_valid: bool, feedback: str)
    """
    if not VALIDATION_ENABLED:
        return True, "Validation disabled"
    
    # Step 1: Regex check
    is_valid, issues = simple_validate(tex_path, template_path)
    
    if not is_valid:
        return False, "; ".join(issues)
    
    # Step 2: Vision check (if enabled)
    if VALIDATION_VISION_ENABLED and generated_pdf and generated_pdf.exists():
        prompt_template = load_prompt("validate_output")
        prompt = prompt_template.replace("{reference_path}", str(REFERENCE_PDF))
        
        # TODO: Implement vision call
        # is_valid, feedback, suggestions = vision_validate(generated_pdf, REFERENCE_PDF)
        
        # For now, pass through
        pass
    
    return True, "Validation passed"