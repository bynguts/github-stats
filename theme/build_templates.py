"""Build the crimson-dither stats card templates in src/templates/.

Matches the bynguts profile README: void background, crimson frame, a dithered
title bar (Bayer-style SVG patterns) and pixel/mono fonts embedded as subset
WOFF2 data URIs (SVGs loaded through <img> can't fetch external fonts).

Fonts (OFL, github.com/google/fonts) go in theme/fonts/:
Silkscreen-Regular.ttf, SpaceMono-Regular.ttf, SpaceMono-Bold.ttf.
Run: python theme/build_templates.py
"""
import base64
import io
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parents[1]
FONTS = Path(__file__).parent / "fonts"
TEMPLATES = ROOT / "src" / "templates"

# Language names, numbers and labels are all printable ASCII
ASCII = "".join(chr(c) for c in range(0x20, 0x7F))


def font_uri(name):
    font = TTFont(FONTS / name)
    opts = subset.Options()
    opts.flavor = "woff2"
    opts.layout_features = []
    opts.name_IDs = []
    opts.notdef_outline = True
    sub = subset.Subsetter(opts)
    sub.populate(text=ASCII)
    sub.subset(font)
    buf = io.BytesIO()
    font.flavor = "woff2"
    font.save(buf)
    return "data:font/woff2;base64," + base64.b64encode(buf.getvalue()).decode()


FONT_CSS = f"""
@font-face {{
  font-family: "Silk";
  src: url({font_uri("Silkscreen-Regular.ttf")}) format("woff2");
}}
@font-face {{
  font-family: "Mono";
  font-weight: 400;
  src: url({font_uri("SpaceMono-Regular.ttf")}) format("woff2");
}}
@font-face {{
  font-family: "Mono";
  font-weight: 700;
  src: url({font_uri("SpaceMono-Bold.ttf")}) format("woff2");
}}
"""

# Ordered-dither densities for the title bar, in 2px dots
PATTERNS = """
<defs>
  <pattern id="d75" width="4" height="4" patternUnits="userSpaceOnUse">
    <rect width="4" height="4" fill="#7f1d1d"/><rect x="2" y="2" width="2" height="2" fill="#0d1117"/>
  </pattern>
  <pattern id="d50" width="4" height="4" patternUnits="userSpaceOnUse">
    <rect width="2" height="2" fill="#7f1d1d"/><rect x="2" y="2" width="2" height="2" fill="#7f1d1d"/>
  </pattern>
  <pattern id="d25" width="4" height="4" patternUnits="userSpaceOnUse">
    <rect width="2" height="2" fill="#7f1d1d"/>
  </pattern>
  <pattern id="d12" width="8" height="4" patternUnits="userSpaceOnUse">
    <rect width="2" height="2" fill="#5c1818"/>
  </pattern>
</defs>
"""


def title_bar(title, note):
    return f"""
<g shape-rendering="crispEdges">
  <rect x="6" y="6" width="120" height="22" fill="#7f1d1d"/>
  <rect x="126" y="6" width="56" height="22" fill="url(#d75)"/>
  <rect x="182" y="6" width="56" height="22" fill="url(#d50)"/>
  <rect x="238" y="6" width="56" height="22" fill="url(#d25)"/>
  <rect x="294" y="6" width="54" height="22" fill="url(#d12)"/>
</g>
<text x="16" y="22" class="title">{title}</text>
<text x="340" y="21" class="note" text-anchor="end">{note}</text>
"""


BASE_CSS = """
svg { font-family: "Mono", ui-monospace, monospace; }
#background { fill: #0d1117; stroke: #7f1d1d; stroke-width: 1px; }
.title { font-family: "Silk", monospace; font-size: 16px; fill: #f0e8e2; }
.note { font-family: "Mono", monospace; font-size: 10px; fill: #ef4444; letter-spacing: 0.05em; }
@keyframes flickerIn { 0% { opacity: 0; } 50% { opacity: 0.4; } 75% { opacity: 0.1; } 100% { opacity: 1; } }
"""

OCTICONS = {
    "star": "M8 .25a.75.75 0 01.673.418l1.882 3.815 4.21.612a.75.75 0 01.416 1.279l-3.046 2.97.719 4.192a.75.75 0 01-1.088.791L8 12.347l-3.766 1.98a.75.75 0 01-1.088-.79l.72-4.194L.818 6.374a.75.75 0 01.416-1.28l4.21-.611L7.327.668A.75.75 0 018 .25z",
    "fork": "M5 3.25a.75.75 0 11-1.5 0 .75.75 0 011.5 0zm0 2.122a2.25 2.25 0 10-1.5 0v.878A2.25 2.25 0 005.75 8.5h1.5v2.128a2.251 2.251 0 101.5 0V8.5h1.5a2.25 2.25 0 002.25-2.25v-.878a2.25 2.25 0 10-1.5 0v.878a.75.75 0 01-.75.75h-4.5A.75.75 0 015 6.25v-.878zm3.75 7.378a.75.75 0 11-1.5 0 .75.75 0 011.5 0zm3-8.75a.75.75 0 100-1.5.75.75 0 000 1.5z",
    "commit": "M11.93 8.5a4.002 4.002 0 01-7.86 0H.75a.75.75 0 010-1.5h3.32a4.002 4.002 0 017.86 0h3.32a.75.75 0 010 1.5h-3.32zM8 10.5a2.5 2.5 0 100-5 2.5 2.5 0 000 5z",
    "diff": "M8.75 1.75a.75.75 0 00-1.5 0V5H4a.75.75 0 000 1.5h3.25v3.25a.75.75 0 001.5 0V6.5H12A.75.75 0 0012 5H8.75V1.75zM4 13a.75.75 0 000 1.5h8a.75.75 0 100-1.5H4z",
    "eye": "M8 2c1.981 0 3.671.992 4.933 2.078 1.27 1.091 2.187 2.345 2.637 3.023a1.62 1.62 0 010 1.798c-.45.678-1.367 1.932-2.637 3.023C11.67 13.008 9.981 14 8 14c-1.981 0-3.671-.992-4.933-2.078C1.797 10.83.88 9.576.43 8.898a1.62 1.62 0 010-1.798c.45-.677 1.367-1.931 2.637-3.022C4.33 2.992 6.019 2 8 2zM8 10a2 2 0 100-4 2 2 0 000 4z",
    "repo": "M2 2.5A2.5 2.5 0 014.5 0h8.75a.75.75 0 01.75.75v12.5a.75.75 0 01-.75.75h-2.5a.75.75 0 010-1.5h1.75v-2h-8a1 1 0 00-.714 1.7.75.75 0 11-1.072 1.05A2.495 2.495 0 012 11.5v-9z",
}

ROWS = [
    ("star", "Stars", "stars"),
    ("fork", "Forks", "forks"),
    ("commit", "Contributions", "contributions"),
    ("diff", "Lines changed", "lines_changed"),
    ("eye", "Views / 14d", "views"),
    ("repo", "Repos touched", "repos"),
]


def overview():
    rows = []
    for i, (icon, label, key) in enumerate(ROWS):
        y = 54 + i * 25
        rows.append(
            f"""<g class="row" style="animation-delay: {i * 120}ms">
  <svg x="18" y="{y - 12}" width="14" height="14" viewBox="0 0 16 16"><path class="icon" d="{OCTICONS[icon]}"/></svg>
  <text x="40" y="{y}" class="label">{label}</text>
  <text x="340" y="{y}" class="value" text-anchor="end">{{{{ {key} }}}}</text>
  <line x1="40" y1="{y + 7.5}" x2="340" y2="{y + 7.5}" stroke="#450a0a" stroke-width="1" stroke-dasharray="2 4"/>
</g>"""
        )
    return f"""<svg id="gh-dark-mode-only" width="360" height="210" xmlns="http://www.w3.org/2000/svg">
<style>{FONT_CSS}{BASE_CSS}
.label {{ font-size: 11px; fill: #c9bfb9; text-transform: uppercase; letter-spacing: 0.06em; }}
.value {{ font-size: 13px; font-weight: 700; fill: #ef4444; }}
.icon {{ fill: #b91c1c; fill-rule: evenodd; }}
.row {{ opacity: 0; animation: flickerIn 0.6s steps(4) forwards; }}
</style>
{PATTERNS}
<rect x="5.5" y="5.5" width="349" height="199" id="background"/>
{title_bar("BYNGUTS.STATS", "// overview")}
{chr(10).join(rows)}
</svg>
"""


RAMP = ["#ef4444", "#dc2626", "#b91c1c", "#991b1b", "#7f1d1d", "#6b1a1a", "#5c1818", "#4a1515"]


def languages():
    # biggest language brightest; everything past the ramp stays darkest
    sel = [f"nth-child({i + 1})" for i in range(len(RAMP) - 1)] + [f"nth-child(n+{len(RAMP)})"]
    ramp_css = "\n".join(
        f".progress-item:{s} {{ background-color: {c} !important; }}\n"
        f"li:{s} .octicon {{ fill: {c} !important; }}"
        for s, c in zip(sel, RAMP)
    )
    return f"""<svg id="gh-dark-mode-only" width="360" height="210" xmlns="http://www.w3.org/2000/svg">
<style>{FONT_CSS}{BASE_CSS}
foreignObject {{ width: 318px; height: 160px; }}
ul {{ list-style: none; padding-left: 0; margin: 0; }}
li {{
  display: inline-flex; align-items: center; flex-wrap: nowrap;
  margin: 0 1.2ch 3px 0; font-size: 11px;
  opacity: 0; animation: flickerIn 0.6s steps(4) forwards;
}}
div.ellipsis {{ height: 160px; overflow: hidden; font-family: "Mono", ui-monospace, monospace; }}
.octicon {{ margin-right: 0.4ch; vertical-align: top; }}
.progress {{
  display: flex; height: 10px; overflow: hidden; margin: 2px 0 12px 0;
  background-color: #161b22; outline: 1px solid #450a0a;
}}
.progress-item {{ outline: 1px solid #0d1117; }}
.lang {{ font-weight: 700; margin-right: 4px; color: #f0e8e2; text-transform: uppercase; letter-spacing: 0.04em; }}
.percent {{ color: #b91c1c; }}
{ramp_css}
</style>
{PATTERNS}
<rect x="5.5" y="5.5" width="349" height="199" id="background"/>
{title_bar("LANGUAGES", "// by file size")}
<foreignObject x="18" y="38" width="324" height="160">
<div xmlns="http://www.w3.org/1999/xhtml" class="ellipsis">

<div>
<span class="progress">
{{{{ progress }}}}
</span>
</div>

<ul>

{{{{ lang_list }}}}

</ul>

</div>
</foreignObject>
</svg>
"""


(TEMPLATES / "overview.svg").write_text(overview(), encoding="utf-8", newline="\n")
(TEMPLATES / "languages.svg").write_text(languages(), encoding="utf-8", newline="\n")
for n in ("overview.svg", "languages.svg"):
    print(n, (TEMPLATES / n).stat().st_size // 1024, "KB")
