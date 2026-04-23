"""Tailored LaTeX rendering for V2 pipeline."""

import shutil
from pathlib import Path
from typing import List
from datetime import datetime

from .config import BASE_DIR, OUTPUT_DIR


LATEX_TEMPLATE = r"""\documentclass[letterpaper,10pt]{article}

\usepackage{latexsym}
\usepackage[empty]{fullpage}
\usepackage{titlesec}
\usepackage{marvosym}
\usepackage[usenames,dvipsnames]{color}
\usepackage{verbatim}
\usepackage{enumitem}
\usepackage[hidelinks]{hyperref}
\usepackage{fancyhdr}
\usepackage[english]{babel}
\usepackage{tabularx}
\usepackage{fontawesome5}
\usepackage{xcolor}
\usepackage{setspace}

\definecolor{teal}{HTML}{78BEBA}
\definecolor{red}{HTML}{D35233}
\definecolor{blue}{HTML}{2C5AA0}
\definecolor{black}{HTML}{111111}

\pagestyle{fancy}
\fancyhf{}
\fancyfoot{}
\renewcommand{\headrulewidth}{0pt}
\renewcommand{\footrulewidth}{0pt}

\addtolength{\oddsidemargin}{-0.6in}
\addtolength{\evensidemargin}{-0.6in}
\addtolength{\textwidth}{1.2in}
\addtolength{\topmargin}{-0.6in}
\addtolength{\textheight}{1.2in}

\urlstyle{same}
\raggedbottom
\raggedright
\setlength{\tabcolsep}{0in}

\titleformat{\section}{
  \vspace{-4pt}\scshape\raggedright\large\color{red}
}{}{0em}{}[\color{black}\titlerule \vspace{-5pt}]

\newcommand{\resumeItem}[1]{
  \item\footnotesize{#1 \vspace{-3pt}}
}

\newcommand{\resumeSubheading}[4]{
  \vspace{-3pt}\item
  \begin{tabular*}{0.97\textwidth}[t]{l@{\extracolsep{\fill}}r}
    \textbf{\color{teal}#1} & \textcolor{blue}{\textit{#2}} \\
    \textit{\footnotesize#3} & \textit{\footnotesiz #4} \\
  \end{tabular*}\vspace{-8pt}
}

\newcommand{\resumeSubItem}[1]{\resumeItem{#1}\vspace{-4pt}}

\newcommand{\resumeSubHeadingListStart}{\begin{itemize}[leftmargin=0.15in]}
\newcommand{\resumeSubHeadingListEnd}{\end{itemize}}
\newcommand{\resumeItemListStart}{\begin{itemize}}
\newcommand{\resumeItemListEnd}{\end{itemize}\vspace{-5pt}}

\begin{document}

\begin{center}
    {\Huge \textbf{DANIEL RAMIREZ}} \\
    \vspace{3pt}
    {\Large \textcolor{teal}{Sound Designer}} \\
    \vspace{10pt}
    \href{daniel@danialrami.com}{\faEnvelope\ daniel@danialrami.com} $
    |$ \href{tel:+17146161558}{\faMobile\ (714) 616-1558} $
    |$ \href{https://danialramirez.com}{\faGlobe\ danialramirez.com}
\end{center}

\section{PROFESSIONAL PROFILE}
\vspace{3pt}
TAILORED_PROFILE

\section{EXPERIENCE}
\resumeSubHeadingListStart

EXPERIENCE_ITEMS

\resumeSubHeadingListEnd

\section{TECHNICAL SKILLS}
\resumeSubHeadingListStart}
\begin{tabular}{ @{} >{\bfseries\color{teal}}l @{\hspace{4pt}} l }
SKILLS_SECTION
\end{tabular}
\resumeSubHeadingListEnd

\section{EDUCATION}
\resumeSubHeadingListStart

EDUCATION_ITEMS

\resumeSubHeadingListEnd

\section{PROJECTS}
\resumeSubHeadingListStart

PROJECT_ITEMS

\resumeSubHeadingListEnd

\AtEndDocument{%
    \ifnum\value{page}>1%
        \PackageError{ResumeLength}{Resume exceeds one page!}{}%
    \fi%
}%

\end{document}
"""


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
    Generate tailored LaTeX from selected content.
    
    Args:
        content: List of bullet dicts with content, metadata
        template_path: Path to template file
        output_path: Output .tex path
    
    Returns:
        Path to generated .tex file
    """
    if not output_path.parent.exists():
        output_path.parent.mkdir(parents=True, exist_ok=True)
    
    if template_path.exists():
        template = template_path.read_text()
    else:
        template = LATEX_TEMPLATE
    
    experience_items = []
    skills_set = set()
    
    for item in content:
        bullet = escape_latex(item.get("content", ""))
        meta = item.get("metadata", {})
        company = escape_latex(meta.get("company", ""))
        
        if meta.get("category") == "experience" and company:
            experience_items.append(
                f"\\resumeSubheading{{{company}}}{{2022–2024}}"
                f"{{Sound Designer}}{{San Francisco, CA}}"
                f"\\resumeItemListStart"
                f"\\resumeItem{{{bullet}}}"
                f"\\resumeItemListEnd"
            )
        
        tags_str = meta.get("tags", "")
        if tags_str:
            for tag in tags_str.split(","):
                if tag.strip():
                    skills_set.add(tag.strip())
    
    skills_str = ", ".join(sorted(skills_set))
    
    template = template.replace("TAILORED_PROFILE", 
        "Sound Designer with expertise in interactive audio and UX sound design.")
    template = template.replace("EXPERIENCE_ITEMS", 
        "\n".join(experience_items) if experience_items else 
        "\\resumeSubheading{Company}{Dates}{Role}{Location}")
    template = template.replace("SKILLS_SECTION", 
        f"Tools & {skills_str}")
    template = template.replace("EDUCATION_ITEMS", 
        "\\resumeSubheading{NYU Steinhardt}{2019}{B.M. Music Theory}{}")
    template = template.replace("PROJECT_ITEMS", 
        "\\resumeSubheading{Projects}{}{}{}")
    
    output_path.write_text(template)
    
    return output_path