"""Tailored LaTeX rendering - uses V1 template as base."""

import yaml
from pathlib import Path


def escape_latex(text: str) -> str:
    """Escape special LaTeX characters."""
    if not text:
        return ""
    if isinstance(text, (int, float)):
        text = str(text)
    
    replacements = [
        ("&", r"\&"),
        ("%", r"\%"),
        ("$", r"\$"),
        ("#", r"\#"),
        ("_", r"\_"),
        ("{", r"\{"),
        ("}", r"\}"),
        ("~", r"\textasciitilde{}"),
        ("^", r"\textasciicircum{}"),
    ]
    for old, new in replacements:
        text = text.replace(old, new)
    return text


def generate_latex(
    content: list,
    template_path: Path,
    output_path: Path
) -> Path:
    """
    Generate tailored LaTeX.
    
    Uses existing V1 template as base, replaces only experience section.
    """
    import yaml
    
    base_dir = template_path.parent.parent.parent
    yaml_path = base_dir / "data" / "resume.yaml"
    yaml_data = yaml.safe_load(yaml_path.read_text())
    
    if not output_path.parent.exists():
        output_path.parent.mkdir(parents=True, exist_ok=True)
    
    if template_path.exists():
        template = template_path.read_text()
    else:
        from .render_tailored import LATEX_TEMPLATE
        template = LATEX_TEMPLATE
    
    # Build experience from selected content
    experience_items = []
    skills_set = set()
    
    for item in content:
        meta = item.get("metadata", {})
        company = meta.get("company", "")
        if not company:
            continue
        
        bullet = escape_latex(item.get("content", ""))[:180]
        
        # Add skills
        tags = meta.get("tags", "")
        if tags:
            for tag in tags.split(","):
                t = tag.strip()
                if t:
                    skills_set.add(t.capitalize())
        
        experience_items.append("\\resumeSubheading")
        experience_items.append(f"{{{escape_latex(meta.get('role', 'Sound Designer'))}}}{{{meta.get('dates', '2024–Present')}}}")
        experience_items.append(f"{{{escape_latex(company)}}}{{{escape_latex(meta.get('location', 'Remote'))}}}")
        experience_items.append("\\resumeItemListStart")
        experience_items.append(f"\\resumeItem{{{bullet}}}")
        experience_items.append("\\resumeItemListEnd")
    
    skills_str = ", ".join(sorted(skills_set)) if skills_set else "Wwise, FMOD"
    
    # Replace in template
    exp_section = '\n'.join(experience_items)
    profile = yaml_data.get('profile', 'Sound Designer')[0:300]
    
    template = template.replace('RESUME_EXPERIENCE', exp_section)
    template = template.replace('RESUME_PROFILE', escape_latex(profile))
    template = template.replace('RESUME_SKILLS', skills_str)
    
    output_path.write_text(template)
    return output_path