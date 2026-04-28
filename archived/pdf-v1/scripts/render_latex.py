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
    
    # Convert to string if number
    if isinstance(text, (int, float)):
        text = str(text)
    
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
    email = escape_latex(contact.get('email', ''))
    phone = contact.get('phone', '')
    website = contact.get('website', '')
    portfolio = contact.get('portfolio', '')
    
    # Format phone without parentheses for the href
    phone_href = phone.replace('(', '').replace(')', '').replace('-', '').replace(' ', '')
    
    parts = []
    if email:
        parts.append(rf'\href{{mailto:{email}}}{{\faEnvelope\, {email}}}')
    if phone:
        parts.append(rf'\href{{tel:{phone_href}}}{{\faMobile\, {phone}}}')
    if website:
        parts.append(rf'\href{{{website}}}{{\faGlobe\, {escape_latex(website)}}}')
    if portfolio:
        parts.append(rf'\href{{{portfolio}}}{{\faFile\, {escape_latex(portfolio)}}}')
    
    return ' $|$ '.join(parts)

def render_experience_latex(experience: list) -> str:
    """Render experience section."""
    lines = []
    for exp in experience:
        company = escape_latex(exp.get('company', ''))
        role = escape_latex(exp.get('role', ''))
        location = escape_latex(exp.get('location', ''))
        dates = escape_latex(str(exp.get('dates', '')))
        
        # Format: {role}{dates}{company}{location}
        lines.append('\\resumeSubheading')
        lines.append(f'{{{role}}}{{{dates}}}')
        lines.append(f'{{{company}}}{{{location}}}')
        
        # Use 'description' field from YAML
        bullets = exp.get('description', [])
        if bullets:
            lines.append('\\resumeItemListStart')
            for bullet in bullets:
                lines.append(f'\\resumeItem{{{escape_latex(bullet)}}}')
            lines.append('\\resumeItemListEnd')
    
    return '\n'.join(lines)

def render_skills_latex(skills: list) -> str:
    """Render skills section from list format."""
    # Build skill categories
    audio_software = ''
    daws = ''
    game_engines = ''
    scripting = ''
    node_based = ''
    specialties = ''
    
    for skill in skills:
        category = skill.get('category', '')
        items = skill.get('list', [])
        
        if 'Audio Software' in category:
            audio_software = ', '.join(items)
        elif 'DAW' in category:
            daws = ', '.join(items)
        elif 'Game Engine' in category:
            game_engines = ', '.join(items)
        elif 'Scripting' in category:
            scripting = ', '.join(items)
        elif 'Node' in category or 'based' in category.lower():
            node_based = ', '.join(items)
        elif 'Specialty' in category:
            specialties = ', '.join(items)
    
    return {
        'implementation': escape_latex(audio_software),
        'daws': escape_latex(daws),
        'game_engines': escape_latex(game_engines),
        'scripting': escape_latex(scripting),
        'node_based': escape_latex(node_based),
        'specialties': escape_latex(specialties)
    }

def render_education_latex(education: list) -> str:
    """Render education section."""
    lines = []
    for edu in education:
        institution = escape_latex(edu.get('school', ''))
        degree = escape_latex(str(edu.get('degree', '')))
        location = escape_latex(str(edu.get('location', '')))
        period = escape_latex(str(edu.get('dates', '')))
        
        lines.append('\\resumeEducationHeading')
        lines.append(f'{{{institution}}}{{{period}}}')
        lines.append(f'{{{degree}}}{{{location}}}')
    
    return '\n'.join(lines)

def render_certifications_latex(certifications: list) -> str:
    """Render certifications section."""
    if not certifications:
        return ''
    
    # Extract certification names
    cert_names = ', '.join(escape_latex(str(cert.get('name', ''))) for cert in certifications)
    
    lines = []
    lines.append('\\resumeEducationHeading')
    lines.append(f'{{Certifications}}{{}}')
    lines.append(f'{{{cert_names}}}{{}}')
    
    return '\n'.join(lines)

def render_projects_latex(projects: list) -> str:
    """Render projects section."""
    lines = []
    for proj in projects:
        name = escape_latex(str(proj.get('name', '')))
        
        lines.append('\\resumeProjectHeading')
        lines.append(f'{{{name}}}{{}}')
        
        bullets = proj.get('description', [])
        
        if bullets:
            lines.append('\\resumeItemListStart')
            for bullet in bullets:
                lines.append(f'\\resumeItem{{{escape_latex(str(bullet))}}}')
            lines.append('\\resumeItemListEnd')
    
    return '\n'.join(lines)

def render_profile_latex(profile: str) -> str:
    """Render profile text."""
    # Profile comes from YAML as single string with newlines
    lines = str(profile).strip().split('\n')
    cleaned = [line.strip() for line in lines if line.strip()]
    # Join into single paragraph (original doesn't use \item for profile)
    return ' '.join(cleaned)

def generate_latex(data: dict) -> str:
    """Generate LaTeX file from data."""
    base_dir = Path(__file__).parent.parent
    template_path = base_dir / 'templates' / 'latex' / 'resume.tex'
    
    with open(template_path, 'r') as f:
        template = f.read()
    
    # Build substitution map
    skills = render_skills_latex(data.get('skills', []))
    
    substitutions = {
        'NAME': escape_latex(str(data.get('name', ''))),
        'TITLE': escape_latex(str(data.get('title', ''))),
        'CONTACT_LINE': render_contact_latex(data.get('contact', {})),
        'PROFILE': render_profile_latex(data.get('profile', '')),
        'EXPERIENCE': render_experience_latex(data.get('experience', [])),
        'SKILLS_IMPLEMENTATION': skills['implementation'],
        'SKILLS_DAWS': skills['daws'],
        'SKILLS_GAME_ENGINES': skills['game_engines'],
        'SKILLS_SCRIPTING': skills['scripting'],
        'SKILLS_NODE_BASED': skills['node_based'],
        'SKILLS_SPECIALTIES': skills['specialties'],
        'EDUCATION': render_education_latex(data.get('education', [])),
        'CERTIFICATIONS_SECTION': render_certifications_latex(data.get('certifications', [])),
        'PROJECTS': render_projects_latex(data.get('projects', [])),
    }
    
    # Replace placeholders
    for placeholder, value in substitutions.items():
        search = 'RESUME_' + placeholder
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
