#!/usr/bin/env python3
"""
Render LaTeX resume from YAML data.
"""

import yaml
from pathlib import Path

def load_yaml_data(yaml_path: str) -> dict:
    """Load YAML data using PyYAML."""
    with open(yaml_path, 'r') as f:
        return yaml.safe_load(f)

def escape_latex(text: str) -> str:
    """Escape special LaTeX characters."""
    if not text:
        return ''
    
    replacements = [
        ('&', r'\&'),
        ('%', r'\%'),
        ('$', r'\$'),
        ('#', r'\#'),
        ('_', r'\_'),
        ('{', r'\{'),
        ('}', r'\}'),
        ('~', r'\textasciitilde{}'),
        ('^', r'\textasciicircum{}'),
    ]
    for old, new in replacements:
        text = text.replace(old, new)
    return text

def render_contact_latex(contact: dict) -> str:
    """Render contact information line."""
    email = contact.get('email', '')
    phone = contact.get('phone', '')
    website = contact.get('website', '')
    portfolio = contact.get('portfolio', '')
    
    parts = []
    if email:
        parts.append(rf'\href{{mailto:{email}}}{{\faEnvelope\, {email}}}')
    if phone:
        parts.append(rf'\href{{tel:{phone}}}{{\faMobile\, {phone}}}')
    if website:
        parts.append(rf'\href{{{website}}}{{\faGlobe\, {website}}}')
    if portfolio:
        parts.append(rf'\href{{{portfolio}}}{{\faFile\, {portfolio}}}')
    
    return ' $|$ '.join(parts)

def render_experience_latex(experience: list) -> str:
    """Render experience section."""
    lines = []
    for exp in experience:
        company = escape_latex(exp.get('company', ''))
        role = escape_latex(exp.get('role', ''))
        location = escape_latex(exp.get('location', ''))
        dates = escape_latex(exp.get('dates', ''))
        
        lines.append(f'\\resumeSubheading{{{role}}}{{{company}}}{{{location}}}{{{dates}}}')
        
        bullets = exp.get('bullets', [])
        if bullets:
            lines.append('\\resumeItemListStart')
            for bullet in bullets:
                lines.append(f'\\resumeItem{{{escape_latex(bullet)}}}')
            lines.append('\\resumeItemListEnd')
    
    return '\n'.join(lines)

def render_skills_latex(skills: dict) -> str:
    """Render skills section."""
    # Audio Software
    audio_software = skills.get('audio_software', {})
    items = ', '.join(item.get('name', '') for item in audio_software.get('items', []))
    audio_skill = escape_latex(items)
    
    # Modular
    modular = skills.get('modular', {})
    items = ', '.join(item.get('name', '') for item in modular.get('items', []))
    modular_skill = escape_latex(items)
    
    # Implementation
    impl = skills.get('implementation', {})
    items = ', '.join(item.get('name', '') for item in impl.get('items', []))
    impl_skill = escape_latex(items)
    
    # Game Engines
    engines = skills.get('game_engines', {})
    items = ', '.join(item.get('name', '') for item in engines.get('items', []))
    engines_skill = escape_latex(items)
    
    # Scripting
    scripting = skills.get('scripting', {})
    items = ', '.join(item.get('name', '') for item in scripting.get('items', []))
    script_skill = escape_latex(items)
    
    # Node-based
    node = skills.get('node_based', {})
    items = ', '.join(item.get('name', '') for item in node.get('items', []))
    node_skill = escape_latex(items)
    
    # DAWs
    daws = skills.get('daws', {})
    items = ', '.join(item.get('name', '') for item in daws.get('items', []))
    daw_skill = escape_latex(items)
    
    return {
        'audio_software': audio_skill,
        'modular': modular_skill,
        'implementation': impl_skill,
        'game_engines': engines_skill,
        'scripting': script_skill,
        'node_based': node_skill,
        'daws': daw_skill
    }

def render_education_latex(education: list) -> str:
    """Render education section."""
    lines = []
    for edu in education:
        institution = escape_latex(edu.get('institution', ''))
        degree = escape_latex(edu.get('degree', ''))
        location = escape_latex(edu.get('location', ''))
        period = escape_latex(edu.get('period', ''))
        
        lines.append(f'\\resumeEducationHeading{{{institution}}}{{{degree}}}{{{location}}}{{{period}}}')
    
    return '\n'.join(lines)

def render_projects_latex(projects: list) -> str:
    """Render projects section."""
    lines = []
    for proj in projects:
        name = escape_latex(proj.get('name', ''))
        desc = '; '.join(escape_latex(d) for d in proj.get('description', []))
        
        lines.append(f'\\resumeProjectHeading{{{name}}}{{}}')
        if desc:
            lines.append('\\resumeItemListStart')
            lines.append(f'\\resumeItem{{{desc}}}')
            lines.append('\\resumeItemListEnd')
    
    return '\n'.join(lines)

def render_certifications_latex(certifications: list) -> str:
    """Render certifications section."""
    lines = []
    for cert in certifications:
        name = escape_latex(cert.get('name', ''))
        
        lines.append(f'\\resumeEducationHeading{{{name}}}{{ certification }}{{}}{{}}')
    
    return '\n'.join(lines)

def render_profile_latex(profile: str) -> str:
    """Render profile text."""
    # Profile comes from YAML as single string with newlines
    # Need to split into items
    lines = profile.strip().split('\n')
    cleaned = [line.strip() for line in lines if line.strip()]
    return '\\item ' + '\\item '.join(escape_latex(line) for line in cleaned)

def generate_latex(data: dict) -> str:
    """Generate LaTeX file from data."""
    base_dir = Path(__file__).parent.parent
    template_path = base_dir / 'templates' / 'latex' / 'resume.tex'
    
    with open(template_path, 'r') as f:
        template = f.read()
    
    # Build substitution map
    skills = render_skills_latex(data.get('skills', {}))
    
    substitutions = {
        'NAME': escape_latex(data.get('name', '')),
        'TITLE': escape_latex(data.get('title', '')),
        'CONTACT_LINE': render_contact_latex(data.get('contact', {})),
        'PROFILE_TEXT': render_profile_latex(data.get('profile', '')),
        'EXPERIENCE': render_experience_latex(data.get('experience', [])),
        'SKILL_AUDIO_SOFTWARE': skills['audio_software'],
        'SKILL_MODULAR': skills['modular'],
        'SKILL_IMPLEMENTATION': skills['implementation'],
        'SKILL_GAME_ENGINES': skills['game_engines'],
        'SKILL_SCRIPTING': skills['scripting'],
        'SKILL_NODE_BASED': skills['node_based'],
        'SKILL_DAWS': skills['daws'],
        'EDUCATION': render_education_latex(data.get('education', [])),
        'PROJECTS': render_projects_latex(data.get('projects', [])),
    }
    
    # Replace placeholders (use single backslash to match template)
    for placeholder, value in substitutions.items():
        search = r'RESUME_' + placeholder
        template = template.replace(search, value)
    
    # Save output
    output_path = base_dir / 'dist' / 'pdf' / 'resume.tex'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        f.write(template)
    
    return str(output_path)

if __name__ == '__main__':
    base_dir = Path(__file__).parent.parent
    data_path = base_dir / 'data' / 'resume.yaml'
    
    if not data_path.exists():
        print(f"Error: YAML file not found at {data_path}")
        import sys
        sys.exit(1)
    
    data = load_yaml_data(str(data_path))
    output_path = generate_latex(data)
    print(f"LaTeX generated: {output_path}")
