"""Render the stats as a dithered pixel panel matching the profile's boot log.

Reads the numbers out of the freshly generated overview.svg and languages.svg
and draws them with the same 5-tone palette, Bayer 8x8 dithering, Silkscreen
font and panel chrome as assets/src/boot.py in bynguts/bynguts.

Fonts: Silkscreen-Regular.ttf and Silkscreen-Bold.ttf in theme/fonts/.
Run: python theme/render_card.py overview.svg languages.svg activity.png
"""
import re
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

FONTS = Path(__file__).parent / "fonts"
OVERVIEW, LANGUAGES, OUT = (Path(p) for p in sys.argv[1:4])

W, H = 450, 144  # same height as the boot log
SCALE = 2
TOP_LANGS = 7

# void, dried blood, crimson, bright red, bone
PALETTE = np.array(
    [(13, 17, 23), (69, 10, 10), (153, 27, 27), (239, 68, 68), (240, 232, 226)],
    dtype=np.uint8,
)
VOID, BLOOD, CRIMSON, BRIGHT, BONE = range(5)
LEVELS = len(PALETTE)

LABELS = ["STARS", "FORKS", "CONTRIBUTIONS", "LINES CHANGED", "VIEWS / 14D", "REPOS TOUCHED"]


def bayer(n):
    m = np.array([[0]])
    while m.shape[0] < n:
        m = np.block([[4 * m, 4 * m + 2], [4 * m + 3, 4 * m + 1]])
    return (m + 0.5) / (n * n)


B8 = bayer(8)


def dither(field):
    h, w = field.shape
    t = np.tile(B8, (h // 8 + 1, w // 8 + 1))[:h, :w]
    v = np.clip(field, 0, 1) * (LEVELS - 1)
    base = np.floor(v)
    return np.clip(base + (v - base > t), 0, LEVELS - 1).astype(np.uint8)


_fonts = {}


def text(idx, s, x, y, color, bold=False):
    """Draw pixel text into the index buffer; returns the x after the text."""
    name = "Silkscreen-Bold.ttf" if bold else "Silkscreen-Regular.ttf"
    f = _fonts.setdefault(name, ImageFont.truetype(str(FONTS / name), 8))
    l, t, r, b = f.getbbox(s)
    im = Image.new("L", (r - l, b - t), 0)
    ImageDraw.Draw(im).text((-l, -t), s, font=f, fill=255)
    m = np.asarray(im) > 127
    h, w = m.shape
    idx[y : y + h, x : x + w][m] = color
    return x + w


def width(s):
    return text(np.zeros((16, 400), np.uint8), s, 0, 0, 1)


def leader(idx, y, x0, x1):
    for dx in range(x0 + 6, x1 - 6, 4):
        idx[y + 4, dx] = BLOOD


# --- data ------------------------------------------------------------------

values = re.findall(r'class="value"[^>]*>([^<]+)<', OVERVIEW.read_text(encoding="utf-8"))
if len(values) != len(LABELS):
    sys.exit(f"expected {len(LABELS)} overview values, found {len(values)}")
langs = re.findall(
    r'<span class="lang">([^<]+)</span>\s*<span class="percent">([\d.]+)%</span>',
    LANGUAGES.read_text(encoding="utf-8"),
)
all_langs = [(name, float(p)) for name, p in langs]
langs = all_langs[:TOP_LANGS]
rest = sum(p for _, p in all_langs[TOP_LANGS:])
if rest >= 0.05:
    langs.append(("OTHERS", rest))
rows = list(zip(LABELS, values)) + [("LANGUAGES USED", str(len(all_langs)))]

# --- panels (same chrome as boot.py) ---------------------------------------

GAP = 8
BOX = (W - GAP) // 2
LY, STEP = 22, 15
SPAN = (len(langs) - 1) * STEP  # both boxes spread their rows over this height


def box(x0, title):
    """Framed panel with a glow and dithered title bar, like the boot log."""
    yy, xx = np.mgrid[0:H, 0:BOX].astype(np.float32)
    glow = np.clip(1.0 - np.sqrt(((xx - BOX) / 200.0) ** 2 + (yy / 150.0) ** 2), 0, 1) ** 2 * 0.22
    panel = dither(glow)
    panel[0, :] = panel[-1, :] = CRIMSON
    panel[:, 0] = panel[:, -1] = CRIMSON
    panel[1:14, 1:-1] = dither(np.tile(np.clip(1.0 - np.arange(BOX - 2) / (BOX * 0.9), 0, 1) * 0.5, (13, 1)))
    text(panel, title, 8, 4, BONE, bold=True)
    idx[:, x0 : x0 + BOX] = panel


idx = np.zeros((H, W), np.uint8)

# left: overview
box(0, "BYNGUTS.STATS")
for i, (label, value) in enumerate(rows):
    y = LY + round(i * SPAN / (len(rows) - 1))
    x = text(idx, label, 10, y, BONE)
    vx = BOX - 10 - width(value)
    leader(idx, y, x, vx)
    text(idx, value, vx, y, BRIGHT)

# right: languages, each bar scaled to the largest
RX = W - BOX
box(RX, "BYNGUTS.LANGUAGES")
name_w = max(width(n.upper()) for n, _ in langs) + 8
pct_w = width("00.0%")
bar_x0, bar_x1 = RX + 10 + name_w, W - 10 - pct_w - 6
top = langs[0][1] if langs else 1.0
for i, (name, pct) in enumerate(langs):
    y = LY + i * STEP
    text(idx, name.upper(), RX + 10, y, BONE)
    full = bar_x1 - bar_x0
    n = max(2, int(full * pct / top))
    idx[y + 6, bar_x0:bar_x1] = BLOOD  # track
    # dark-to-bright like the boot log's charging bar
    ramp = np.linspace(0.35, 1.0, n) * (0.6 + 0.4 * (1 - i / TOP_LANGS))
    idx[y : y + 7, bar_x0 : bar_x0 + n] = dither(np.tile(ramp, (7, 1)))
    s = f"{pct:.1f}%"
    text(idx, s, W - 10 - width(s), y, BRIGHT)

im = Image.fromarray(PALETTE[idx], "RGB").resize((W * SCALE, H * SCALE), Image.NEAREST)
pal = Image.new("P", (1, 1))
pal.putpalette(PALETTE.flatten().tolist() + [0] * (768 - PALETTE.size))
im.quantize(palette=pal, dither=Image.Dither.NONE).save(OUT, optimize=True)
print(OUT, OUT.stat().st_size // 1024, "KB")
