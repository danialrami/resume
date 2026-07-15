#!/usr/bin/env python3
"""
Render the multi-lens HTML resume from YAML data.

The site is a single persistent-audio shell (rail = cloud mark + particle cloud +
catalog streaming player + reactivity engine) with the main content swapped between
three lenses driven by data/site.yaml:

    /              -> data/resume.root.yaml   (synthesis / cold-landing)
    /sound-design  -> data/resume.yaml        (current sound-design copy)
    /infra         -> data/resume.infra.yaml  (infrastructure engineering)

The rail mounts once; a small History-API router swaps only the #content fragment,
so audio keeps playing across lens changes. Each route is also emitted as a real
static page (dist/html/index.html, /sound-design/index.html, /infra/index.html) so
cold loads, no-JS, and crawlers get real content and deep links work under static
hosting. Slugs are a locked contract shared with resume-builder-workspace.

The template (templates/html/index.html) is Amacher's redesign, left pristine and
patched at build time via anchor asserts: if the template structure changes, the
build fails loudly rather than emitting something broken.
"""

import json
import os
import re
import sys
from pathlib import Path

import yaml

BASE_DIR = Path(__file__).parent.parent
TEMPLATE = BASE_DIR / "templates" / "html" / "index.html"
DATA_DIR = BASE_DIR / "data"
OUT_DIR = BASE_DIR / "dist" / "html"


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def load_yaml(path: Path) -> dict:
    with open(path, "r") as f:
        return yaml.safe_load(f)


def escape_html(text) -> str:
    if text is None:
        return ""
    if isinstance(text, (int, float)):
        text = str(text)
    for old, new in (
        ("&", "&amp;"), ("<", "&lt;"), (">", "&gt;"),
        ('"', "&quot;"), ("'", "&#039;"),
    ):
        text = text.replace(old, new)
    return text


def replace_once(s: str, old: str, new: str, what: str) -> str:
    n = s.count(old)
    if n != 1:
        raise SystemExit(
            f"[render] template contract broken: expected exactly 1 occurrence "
            f"of anchor for '{what}', found {n}. Template changed?"
        )
    return s.replace(old, new)


def sub_once(s: str, pattern: str, repl: str, what: str) -> str:
    out, n = re.subn(pattern, repl, s, count=1)
    if n != 1:
        raise SystemExit(
            f"[render] template contract broken: regex for '{what}' matched {n} "
            f"times (expected 1). Template changed?"
        )
    return out


# --------------------------------------------------------------------------- #
# fragment builders (dossier markup — must match the template's CSS classes)
# --------------------------------------------------------------------------- #
def render_headline(headline: str) -> str:
    lines = [escape_html(l) for l in str(headline).split("\n")]
    return "<br>".join(lines)


def bullet_text(b) -> str:
    """Coerce a bullet to text. Guards against a YAML colon mis-parse where
    '- some phrase: detail' becomes a {phrase: detail} dict instead of a string."""
    if isinstance(b, dict):
        return "; ".join(f"{k}: {v}" for k, v in b.items())
    return b if isinstance(b, str) else str(b)


def render_profile(profile: str) -> str:
    lines = [l.strip() for l in str(profile).split("\n") if l.strip()]
    return escape_html(" ".join(lines))


def render_experience(experience: list) -> str:
    out = []
    for exp in experience or []:
        company = escape_html(exp.get("company", ""))
        role = escape_html(exp.get("role", ""))
        location = escape_html(exp.get("location", ""))
        dates = escape_html(exp.get("dates", ""))
        meta = " · ".join([p for p in [dates, location] if p])
        out.append('<div class="tl-item">')
        if meta:
            out.append(f'  <div class="when">{meta}</div>')
        out.append(f"  <h3>{role}</h3>")
        if company:
            out.append(f'  <div class="org">{company}</div>')
        bullets = exp.get("description", [])
        if bullets:
            out.append('  <ul class="bul">')
            for b in bullets:
                out.append(f"    <li>{escape_html(bullet_text(b))}</li>")
            out.append("  </ul>")
        out.append("</div>")
    return "\n".join(out)


def render_education(education: list) -> str:
    out = []
    for edu in education or []:
        school = escape_html(edu.get("school", ""))
        degree = escape_html(edu.get("degree", ""))
        location = escape_html(edu.get("location", ""))
        dates = escape_html(edu.get("dates", ""))
        meta = " · ".join([p for p in [dates, location] if p])
        out.append('<div class="tl-item">')
        if meta:
            out.append(f'  <div class="when">{meta}</div>')
        out.append(f"  <h3>{degree}</h3>")
        if school:
            out.append(f'  <div class="org">{school}</div>')
        out.append("</div>")
    return "\n".join(out)


def render_certifications(certs: list) -> str:
    return "\n".join(
        f'<span class="tag">{escape_html(c.get("name", ""))}</span>'
        for c in (certs or []) if c.get("name")
    )


def render_projects(projects: list) -> str:
    out = []
    for proj in projects or []:
        name = escape_html(proj.get("name", ""))
        desc = escape_html(" ".join(bullet_text(b) for b in proj.get("description", [])))
        out.append('<div class="card reveal">')
        out.append('  <span class="k">Project</span>')
        out.append(f"  <h3>{name}</h3>")
        if desc:
            out.append(f"  <p>{desc}</p>")
        out.append("</div>")
    return "\n".join(out)


def render_skills(skills: list) -> str:
    out = []
    for sk in skills or []:
        out.append('<div class="card reveal">')
        out.append(f'  <span class="k">{escape_html(sk.get("category", ""))}</span>')
        out.append('  <div class="tags">')
        for it in sk.get("list", []):
            out.append(f'    <span class="tag">{escape_html(it)}</span>')
        out.append("  </div>")
        out.append("</div>")
    return "\n".join(out)


def render_lens_inner(data: dict, deck: dict) -> str:
    """The inner HTML of <main id="content"> for one lens (hero -> footer)."""
    contact = data.get("contact", {})
    email = escape_html(contact.get("email", ""))
    github = escape_html(contact.get("github", ""))
    linkedin = escape_html(contact.get("linkedin", ""))
    phone = escape_html(contact.get("phone", ""))
    title = escape_html(data.get("title", ""))
    certs = data.get("certifications", [])

    deck_btn = ""
    if deck.get("download_url"):
        deck_btn = (
            f'\n        <a class="btn ghost" href="{escape_html(deck["download_url"])}" '
            f'target="_blank" rel="noopener noreferrer" data-hover>⤓ '
            f'{escape_html(deck.get("label", "Download deck (PDF)"))}</a>'
        )

    # Reel button is opt-in per lens (default on). Infra turns it off.
    if data.get("reel", True):
        hero_cta = (
            '<a class="btn" href="https://reel.danialrami.com" target="_blank" rel="noopener noreferrer" data-hover>▶ Play the reel</a>\n'
            '        <a class="btn ghost" href="#contact" data-hover>Contact</a>'
        )
    else:
        hero_cta = '<a class="btn" href="#contact" data-hover>Contact</a>'

    cert_row = ""
    edu_heading = "Education"
    if certs:
        edu_heading = "Education &amp; Certs"
        cert_row = (
            '\n      <div class="cert-row reveal">\n'
            '        <span class="cert-label">Certifications</span>\n'
            f'        <div class="tags">{render_certifications(certs)}</div>\n'
            "      </div>"
        )

    return f"""<header class="hero" id="top">
      <span class="sec-label eyebrow">{title}</span>
      <h1 class="big">{render_headline(data.get("headline", title))}<span class="dot">.</span></h1>
      <p class="lead">{escape_html(data.get("lead", ""))}</p>
      <div class="hero-cta">
        {hero_cta}
      </div>
    </header>

    <section class="blk" id="about">
      <div class="blk-head reveal"><span class="num">01</span><h2>About</h2></div>
      <p class="prose reveal">{render_profile(data.get("profile", ""))}</p>
    </section>

    <section class="blk" id="skills">
      <div class="blk-head reveal"><span class="num">02</span><h2>Skills</h2></div>
      <div class="grid g-3">
        {render_skills(data.get("skills", []))}
      </div>
    </section>

    <section class="blk" id="work">
      <div class="blk-head reveal"><span class="num">03</span><h2>Experience</h2></div>
      <div class="tl reveal">
        {render_experience(data.get("experience", []))}
      </div>
    </section>

    <section class="blk" id="edu">
      <div class="blk-head reveal"><span class="num">04</span><h2>{edu_heading}</h2></div>
      <div class="tl reveal">
        {render_education(data.get("education", []))}
      </div>{cert_row}
    </section>

    <section class="blk" id="projects">
      <div class="blk-head reveal"><span class="num">05</span><h2>Selected projects</h2></div>
      <div class="grid g-3">
        {render_projects(data.get("projects", []))}
      </div>
    </section>

    <section class="blk" id="contact">
      <div class="blk-head reveal"><span class="num">06</span><h2>Get in touch</h2></div>
      <p class="prose reveal">{escape_html(data.get("contact_line", ""))}</p>
      <p class="reveal mono" style="font-size:.78rem;letter-spacing:.04em;color:var(--muted);margin-top:6px">{email}&nbsp;&nbsp;·&nbsp;&nbsp;{phone}</p>
      <div class="contact-links reveal">
        <a class="btn" href="mailto:{email}" data-hover>Email</a>
        <a class="btn ghost" href="https://github.com/{github}" target="_blank" rel="noopener noreferrer" data-hover>GitHub</a>
        <a class="btn ghost" href="https://www.linkedin.com/in/{linkedin}" target="_blank" rel="noopener noreferrer" data-hover>LinkedIn</a>{deck_btn}
      </div>
    </section>

    <footer>
      <span class="mono">© Daniel Ramirez — Sound &amp; Systems</span>
      <span class="mono">Audio streamed from <a href="https://catalog.lufs.audio" target="_blank" rel="noopener noreferrer" data-hover style="color:var(--gold)">catalog.lufs.audio</a></span>
    </footer>"""


# --------------------------------------------------------------------------- #
# template patching (pristine template -> placeholder template, once)
# --------------------------------------------------------------------------- #
EXTRA_CSS = (
    ".lens-switch{display:flex;flex-wrap:wrap;gap:6px;margin:2px 0 18px}"
    ".lens-switch a{font-family:'Space Mono',monospace;font-size:.56rem;text-transform:uppercase;"
    "letter-spacing:.13em;color:var(--muted);padding:5px 9px;border:1px solid var(--hair);"
    "border-radius:99px;transition:color .2s,border-color .2s,background .2s;cursor:none}"
    ".lens-switch a:hover{color:var(--gold);border-color:var(--gold)}"
    ".lens-switch a.active{color:#1e1c19;background:var(--gold);border-color:var(--gold)}"
    "/* dev affordances hidden on the shipped site (dial panel still toggles with 'd') */"
    ".proto-note,.dial-toggle{display:none!important}"
    "/* lens transition: fade + slide-up on content swap (Amacher can retune the feel) */"
    ".content.lens-exit{opacity:0;transform:translateY(-8px);transition:opacity .17s ease,transform .17s ease}"
    ".content.lens-enter{opacity:0;transform:translateY(14px)}"
    ".content.lens-enter-active{opacity:1;transform:none;transition:opacity .34s ease,transform .34s ease}"
    "@media (prefers-reduced-motion:reduce){.content.lens-exit,.content.lens-enter,.content.lens-enter-active{transition:none!important;transform:none!important;opacity:1!important}}"
)

SWITCH_LINKS = (
    '<a data-lens="" href="/" data-hover>Overview</a>'
    '<a data-lens="sound-design" href="/sound-design/" data-hover>Sound Design</a>'
    '<a data-lens="infra" href="/infra/" data-hover>Infrastructure</a>'
)

ROUTER_JS = r"""
<script>
/* Persistent-audio lens router. The rail (cloud + player + reactivity) is mounted
   once and never touched; only #content is swapped, so audio keeps playing across
   lens changes. Real routes (/, /sound-design/, /infra/) via pushState, with each
   route also emitted as a static page for cold loads / no-JS / crawlers. */
(function(){
  var FR = window.LENS_FRAGMENTS || {}, META = window.LENS_META || {}, DEF = window.LENS_DEFAULT || "";
  var content = document.getElementById('content');
  var railRole = document.getElementById('railRole');
  var sw = document.getElementById('lensSwitch');
  if(!content || !sw) return;
  var spyHandler = null;

  function bindSpy(){
    var links = [].slice.call(document.querySelectorAll('#railNav a'));
    var secs = links.map(function(a){ try{ return content.querySelector(a.getAttribute('href')); }catch(e){ return null; } });
    if(spyHandler) removeEventListener('scroll', spyHandler);
    spyHandler = function(){ var y=scrollY+innerHeight*0.32, best=0;
      for(var i=0;i<secs.length;i++){ if(secs[i]&&secs[i].offsetTop<=y) best=i; }
      links.forEach(function(l,i){ l.classList.toggle('active', i===best); }); };
    addEventListener('scroll', spyHandler, {passive:true}); spyHandler();
  }

  function normalize(path){
    var s=(path||'/').replace(/^\/+|\/+$/g,'');
    return FR.hasOwnProperty(s) ? s : '';
  }

  function paint(slug){
    content.innerHTML = FR[slug];
    var m = META[slug] || {};
    if(railRole && m.role) railRole.textContent = m.role;
    if(m.title) document.title = m.title;
    [].forEach.call(sw.querySelectorAll('a'), function(a){
      a.classList.toggle('active', a.getAttribute('data-lens')===slug); });
    [].forEach.call(content.querySelectorAll('.reveal'), function(e){ e.classList.add('in'); });
    bindSpy();
  }
  var REDUCE = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
  function showLens(slug, push, keepScroll){
    if(!FR.hasOwnProperty(slug)) slug='';
    function commit(){ if(push){ try{ history.pushState({lens:slug}, '', slug ? '/'+slug+'/' : '/'); }catch(e){} } }
    /* initial paint (server DOM already correct) or reduced-motion: swap instantly */
    if(keepScroll || REDUCE){
      paint(slug);
      if(!keepScroll){ try{ scrollTo(0,0); }catch(e){} }
      commit();
      return;
    }
    /* fade + slide-up transition on lens change */
    content.classList.add('lens-exit');
    setTimeout(function(){
      paint(slug);
      try{ scrollTo(0,0); }catch(e){}
      content.classList.remove('lens-exit');
      content.classList.add('lens-enter');
      requestAnimationFrame(function(){ requestAnimationFrame(function(){
        content.classList.add('lens-enter-active');
        content.classList.remove('lens-enter'); }); });
      setTimeout(function(){ content.classList.remove('lens-enter-active'); }, 380);
      commit();
    }, 170);
  }

  sw.addEventListener('click', function(e){
    var a = e.target.closest('a[data-lens]'); if(!a) return;
    e.preventDefault();
    var slug = a.getAttribute('data-lens');
    if(slug !== normalize(location.pathname)) showLens(slug, true);
  });
  addEventListener('popstate', function(e){
    showLens((e.state && e.state.lens!=null) ? e.state.lens : normalize(location.pathname), false); });

  /* Initial paint: server already rendered DEF as live DOM. Re-run through showLens
     to wire switcher/spy/reveal without changing which lens is shown. */
  showLens(DEF, false, true);
})();
</script>
"""


def patch_template(raw: str) -> str:
    t = raw
    # head: title + meta description -> placeholders
    t = replace_once(
        t, "<title>Resume | Daniel Ramirez</title>",
        "<title>%%PAGETITLE%%</title>", "page title",
    )
    t = sub_once(
        t, r'<meta name="description" content="[^"]*"',
        '<meta name="description" content="%%METADESC%%"', "meta description",
    )
    # extra css before </head>
    t = replace_once(t, "</head>", f"<style>{EXTRA_CSS}</style>\n</head>", "extra css")
    # rail role -> id'd placeholder + lens switcher
    t = replace_once(
        t,
        '<div class="rail-role">RESUME_TITLE · Interactive Audio</div>',
        '<div class="rail-role" id="railRole">%%RAILROLE%%</div>\n'
        '    <nav class="lens-switch" id="lensSwitch" aria-label="Resume lens">%%SWITCHER%%</nav>',
        "rail role + switcher",
    )
    # replace whole <main class="content"> ... </main> with a single mount point
    a = t.find('<main class="content">')
    if a == -1:
        raise SystemExit("[render] anchor '<main class=\"content\">' not found")
    b = t.find("</main>", a)
    if b == -1:
        raise SystemExit("[render] closing </main> not found")
    b += len("</main>")
    t = t[:a] + '<main class="content" id="content">%%MAIN%%</main>' + t[b:]
    # remove the template's original rail scroll-spy IIFE (router owns spy now)
    sa = t.find("/* rail scroll-spy */")
    if sa != -1:
        se = t.find("})();", sa)
        if se != -1:
            t = t[:sa] + "/* rail scroll-spy handled by lens router */" + t[se + len("})();"):]
    # SPA data + router before </body>
    t = replace_once(t, "</body>", "%%SPA%%\n</body>", "spa injection")
    return t


# --------------------------------------------------------------------------- #
# build
# --------------------------------------------------------------------------- #
def build_site() -> list:
    site = load_yaml(DATA_DIR / "site.yaml")
    deck = site.get("deck", {}) or {}
    lenses = site.get("lenses", [])
    if not lenses:
        raise SystemExit("[render] site.yaml has no lenses")

    raw = TEMPLATE.read_text()
    tmpl = patch_template(raw)

    fragments, meta, page_title, meta_desc = {}, {}, {}, {}
    switch_active = {}
    for lens in lenses:
        slug = lens.get("slug", "")
        data = load_yaml(DATA_DIR / lens["data"])
        fragments[slug] = render_lens_inner(data, deck)
        role = data.get("title", "")
        label = lens.get("nav_label", role)
        title_tag = f"Daniel Ramirez — {label}"
        meta[slug] = {"role": role, "title": title_tag}
        page_title[slug] = escape_html(title_tag)
        meta_desc[slug] = escape_html(data.get("lead", "") or role)

    # JSON blobs for the client (guard against </script> breakout)
    def js(obj):
        return json.dumps(obj, ensure_ascii=False).replace("</", "<\\/")

    switcher_for = {}
    for lens in lenses:
        slug = lens.get("slug", "")
        links = SWITCH_LINKS
        # mark the active link server-side (progressive: router re-affirms it)
        needle = f'data-lens="{slug}"'
        links = links.replace(needle, needle + ' class="active"', 1)
        switcher_for[slug] = links

    outputs = []
    for lens in lenses:
        slug = lens.get("slug", "")
        spa = (
            "<script>\n"
            f"window.LENS_FRAGMENTS = {js(fragments)};\n"
            f"window.LENS_META = {js(meta)};\n"
            f"window.LENS_DEFAULT = {js(slug)};\n"
            "</script>" + ROUTER_JS
        )
        page = (
            tmpl.replace("%%PAGETITLE%%", page_title[slug])
            .replace("%%METADESC%%", meta_desc[slug])
            .replace("%%RAILROLE%%", escape_html(meta[slug]["role"]))
            .replace("%%SWITCHER%%", switcher_for[slug])
            .replace("%%MAIN%%", fragments[slug])
            .replace("%%SPA%%", spa)
        )
        # verify: no leftover placeholders
        leftover = sorted(set(re.findall(r"%%[A-Z_]+%%", page)) | set(re.findall(r"RESUME_[A-Z_]+", page)))
        if leftover:
            raise SystemExit(f"[render] unfilled placeholders in '{slug or '/'}' page: {leftover}")

        out_path = OUT_DIR if slug == "" else OUT_DIR / slug
        out_path.mkdir(parents=True, exist_ok=True)
        (out_path / "index.html").write_text(page)
        outputs.append(str(out_path / "index.html"))
        print(f"  built {'/' if slug=='' else '/'+slug+'/'} -> {out_path/'index.html'}")

    return outputs


if __name__ == "__main__":
    if not TEMPLATE.exists():
        print(f"Error: template not found at {TEMPLATE}")
        sys.exit(1)
    outs = build_site()
    print(f"Built {len(outs)} lens pages.")
