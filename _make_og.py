#!/usr/bin/env python3
"""Generate 1200x630 Open Graph share cards on the Kannski brand.

One title-bearing card per page so a shared link clearly advertises a
specific, clickable article (title + kind/date), not a generic banner.

Fonts (Spectral + IBM Plex Mono) are expected in _fonts/. Fetch with:
  base=https://raw.githubusercontent.com/google/fonts/main/ofl
  curl -O $base/spectral/Spectral-{Bold,Regular,Italic}.ttf
  curl -O $base/ibmplexmono/IBMPlexMono-{Regular,Medium}.ttf
Run: python3 _make_og.py   (writes img/og-*.png)
"""
import glob
import html
import os
import re
import random
from PIL import Image, ImageDraw, ImageFont

W, H = 1200, 630
CREAM = (244, 239, 228)
INK = (33, 29, 24)
BLUE = (0, 51, 153)
RED = (163, 33, 26)
MUTED = (111, 106, 95)
LINE = (226, 220, 205)
WHITE = (255, 255, 255)

SERIF_B = "_fonts/Spectral-Bold.ttf"
SERIF_R = "_fonts/Spectral-Regular.ttf"
SERIF_I = "_fonts/Spectral-Italic.ttf"
MONO = "_fonts/IBMPlexMono-Medium.ttf"

L = 84  # content left margin


def f(path, size):
    return ImageFont.truetype(path, size)


def text_tracked(d, xy, s, font, fill, tracking=0):
    x, y = xy
    for ch in s:
        d.text((x, y), ch, font=font, fill=fill)
        x += d.textlength(ch, font=font) + tracking
    return x - xy[0] - (tracking if s else 0)


def tracked_width(d, s, font, tracking=0):
    if not s:
        return 0
    return sum(d.textlength(ch, font=font) + tracking for ch in s) - tracking


def base_canvas():
    img = Image.new("RGB", (W, H), CREAM)
    d = ImageDraw.Draw(img)
    d.rectangle([28, 28, W - 29, H - 29], outline=LINE, width=2)
    return img, d


def signal_line(d, x0, y, width, amp=8, n=44, seed=7):
    random.seed(seed)
    pts = []
    step = width / n
    for i in range(n + 1):
        damp = max(0.0, 1 - i / (n * 0.72))
        pts.append((x0 + i * step, y + (random.random() - 0.5) * 2 * amp * damp))
    d.line(pts, fill=BLUE, width=3, joint="curve")


def wrap(d, text, font, maxw):
    lines, cur = [], ""
    for word in text.split():
        t = (cur + " " + word).strip()
        if d.textlength(t, font=font) <= maxw or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def fit_title(d, text, maxw, avail_h, sizes, max_lines):
    for size in sizes:
        font = f(SERIF_B, size)
        lines = wrap(d, text, font, maxw)
        lh = size * 1.1
        if len(lines) <= max_lines and len(lines) * lh <= avail_h:
            return font, lines, lh
    font = f(SERIF_B, sizes[-1])
    return font, wrap(d, text, font, maxw), sizes[-1] * 1.1


def footer(d, accent=RED):
    fy = H - 92
    d.text((L, fy), "Kannski", font=f(SERIF_B, 46), fill=INK)
    wm = d.textlength("Kannski", font=f(SERIF_B, 46))
    text_tracked(d, (L + wm + 18, fy + 18), "KANNSKI-ESB.IS", f(MONO, 18), accent, 3)
    name = "GAUTI B. EGGERTSSON"
    nw = tracked_width(d, name, f(MONO, 18), 3)
    text_tracked(d, (W - L - nw, fy + 18), name, f(MONO, 18), MUTED, 3)


def title_card(out, eyebrow, title, subtitle=None):
    img, d = base_canvas()
    if eyebrow:
        text_tracked(d, (L, 92), eyebrow.upper(), f(MONO, 20), RED, 3)
        signal_line(d, L, 144, 300)
    top, bot = 182, 470
    avail = bot - top
    maxw = W - 2 * L
    font, lines, lh = fit_title(d, title, maxw, avail,
                                [76, 68, 60, 54, 48, 44, 40, 36], 6)
    block = len(lines) * lh
    y = top + max(0, (avail - block) / 2)
    for ln in lines:
        d.text((L, y), ln, font=font, fill=INK)
        y += lh
    if subtitle:
        sf = f(SERIF_I, 28)
        for ln in wrap(d, subtitle, sf, maxw)[:2]:
            d.text((L, y + 6), ln, font=sf, fill=MUTED)
            y += 36
    footer(d)
    img.save(out)


def brand_card(out):
    img, d = base_canvas()
    text_tracked(d, (L, 92), "ÞJÓÐARATKVÆÐAGREIÐSLA · ÁGÚST 2026", f(MONO, 21), RED, 4)
    signal_line(d, L, 150, 360)
    d.text((L - 4, 188), "Kannski", font=f(SERIF_B, 168), fill=INK)
    d.text((L, 392), "Skrif um Evrópusambandið og", font=f(SERIF_R, 40), fill=MUTED)
    d.text((L, 440), "þjóðaratkvæðagreiðsluna í ágúst", font=f(SERIF_R, 40), fill=MUTED)
    d.text((L, 498), "eftir Gauta B. Eggertsson", font=f(SERIF_I, 30), fill=INK)
    text_tracked(d, (L, 556), "KANNSKI-ESB.IS", f(MONO, 19), RED, 3)
    img.save(out)


# ---- extraction helpers -------------------------------------------------
def read(p):
    with open(p, encoding="utf-8") as fh:
        return fh.read()


def page_title(s):
    m = re.search(r"<title>(.*?)</title>", s, re.S)
    t = html.unescape(m.group(1)).strip()
    return re.sub(r"\s*[—-]\s*Kannski\s*$", "", t)


def article_meta(s):
    m = re.search(r"<span>([^<]*\d{4})</span>\s*<span[^>]*>([^<]*)</span>", s)
    if not m:
        return None, None
    return html.unescape(m.group(1)).strip(), html.unescape(m.group(2)).strip()


def category_meta(s):
    part = re.search(r">(Hluti\s*\d+)<", s)
    sub = re.search(r"</h1>.*?<p[^>]*>([^<]+)</p>", s, re.S)
    return (part.group(1) if part else "Efnisflokkur",
            html.unescape(sub.group(1)).strip() if sub else None)


# ---- build --------------------------------------------------------------
def main():
    brand_card("img/og-card.png")  # homepage / site identity

    s = read("um.html")
    title_card("img/og-um.png", "Um höfundinn", page_title(s))

    s = read("allt.html")
    title_card("img/og-allt.png", "Tímalína", page_title(s))

    for p in sorted(glob.glob("flokkur/*.html")):
        s = read(p)
        eyebrow, sub = category_meta(s)
        out = "img/og-fl-" + os.path.basename(p).replace(".html", ".png")
        title_card(out, eyebrow, page_title(s), sub)

    for p in sorted(glob.glob("grein/*.html")):
        s = read(p)
        date, kind = article_meta(s)
        eyebrow = f"{kind} · {date}" if kind and date else "Skrif"
        out = "img/og-" + os.path.basename(p).replace(".html", ".png")
        title_card(out, eyebrow, page_title(s))

    print("cards written:", len(glob.glob("img/og-*.png")))


if __name__ == "__main__":
    main()
