#!/usr/bin/env python3
"""
Render HTML resume from YAML data.
"""

import yaml
from pathlib import Path

def load_yaml_data(yaml_path: str) -> dict:
    """Load YAML data using PyYAML."""
    with open(yaml_path, 'r') as f:
        return yaml.safe_load(f)

def escape_html(text: str) -> str:
    """Escape HTML special characters."""
    if not text:
        return ''
    
    replacements = [
        ('&', '&amp;'),
        ('<', '&lt;'),
        ('>', '&gt;'),
        ('"', '&quot;'),
        ("'", '&#039;'),
    ]
    for old, new in replacements:
        text = text.replace(old, new)
    return text

def render_contact_html(contact: dict) -> str:
    """Render contact information."""
    email = escape_html(contact.get('email', ''))
    phone = escape_html(contact.get('phone', ''))
    
    parts = []
    if email:
        parts.append(f'<div class="contact-item"><i class="fas fa-envelope"></i><a href="mailto:{email}">{email}</a></div>')
    if phone:
        parts.append(f'<div class="contact-item"><i class="fas fa-phone"></i><a href="tel:{phone}">{phone}</a></div>')
    
    return '\n'.join(parts)

def render_experience_html(experience: list) -> str:
    """Render experience section."""
    html = []
    for exp in experience:
        company = escape_html(exp.get('company', ''))
        role = escape_html(exp.get('role', ''))
        location = escape_html(exp.get('location', ''))
        dates = escape_html(exp.get('dates', ''))
        
        html.append('<div class="timeline-item">')
        html.append('    <div class="timeline-dot"></div>')
        html.append('    <div class="timeline-content">')
        
        bullets = exp.get('bullets', [])
        if len(bullets) <= 1:
            html.append(f'    <h3>{role} | {company}</h3>')
            if location or dates:
                date_line = []
                if location:
                    date_line.append(location)
                if dates:
                    date_line.append(dates)
                html.append(f'    <p class="timeline-date">{"; ".join(date_line)}</p>')
            if bullets:
                html.append(f'    <ul><li>{escape_html(bullets[0])}</li></ul>')
        else:
            html.append(f'    <h3>{role} | {company}</h3>')
            date_line = []
            if location:
                date_line.append(location)
            if dates:
                date_line.append(dates)
            html.append(f'    <p class="timeline-date">{"; ".join(date_line)}</p>')
            html.append('    <ul>')
            for bullet in bullets:
                html.append(f'        <li>{escape_html(bullet)}</li>')
            html.append('    </ul>')
        
        html.append('    </div>')
        html.append('</div>')
    
    return '\n'.join(html)

def render_skills_html(skills: dict) -> str:
    """Render skills sections."""
    html = []
    
    # Audio Software & Hardware
    audio_software = skills.get('audio_software', {})
    items = audio_software.get('items', [])
    if items:
        html.append('<div class="skills-category">')
        html.append('    <h3>Audio Software & Hardware</h3>')
        html.append('    <div class="skills-grid">')
        
        for item in items:
            name = escape_html(item.get('name', ''))
            desc = escape_html(item.get('description', ''))
            html.append(f'<div class="skill-item" data-sound="audio">')
            html.append(f'    <div class="skill-icon"><i class="fas fa-music"></i></div>')
            html.append(f'    <div class="skill-name">{name}</div>')
            if desc:
                html.append(f'    <div class="skill-details">{desc}</div>')
            html.append('</div>')
        
        html.append('    </div>')
        html.append('</div>')
    
    # Development Tools
    dev_tools = skills.get('dev_tools', {})
    items = dev_tools.get('items', []) if dev_tools else []
    
    html.append('<div class="skills-category">')
    html.append('    <h3>Development Tools</h3>')
    html.append('    <div class="skills-grid">')
    
    if items:
        for item in items:
            name = escape_html(item.get('name', ''))
            desc = escape_html(item.get('description', ''))
            html.append(f'<div class="skill-item" data-sound="dev">')
            html.append(f'    <div class="skill-icon"><i class="fas fa-code"></i></div>')
            html.append(f'    <div class="skill-name">{name}</div>')
            if desc:
                html.append(f'    <div class="skill-details">{desc}</div>')
            html.append('</div>')
    
    html.append('    </div>')
    html.append('</div>')
    
    return '\n'.join(html)

def render_education_html(education: list) -> str:
    """Render education section."""
    html = []
    
    for edu in education:
        institution = escape_html(edu.get('institution', ''))
        degree = escape_html(edu.get('degree', ''))
        location = escape_html(edu.get('location', ''))
        period = escape_html(edu.get('period', ''))
        
        html.append('<div class="education-item">')
        html.append(f'    <h3>{institution}</h3>')
        html.append(f'    <p class="education-degree">{degree}</p>')
        
        details = []
        if location:
            details.append(location)
        if period:
            details.append(period)
        
        if details or edu.get('notes'):
            html.append(f'    <p class="education-location">{"; ".join(details)}</p>')
            if edu.get('notes'):
                html.append(f'    <p>{escape_html(edu["notes"])}</p>')
        
        html.append('</div>')
    
    return '\n'.join(html)

def render_certifications_html(certifications: list) -> str:
    """Render certifications section."""
    html = []
    
    for cert in certifications:
        name = escape_html(cert.get('name', ''))
        
        html.append('<div class="certification-item">')
        html.append(f'    <h3>{name}</h3>')
        
        bullets = cert.get('items', [])
        if bullets:
            html.append('    <ul>')
            for bullet in bullets:
                html.append(f'        <li>{escape_html(bullet)}</li>')
            html.append('    </ul>')
        
        html.append('</div>')
    
    return '\n'.join(html)

def render_projects_html(projects: list) -> str:
    """Render projects section."""
    html = []
    
    for proj in projects:
        name = escape_html(proj.get('name', ''))
        
        # Determine icon based on category
        icons = {
            'hardware': 'fa-microchip',
            'scripting': 'fa-code',
            'docker': 'fa-server',
            'automation': 'fa-cogs',
        }
        
        icon = 'fa-code'
        for keyword, i in icons.items():
            if keyword.lower() in name.lower():
                icon = i
                break
        
        html.append('<div class="project-item">')
        html.append(f'<div class="project-icon"><i class="fas {icon}"></i></div>')
        html.append(f'<h3>{name}</h3>')
        
        desc = proj.get('description', [])
        if desc:
            html.append('<ul>')
            for item in desc:
                html.append(f'<li>{escape_html(item)}</li>')
            html.append('</ul>')
        
        html.append('</div>')
    
    return '\n'.join(html)

def render_social_links_html(contact: dict) -> str:
    """Render social media links."""
    html = []
    
    github = contact.get('github', '')
    linkedin = contact.get('linkedin', '')
    website = contact.get('website', '')
    portfolio = contact.get('portfolio', '')
    
    if github:
        html.append(f'<a href="https://github.com/{github}" class="social-link" title="GitHub" target="_blank"><i class="fab fa-github"></i></a>')
    
    if linkedin:
        html.append(f'<a href="https://www.linkedin.com/in/{linkedin}" class="social-link" title="LinkedIn" target="_blank"><i class="fab fa-linkedin"></i></a>')
    
    if website and 'lufs' in website.lower():
        html.append(f'<a href="{website}" class="social-link custom-icon" title="danialrami.com" target="_blank"><img src="Asset-3.svg" alt="Website Icon"></a>')
    
    if portfolio and 'danialrami' in portfolio.lower():
        html.append(f'<a href="{portfolio}" class="social-link custom-icon small-icon" title="danialrami.com" target="_blank"><img src="svg-cloud-25.svg" alt="Website Icon"></a>')
    
    return '\n'.join(html)

def render_profile_html(profile: str) -> str:
    """Render profile text for HTML."""
    lines = [line.strip() for line in profile.split('\n') if line.strip()]
    return escape_html(' '.join(lines))

def generate_html(data: dict) -> str:
    """Generate HTML file from data."""
    base_dir = Path(__file__).parent.parent
    template_path = base_dir / 'templates' / 'html' / 'index.html'
    
    with open(template_path, 'r') as f:
        template = f.read()
    
    # Build substitution map
    substitutions = {
        'NAME': escape_html(data.get('name', '')),
        'TITLE': escape_html(data.get('title', '')),
        'EMAIL': escape_html(data.get('contact', {}).get('email', '')),
        'BRAND_NAME': 'DANIALRAMI',
        'PROFILE_ABOUT': render_profile_html(data.get('profile', '')),
        'SKILLS_AUDIO_GRID': render_skills_html(data.get('skills', {})),
        'EXPERIENCE_TIMELINE': render_experience_html(data.get('experience', [])),
        'EDUCATION_ITEMS': render_education_html(data.get('education', [])),
        'CERTIFICATIONS': render_certifications_html(data.get('certifications', [])),
        'PROJECTS_GRID': render_projects_html(data.get('projects', [])),
        'SOCIAL_LINKS': render_social_links_html(data.get('contact', {})),
    }
    
    # Replace placeholders
    for placeholder, value in substitutions.items():
        search = 'RESUME_' + placeholder
        template = template.replace(search, value)
    
    # Save output
    output_path = base_dir / 'dist' / 'html'
    output_path.mkdir(parents=True, exist_ok=True)
    
    with open(output_path / 'index.html', 'w') as f:
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
    output_path = generate_html(data)
    print(f"HTML generated: {output_path}")
