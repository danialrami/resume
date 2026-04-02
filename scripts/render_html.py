#!/usr/bin/env python3
"""
Render HTML resume from YAML data.
"""

import subprocess
import re
import os
import yaml
from pathlib import Path


def load_yaml_data(yaml_path: str) -> dict:
    """Load YAML data using PyYAML."""
    with open(yaml_path, "r") as f:
        return yaml.safe_load(f)


def escape_html(text: str) -> str:
    """Escape HTML special characters."""
    if not text:
        return ""

    # Convert to string if number
    if isinstance(text, (int, float)):
        text = str(text)

    replacements = [
        ("&", "&amp;"),
        ("<", "&lt;"),
        (">", "&gt;"),
        ('"', "&quot;"),
        ("'", "&#039;"),
    ]
    for old, new in replacements:
        text = text.replace(old, new)
    return text


def render_experience_html(experience: list) -> str:
    """Render experience section."""
    html = []
    for exp in experience:
        company = escape_html(str(exp.get("company", "")))
        role = escape_html(str(exp.get("role", "")))
        location = escape_html(str(exp.get("location", "")))
        dates = escape_html(str(exp.get("dates", "")))

        bullets = exp.get("description", [])

        html.append('<div class="timeline-item">')
        html.append('    <div class="timeline-dot"></div>')
        html.append('    <div class="timeline-content">')

        date_line = []
        if location:
            date_line.append(location)
        if dates:
            date_line.append(dates)

        html.append(f"    <h3>{role} | {company}</h3>")
        if date_line:
            html.append(f'    <p class="timeline-date">{" | ".join(date_line)}</p>')

        if bullets:
            html.append("    <ul>")
            for bullet in bullets:
                html.append(f"        <li>{escape_html(str(bullet))}</li>")
            html.append("    </ul>")

        html.append("    </div>")
        html.append("</div>")

    return "\n".join(html)


def render_education_html(education: list) -> str:
    """Render education section."""
    html = []

    for edu in education:
        school = escape_html(str(edu.get("school", "")))
        degree = escape_html(str(edu.get("degree", "")))
        location = escape_html(str(edu.get("location", "")))
        dates = escape_html(str(edu.get("dates", "")))

        html.append('<div class="education-item">')
        html.append(f"    <h3>{school}</h3>")
        html.append(f'    <p class="education-degree">{degree}</p>')

        details = []
        if location:
            details.append(location)
        if dates:
            details.append(dates)

        html.append(f'    <p class="education-location">{" | ".join(details)}</p>')
        html.append("</div>")

    return "\n".join(html)


def render_certifications_html(certifications: list) -> str:
    """Render certifications section."""
    html = []

    for cert in certifications:
        name = escape_html(str(cert.get("name", "")))

        html.append('<div class="certification-item">')
        html.append(f"    <h3>{name}</h3>")

        # Extract items from link if it looks like a list
        link = cert.get("link", "")
        # Simple parsing for certifications
        html.append("    <ul>")
        html.append(
            f'        <li><a href="{escape_html(str(link))}" target="_blank">View Certification</a></li>'
        )
        html.append("    </ul>")
        html.append("</div>")

    return "\n".join(html)


def render_projects_html(projects: list) -> str:
    """Render projects section."""
    html = []

    for proj in projects:
        name = escape_html(str(proj.get("name", "")))

        # Determine icon based on category
        icons = {
            "app": "fa-mobile-alt",
            "audio": "fa-microphone",
            "automation": "fa-cogs",
            "pipeline": "fa-stream",
        }

        icon = "fa-code"
        for keyword, i in icons.items():
            if keyword.lower() in name.lower():
                icon = i.replace(" ", "")
                break

        html.append('<div class="project-item">')
        html.append(f'    <div class="project-icon"><i class="fas {icon}"></i></div>')
        html.append(f"    <h3>{name}</h3>")

        bullets = proj.get("description", [])
        if bullets:
            html.append("    <ul>")
            for bullet in bullets:
                html.append(f"        <li>{escape_html(str(bullet))}</li>")
            html.append("    </ul>")

        html.append("</div>")

    return "\n".join(html)


def render_skills_html(skills: list) -> str:
    """Render skills sections."""
    html = []

    # Audio Software
    for skill in skills:
        if "Audio Software" in str(skill.get("category", "")):
            items = ", ".join(str(x) for x in skill.get("list", []))
            html.append('<div class="skills-category">')
            html.append("    <h3>Audio Software & Hardware</h3>")
            html.append('    <div class="skills-grid">')
            html.append(
                f'        <div class="skill-item"><i class="fas fa-sliders-h"></i><span>{escape_html(items)}</span></div>'
            )
            html.append("    </div>")
            html.append("</div>")

    # DAWs
    for skill in skills:
        if "DAW" in str(skill.get("category", "")):
            items = ", ".join(str(x) for x in skill.get("list", []))
            html.append('<div class="skills-category">')
            html.append("    <h3>DAWs</h3>")
            html.append('    <div class="skills-grid">')
            html.append(
                f'        <div class="skill-item"><i class="fas fa-music"></i><span>{escape_html(items)}</span></div>'
            )
            html.append("    </div>")
            html.append("</div>")

    # Game Engines
    for skill in skills:
        if "Game" in str(skill.get("category", "")):
            items = ", ".join(str(x) for x in skill.get("list", []))
            html.append('<div class="skills-category">')
            html.append("    <h3>Game Engines</h3>")
            html.append('    <div class="skills-grid">')
            html.append(
                f'        <div class="skill-item"><i class="fas fa-gamepad"></i><span>{escape_html(items)}</span></div>'
            )
            html.append("    </div>")
            html.append("</div>")

    # Scripting
    for skill in skills:
        if "Script" in str(skill.get("category", "")):
            items = ", ".join(str(x) for x in skill.get("list", []))
            html.append('<div class="skills-category">')
            html.append("    <h3>Scripting</h3>")
            html.append('    <div class="skills-grid">')
            html.append(
                f'        <div class="skill-item"><i class="fas fa-code"></i><span>{escape_html(items)}</span></div>'
            )
            html.append("    </div>")
            html.append("</div>")

    # Node-based
    for skill in skills:
        if (
            "Node" in str(skill.get("category", ""))
            or "based" in str(skill.get("category", "")).lower()
        ):
            items = ", ".join(str(x) for x in skill.get("list", []))
            html.append('<div class="skills-category">')
            html.append("    <h3>Node-based</h3>")
            html.append('    <div class="skills-grid">')
            html.append(
                f'        <div class="skill-item"><i class="fas fa-project-diagram"></i><span>{escape_html(items)}</span></div>'
            )
            html.append("    </div>")
            html.append("</div>")

    return "\n".join(html)


def render_profile_html(profile: str) -> str:
    """Render profile text for HTML."""
    lines = [line.strip() for line in str(profile).split("\n") if line.strip()]
    return escape_html(" ".join(lines))


def render_social_links(contact: dict) -> str:
    """Render social links."""
    html = []

    github = contact.get("github", "")
    linkedin = contact.get("linkedin", "")

    if github:
        html.append(
            f'<a href="https://github.com/{github}" class="social-link" title="GitHub"><i class="fab fa-github"></i></a>'
        )
    if linkedin:
        html.append(
            f'<a href="https://www.linkedin.com/in/{linkedin}" class="social-link" title="LinkedIn"><i class="fab fa-linkedin"></i></a>'
        )

    return "\n".join(html)


def get_audio_duration(file_path: str) -> float:
    """Get audio file duration in seconds using ffprobe."""
    try:
        cmd = [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            file_path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0 and result.stdout.strip():
            return float(result.stdout.strip())
    except Exception as e:
        print(f"Warning: Could not get duration for {file_path}: {e}")
    return 0.0


def format_duration(seconds: float) -> str:
    """Format duration in seconds to MM:SS format."""
    if seconds <= 0:
        return "0:00"
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes}:{secs:02d}"


def filename_to_title(filename: str) -> str:
    """Convert filename to a readable title."""
    # Get filename without extension
    name = os.path.splitext(filename)[0]

    # Replace common separators with spaces
    title = re.sub(r"[-_]+", " ", name)

    # Capitalize each word
    title = " ".join(word.capitalize() for word in title.split())

    # If title is empty or only numbers, use the original name
    if not title.strip() or re.match(r"^[\d\s]+$", title):
        return name

    return title


def scan_audio_samples(audio_dir: Path) -> list:
    """Scan audio directory and return list of sample info."""
    samples = []
    audio_extensions = {".wav", ".mp3", ".ogg", ".m4a", ".flac", ".aac"}

    if not audio_dir.exists():
        print(f"Warning: Audio directory not found: {audio_dir}")
        return samples

    for file_path in sorted(audio_dir.iterdir()):
        if file_path.is_file() and file_path.suffix.lower() in audio_extensions:
            duration = get_audio_duration(str(file_path))
            title = filename_to_title(file_path.name)
            samples.append(
                {
                    "filename": file_path.name,
                    "title": title,
                    "duration": duration,
                    "formatted_duration": format_duration(duration),
                }
            )

    return samples


def render_audio_samples_dropdown(audio_samples: list) -> str:
    """Render audio samples dropdown options HTML."""
    options = []
    for sample in audio_samples:
        label = f"{sample['title']} ({sample['formatted_duration']})"
        value = f"assets/audio/{sample['filename']}"
        options.append(f'<option value="{value}">{label}</option>')
    return "\n".join(options)


def copy_html_assets(base_dir: Path, audio_samples: list = None) -> None:
    """Copy CSS, JS, and other assets to dist/html."""
    html_dir = base_dir / "templates" / "html"
    dist_html = base_dir / "dist" / "html"

    # List of assets to copy
    assets = ["styles.css", "script.js", "three_effects.js"]

    for asset in assets:
        src = html_dir / asset
        if src.exists():
            dst = dist_html / asset
            with open(src, "r") as f:
                content = f.read()
            with open(dst, "w") as f:
                f.write(content)

    # Copy SVG assets
    for svg_file in html_dir.glob("*.svg"):
        dst = dist_html / svg_file.name
        with open(svg_file, "r") as f:
            content = f.read()
        with open(dst, "w") as f:
            f.write(content)

    # Copy audio assets
    if audio_samples:
        audio_src_dir = base_dir / "assets" / "audio"
        audio_dst_dir = dist_html / "assets" / "audio"
        audio_dst_dir.mkdir(parents=True, exist_ok=True)

        for sample in audio_samples:
            src = audio_src_dir / sample["filename"]
            dst = audio_dst_dir / sample["filename"]
            if src.exists():
                import shutil

                shutil.copy2(src, dst)
                print(f"  Copied: {sample['filename']}")


def generate_html(data: dict) -> str:
    """Generate HTML file from data."""
    base_dir = Path(__file__).parent.parent
    template_path = base_dir / "templates" / "html" / "index.html"

    with open(template_path, "r") as f:
        template = f.read()

    # Build substitution map
    name = escape_html(str(data.get("name", "")))
    title = escape_html(str(data.get("title", "Sound Designer")))

    contact = data.get("contact", {})

    # Scan audio samples
    audio_dir = base_dir / "assets" / "audio"
    audio_samples = scan_audio_samples(audio_dir)
    print(f"Found {len(audio_samples)} audio samples:")
    for sample in audio_samples:
        print(f"  - {sample['title']} ({sample['formatted_duration']})")

    substitutions = {
        "RESUME_NAME": name,
        "RESUME_TITLE": title,
        "RESUME_EMAIL": escape_html(str(contact.get("email", ""))),
        "RESUME_PHONE": escape_html(str(contact.get("phone", "")))
        if contact.get("phone")
        else "",
        "RESUME_LINKEDIN": escape_html(str(contact.get("linkedin", "")))
        if contact.get("linkedin")
        else "",
        "RESUME_GITHUB": escape_html(str(contact.get("github", "")))
        if contact.get("github")
        else "",
        "RESUME_PROFILE": render_profile_html(data.get("profile", "")),
        "RESUME_EXPERIENCE_TIMELINE": render_experience_html(
            data.get("experience", [])
        ),
        "RESUME_EDUCATION_ITEMS": render_education_html(data.get("education", [])),
        "RESUME_CERTIFICATIONS": render_certifications_html(
            data.get("certifications", [])
        ),
        "RESUME_PROJECTS_GRID": render_projects_html(data.get("projects", [])),
        "RESUME_SKILLS_GRID": render_skills_html(data.get("skills", [])),
        "RESUME_SOCIAL_LINKS": render_social_links(contact),
        "AUDIO_SAMPLES_OPTIONS": render_audio_samples_dropdown(audio_samples),
    }

    # Replace placeholders
    for placeholder, value in substitutions.items():
        template = template.replace(f"RESUME_{placeholder}", value)
        # Also handle non-RESUME prefixed placeholders
        template = template.replace(f"{placeholder}", value)

    # Save output
    output_path = base_dir / "dist" / "html"
    output_path.mkdir(parents=True, exist_ok=True)

    with open(output_path / "index.html", "w") as f:
        f.write(template)

    copy_html_assets(base_dir, audio_samples)
    return str(output_path)


if __name__ == "__main__":
    base_dir = Path(__file__).parent.parent
    data_path = base_dir / "data" / "resume.yaml"

    if not data_path.exists():
        print(f"Error: YAML file not found at {data_path}")
        import sys

        sys.exit(1)

    data = load_yaml_data(str(data_path))
    output_path = generate_html(data)
    print(f"HTML generated: {output_path}")
