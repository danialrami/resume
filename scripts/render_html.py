#!/usr/bin/env python3
"""
Render the multi-lens HTML resume from YAML data.

The site is a single persistent-audio shell (rail = cloud mark + particle cloud +
catalog streaming player + reactivity engine) with the main content swapped between
three lenses driven by data/site.yaml:

    /              -> data/resume.root.yaml   (synthesis / cold-landing)
    /audio         -> data/resume.yaml        (audio & interactive sound)
    /infra         -> data/resume.infra.yaml  (infrastructure engineering)

The rail mounts once; a small History-API router swaps only the #content fragment,
so audio keeps playing across lens changes. Each route is also emitted as a real
static page (dist/html/index.html, /audio/index.html, /infra/index.html) so
cold loads, no-JS, and crawlers get real content and deep links work under static
hosting. Slugs are set in data/site.yaml; SWITCH_LINKS below must be kept in sync.

The template (templates/html/index.html) is Amacher's redesign, left pristine and
patched at build time via anchor asserts: if the template structure changes, the
build fails loudly rather than emitting something broken.
"""

import json
import os
import re
import shutil
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
        out.append('<div class="tl-item">')
        if dates or location:
            loc = f'<span class="loc"> · {location}</span>' if location else ""
            out.append(f'  <div class="when">{dates}{loc}</div>')
        # Masthead order: date, then the company at headline scale, then the role.
        if company:
            out.append(f'  <div class="org">{company}</div>')
        out.append(f"  <h3>{role}</h3>")
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
        out.append('<div class="tl-item">')
        if dates or location:
            loc = f'<span class="loc"> · {location}</span>' if location else ""
            out.append(f'  <div class="when">{dates}{loc}</div>')
        # Masthead order: date, then the school at headline scale, then the degree.
        if school:
            out.append(f'  <div class="org">{school}</div>')
        out.append(f"  <h3>{degree}</h3>")
        out.append("</div>")
    return "\n".join(out)


def _cert_parts(certs: list):
    """Split certs into (earned, in_progress), preserving authored order."""
    earned, prog = [], []
    for c in certs or []:
        if not c.get("name"):
            continue
        (earned if str(c.get("status", "")).lower() == "earned" else prog).append(c)
    return earned, prog


def render_certifications(certs: list) -> str:
    """Certifications as their own grid — earned first, each with its issuer."""
    earned, prog = _cert_parts(certs)
    out = []
    for c, done in [(c, True) for c in earned] + [(c, False) for c in prog]:
        cls = "specitem done" if done else "specitem"
        label = "Certified" if done else "In progress"
        out.append(f'<div class="{cls} reveal">')
        out.append(f'  <span class="st">{label}</span>')
        out.append(f'  <span class="nm">{escape_html(c.get("name", ""))}</span>')
        if c.get("issuer"):
            out.append(f'  <span class="by">{escape_html(c["issuer"])}</span>')
        out.append("</div>")
    return "\n".join(out)


def render_front_matter(education: list, certs: list) -> str:
    """Credentials as standfirst: up to two schools plus a certifications summary,
    sitting directly under the hero so they land in the first screen."""
    cells = []
    for edu in (education or [])[:2]:
        kind = escape_html(edu.get("kind", "Education"))
        meta = " · ".join(
            [p for p in [escape_html(edu.get("dates", "")), escape_html(edu.get("location", ""))] if p]
        )
        cells.append(
            f'<div class="fm">\n'
            f'          <span class="k">{kind}</span>\n'
            f'          <span class="v">{escape_html(edu.get("school", ""))}</span>\n'
            f'          <span class="d">{escape_html(edu.get("degree", ""))}</span>\n'
            f'          <span class="m">{meta}</span>\n'
            f'        </div>'
        )
    earned, prog = _cert_parts(certs)
    if earned or prog:
        head = " · ".join(
            escape_html(c.get("short") or c["name"]) for c in earned
        ) or "In progress"
        detail = ", ".join(escape_html(c["name"]) for c in prog)
        detail = f"{detail} in progress" if detail else "&nbsp;"
        tally = " · ".join(
            p for p in [
                f"{len(earned)} earned" if earned else "",
                f"{len(prog)} in progress" if prog else "",
            ] if p
        )
        cells.append(
            f'<div class="fm">\n'
            f'          <span class="k">Certifications</span>\n'
            f'          <span class="v">{head}</span>\n'
            f'          <span class="d">{detail}</span>\n'
            f'          <span class="m">{tally}</span>\n'
            f'        </div>'
        )
    if not cells:
        return ""
    return '<div class="frontmatter">\n        ' + "\n        ".join(cells) + "\n      </div>"


def render_projects(projects: list) -> str:
    """Project cards. When a project carries a `link`, the whole card becomes the
    button — so every entry a reader clicks lands on a real, public repo."""
    out = []
    for proj in projects or []:
        name = escape_html(proj.get("name", ""))
        desc = escape_html(" ".join(bullet_text(b) for b in proj.get("description", [])))
        link = proj.get("link", "")
        kicker = escape_html(proj.get("meta", "Project"))
        if link:
            out.append(
                f'<a class="card reveal" href="{escape_html(link)}" target="_blank" '
                f'rel="noopener noreferrer" data-hover>'
            )
        else:
            out.append('<div class="card reveal">')
        out.append(f'  <span class="k">{kicker}</span>')
        out.append(f"  <h3>{name}</h3>")
        if desc:
            out.append(f"  <p>{desc}</p>")
        if link:
            out.append('  <span class="go">View on GitHub <i>&rarr;</i></span>')
            out.append("</a>")
        else:
            out.append("</div>")
    return "\n".join(out)


def render_skills(skills: list) -> str:
    """Skills as hairline cells, matching Certifications. Deliberately NOT
    `.card`: a filled, lifting panel reads as a button, and only the project
    cards are actually clickable."""
    out = []
    for sk in skills or []:
        items = " · ".join(escape_html(it) for it in sk.get("list", []))
        out.append('<div class="specitem reveal">')
        out.append(f'  <span class="k">{escape_html(sk.get("category", ""))}</span>')
        out.append(f'  <p class="slist">{items}</p>')
        out.append("</div>")
    return "\n".join(out)


# Section order is declared once and drives BOTH the numbered headings and the
# rail nav, so the two can never drift apart.
SECTIONS = [
    ("about",    "About"),
    ("work",     "Experience"),
    ("edu",      "Education"),
    ("certs",    "Certifications"),
    ("projects", "Selected projects"),
    ("skills",   "Skills"),
    ("contact",  "Get in touch"),
]
NAV_LABELS = {"work": "Experience", "projects": "Projects", "contact": "Contact"}
_NUM = {sid: f"{i + 1:02d}" for i, (sid, _) in enumerate(SECTIONS)}


def render_rail_nav() -> str:
    """The rail nav, generated from SECTIONS. The rail mounts once and is shared
    by every lens, so the section set must be identical across lenses."""
    rows = [
        f'      <a href="#{sid}" data-hover><span class="n">{_NUM[sid]}</span> '
        f'{escape_html(NAV_LABELS.get(sid, heading))}</a>'
        for sid, heading in SECTIONS
    ]
    return (
        '<nav class="rail-nav" id="railNav">\n'
        '      <span class="spine"><span class="prog" id="prog"></span></span>\n'
        + "\n".join(rows)
        + "\n    </nav>"
    )


def render_lens_inner(data: dict, site: dict) -> str:
    """The inner HTML of <main id="content"> for one lens (hero -> footer)."""
    deck = site.get("deck", {}) or {}
    links = site.get("links", {}) or {}
    pdf = site.get("resume_pdf", {}) or {}

    contact = data.get("contact", {})
    email = escape_html(contact.get("email", ""))
    github = escape_html(contact.get("github", ""))
    linkedin = escape_html(contact.get("linkedin", ""))
    phone = escape_html(contact.get("phone", ""))
    title = escape_html(data.get("title", ""))

    # Certifications are shared in site.yaml; a lens may still override its own.
    certs = data.get("certifications") or site.get("certifications", [])
    education = data.get("education", [])

    # ---- hero CTAs: primary action, then the cross-links to the sibling sites
    cta = []
    if data.get("reel", True):
        cta.append(
            '<a class="btn" href="https://reel.daniel-ramirez.io" target="_blank" '
            'rel="noopener noreferrer" data-hover>&#9654; Play the reel</a>'
        )
        cta.append(f'<a class="btn ghost" href="mailto:{email}" data-hover>Contact</a>')
    else:
        cta.append(f'<a class="btn" href="mailto:{email}" data-hover>Contact</a>')
    if deck.get("site_url"):
        cta.append(
            f'<a class="btn ghost" href="{escape_html(deck["site_url"])}" target="_blank" '
            f'rel="noopener noreferrer" data-hover>Deck</a>'
        )
    # Stays hidden until a real PDF ships — see the note in data/site.yaml.
    if pdf.get("url"):
        cta.append(
            f'<a class="btn ghost" href="{escape_html(pdf["url"])}" '
            f'data-hover>{escape_html(pdf.get("label", "Download PDF"))}</a>'
        )
    hero_cta = "\n        ".join(cta)

    # ---- contact row: email / code / network / writing, then the deck download
    extra = ""
    blog = links.get("blog", {}) or {}
    if blog.get("url"):
        extra += (
            f'\n        <a class="btn ghost" href="{escape_html(blog["url"])}" target="_blank" '
            f'rel="noopener noreferrer" data-hover>{escape_html(blog.get("label", "Blog"))}</a>'
        )
    if deck.get("download_url"):
        extra += (
            f'\n        <a class="btn ghost" href="{escape_html(deck["download_url"])}" '
            f'target="_blank" rel="noopener noreferrer" data-hover>&#10515; '
            f'{escape_html(deck.get("label", "Download deck (PDF)"))}</a>'
        )

    # lufs-vh verification stamp: a tool-derived hash of this site's own URL,
    # sitting on the right of the footer.
    vh = site.get("visual_hash", {}) or {}
    vh_mark = ""
    if vh.get("mark"):
        alt = escape_html(vh.get("alt", ""))
        vh_mark = (
            f'\n      <img class="vh-mark" src="{escape_html(vh["mark"])}" '
            f'alt="{alt}" title="{alt}" width="64" height="64" loading="lazy" />'
        )

    def head(sid):
        return (
            f'<div class="blk-head reveal"><span class="num">{_NUM[sid]}</span>'
            f"<h2>{dict(SECTIONS)[sid]}</h2></div>"
        )

    return f"""<header class="hero" id="top">
      <span class="sec-label eyebrow">{title}</span>
      <h1 class="big">{render_headline(data.get("headline", title))}<span class="dot">.</span></h1>
      <p class="lead">{escape_html(data.get("lead", ""))}</p>
      <div class="hero-cta">
        {hero_cta}
      </div>
    </header>

    {render_front_matter(education, certs)}

    <section class="blk" id="about">
      {head("about")}
      <p class="prose reveal">{render_profile(data.get("profile", ""))}</p>
    </section>

    <section class="blk" id="work">
      {head("work")}
      <div class="tl reveal">
        {render_experience(data.get("experience", []))}
      </div>
    </section>

    <section class="blk" id="edu">
      {head("edu")}
      <div class="tl reveal">
        {render_education(education)}
      </div>
    </section>

    <section class="blk" id="certs">
      {head("certs")}
      <div class="speclist">
        {render_certifications(certs)}
      </div>
    </section>

    <section class="blk" id="projects">
      {head("projects")}
      <div class="grid g-3">
        {render_projects(data.get("projects", []))}
      </div>
    </section>

    <section class="blk" id="skills">
      {head("skills")}
      <div class="speclist">
        {render_skills(data.get("skills", []))}
      </div>
    </section>

    <section class="blk" id="contact">
      {head("contact")}
      <p class="prose reveal">{escape_html(data.get("contact_line", ""))}</p>
      <p class="reveal mono" style="font-size:.78rem;letter-spacing:.04em;color:var(--muted);margin-top:6px">{email}&nbsp;&nbsp;·&nbsp;&nbsp;{phone}</p>
      <div class="contact-links reveal">
        <a class="btn" href="mailto:{email}" data-hover>Email</a>
        <a class="btn ghost" href="https://github.com/{github}" target="_blank" rel="noopener noreferrer" data-hover>GitHub</a>
        <a class="btn ghost" href="https://www.linkedin.com/in/{linkedin}" target="_blank" rel="noopener noreferrer" data-hover>LinkedIn</a>{extra}
      </div>
    </section>

    <footer>
      <div class="foot-txt">
        <span class="mono">© LUFS Audio, LLC — Sound &amp; Systems</span>
        <span class="mono">Original audio streamed from <a href="https://catalog.lufs.audio" target="_blank" rel="noopener noreferrer" data-hover style="color:var(--accent-txt)">catalog.lufs.audio</a></span>
      </div>{vh_mark}
    </footer>"""


# --------------------------------------------------------------------------- #
# template patching (pristine template -> placeholder template, once)
# --------------------------------------------------------------------------- #
# NOTE: the lens-switch styling, the dev-affordance hide, and the lens-transition
# rules used to be injected from here as EXTRA_CSS. They now live in
# templates/html/styles.css (single source of truth), so there is no injected
# <style> block anymore.

SWITCH_LINKS = (
    '<span class="thumb" aria-hidden="true"></span>'
    '<a data-lens="" href="/" data-hover>Overview</a>'
    '<a data-lens="audio" href="/audio/" data-hover>Audio</a>'
    '<a data-lens="infra" href="/infra/" data-hover>Infra</a>'
)

ROUTER_JS = r"""
<script>
/* Persistent-audio lens router. The rail (cloud + player + reactivity) is mounted
   once and never touched; only #content is swapped, so audio keeps playing across
   lens changes. Real routes (/, /audio/, /infra/) via pushState, with each
   route also emitted as a static page for cold loads / no-JS / crawlers. */
(function(){
  var FR = window.LENS_FRAGMENTS || {}, META = window.LENS_META || {}, DEF = window.LENS_DEFAULT || "";
  var content = document.getElementById('content');
  var railRole = document.getElementById('railRole');
  var sw = document.getElementById('lensSwitch');
  if(!content || !sw) return;
  var spyHandler = null;
  var curSlug = null;
  var thumb = sw.querySelector('.thumb');

  function moveThumb(){
    if(!thumb) return;
    var a = sw.querySelector('a.active'); if(!a) return;
    thumb.style.width = a.offsetWidth + 'px';
    thumb.style.transform = 'translateX(' + (a.offsetLeft - 4) + 'px)';
  }
  addEventListener('resize', moveThumb);

  function bindSpy(){
    var links = [].slice.call(document.querySelectorAll('#railNav a'));
    var secs = links.map(function(a){ try{ return content.querySelector(a.getAttribute('href')); }catch(e){ return null; } });
    if(spyHandler) removeEventListener('scroll', spyHandler);
    spyHandler = function(){ var y=scrollY+innerHeight*0.32, best=0;
      for(var i=0;i<secs.length;i++){ if(secs[i]&&secs[i].offsetTop<=y) best=i; }
      links.forEach(function(l,i){ l.classList.toggle('active', i===best); });
      var prog=document.getElementById('prog');
      if(prog){ var mx=document.documentElement.scrollHeight-innerHeight;
        prog.style.height=(mx>0?Math.min(100,Math.max(0,scrollY/mx*100)):0)+'%'; } };
    addEventListener('scroll', spyHandler, {passive:true}); spyHandler();
  }

  function normalize(path){
    var s=(path||'/').replace(/^\/+|\/+$/g,'');
    return FR.hasOwnProperty(s) ? s : '';
  }

  function paint(slug){
    curSlug = slug;
    content.innerHTML = FR[slug];
    var m = META[slug] || {};
    if(railRole && m.role) railRole.textContent = m.role;
    if(m.title) document.title = m.title;
    [].forEach.call(sw.querySelectorAll('a'), function(a){
      a.classList.toggle('active', a.getAttribute('data-lens')===slug); });
    moveThumb();
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
    var next = (e.state && e.state.lens!=null) ? e.state.lens : normalize(location.pathname);
    /* Fragment-only navigation (#about, #contact, ...) fires popstate with the
       SAME lens. Repainting there scrolls to top and cancels the anchor jump —
       which is exactly what silently broke every in-page link, the whole rail
       nav included. Only act when the lens actually changes. */
    if(next === curSlug) return;
    showLens(next, false); });

  /* Initial paint: server already rendered DEF as live DOM. Re-run through showLens
     to wire switcher/spy/reveal without changing which lens is shown. */
  showLens(DEF, false, true);
})();
</script>
"""


def patch_template(raw: str, site: dict) -> str:
    t = raw
    # rail viz caption (plain text, deliberately not a link)
    viz = site.get("viz_tag")
    if viz:
        t = sub_once(
            t, r'<span class="viz-tag">[^<]*</span>',
            lambda _m: f'<span class="viz-tag">{escape_html(viz)}</span>',
            "viz tag",
        )
    # favicon -> the lufs-vh mark, replacing the inline data-URI cloud
    vh = site.get("visual_hash", {}) or {}
    if vh.get("mark"):
        # Same file as the footer stamp: the tab icon and the seal at the foot
        # of the page are one image at two sizes.
        t = sub_once(
            t, r'<link rel="icon"[^>]*>',
            lambda _m: f'<link rel="icon" type="image/svg+xml" href="{escape_html(vh["mark"])}">',
            "favicon",
        )
    # head: title + meta description -> placeholders
    t = replace_once(
        t, "<title>Resume | Daniel Ramirez</title>",
        "<title>%%PAGETITLE%%</title>", "page title",
    )
    t = sub_once(
        t, r'<meta name="description" content="[^"]*"',
        '<meta name="description" content="%%METADESC%%"', "meta description",
    )
    # Styling now lives in templates/html/styles.css (linked from the template);
    # the lens-switch + transition rules moved there too, so nothing is injected
    # into <head> here anymore.
    # rail role -> id'd placeholder + lens switcher
    t = replace_once(
        t,
        '<div class="rail-role">RESUME_TITLE · Interactive Audio</div>',
        '<div class="rail-role" id="railRole">%%RAILROLE%%</div>\n'
        '    <nav class="lens-switch" id="lensSwitch" aria-label="Resume lens">%%SWITCHER%%</nav>',
        "rail role + switcher",
    )
    # rail nav is generated from SECTIONS so it can't drift from the content
    t = sub_once(
        t, r'(?s)<nav class="rail-nav" id="railNav">.*?</nav>',
        lambda _m: render_rail_nav(), "rail nav",
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
    lenses = site.get("lenses", [])
    if not lenses:
        raise SystemExit("[render] site.yaml has no lenses")

    raw = TEMPLATE.read_text()
    tmpl = patch_template(raw, site)

    # Clean the output dir so stale files from earlier builds never ride along
    # into a deploy (deploy.sh force-pushes whatever is in dist/html).
    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)

    fragments, meta, page_title, meta_desc = {}, {}, {}, {}
    switch_active = {}
    for lens in lenses:
        slug = lens.get("slug", "")
        data = load_yaml(DATA_DIR / lens["data"])
        # The rail nav is shared across lenses, so every lens must render the
        # same section set — fail loudly rather than emit a nav with dead links.
        if not (data.get("certifications") or site.get("certifications")):
            raise SystemExit(
                f"[render] lens '{slug or '/'}' has no certifications and none are "
                f"shared in site.yaml; the shared rail nav would link a dead #certs."
            )
        fragments[slug] = render_lens_inner(data, site)
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
        (out_path / "index.html").write_text(page + "\n")
        outputs.append(str(out_path / "index.html"))
        print(f"  built {'/' if slug=='' else '/'+slug+'/'} -> {out_path/'index.html'}")

    # copy the single stylesheet to the site root so an absolute /styles.css
    # resolves for every lens (root + /sound-design/ + /infra/).
    shutil.copy(TEMPLATE.parent / "styles.css", OUT_DIR / "styles.css")
    print(f"  copied styles.css -> {OUT_DIR/'styles.css'}")

    # the lufs-vh mark ships as a real file: it is both the favicon and the
    # footer mark, and scripts/verify asserts every local reference resolves.
    vh = site.get("visual_hash", {}) or {}
    ref = vh.get("mark")
    if ref:
        src = TEMPLATE.parent / Path(ref).name
        if not src.is_file():
            raise SystemExit(
                f"[render] site.yaml declares visual_hash.mark {ref!r} but {src} "
                f"is missing. Render it with the lufs-vh CLI (see data/site.yaml) "
                f"or clear the key — never hand-draw a substitute."
            )
        shutil.copy(src, OUT_DIR / Path(ref).name)
        print(f"  copied {src.name} -> {OUT_DIR/Path(ref).name}")

    # _headers: the platform file is GENERATED from the root manifest, which
    # stays authoritative (website-portability contract). Without this the host
    # default cached styles.css for 4h against always-fresh HTML.
    root_manifest = BASE_DIR / "site.yaml"
    if root_manifest.is_file():
        rules = (load_yaml(root_manifest) or {}).get("headers") or []
        if rules:
            lines = []
            for rule in rules:
                path, cc = rule.get("path"), rule.get("cache_control")
                if not path or not cc:
                    continue
                lines.append(f"{path}\n  Cache-Control: {cc}\n")
            if lines:
                (OUT_DIR / "_headers").write_text("\n".join(lines))
                print(f"  wrote _headers ({len(lines)} rules) -> {OUT_DIR/'_headers'}")

    return outputs


if __name__ == "__main__":
    if not TEMPLATE.exists():
        print(f"Error: template not found at {TEMPLATE}")
        sys.exit(1)
    outs = build_site()
    print(f"Built {len(outs)} lens pages.")
