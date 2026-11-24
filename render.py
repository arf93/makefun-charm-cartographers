#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Treasure Map of the Isle of Misplaced Fortune
---------------------------------------------
Hand-inked style treasure map renderer (Pillow only).
Draws a fictional island map 1024x1024, sepia ink on parchment,
with 11 labelled places and a red dashed route to X.
Output: entry.png (same directory as this script).
"""
import io
import math
import os
import random

from PIL import Image, ImageDraw, ImageFont

W = H = 1024
MAX_BYTES = 1_048_576  # make.fun entry limit: <= 1 MiB
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "entry.png")

# ---- consistent sepia ink-on-parchment palette ----
INK      = (72, 47, 26)      # main ink
INK_SOFT = (116, 82, 48)     # lighter wash
INK_PALE = (136, 99, 60)     # faint detail
RED      = (168, 36, 30)     # route + X
PARCH    = (236, 215, 170)   # parchment base
ISLAND   = (227, 203, 150)   # island fill
CREAM    = (246, 231, 194)   # text halo
GOLD     = (178, 136, 52)    # gilded lagoon sparkle

FONT_DIR = "/usr/share/fonts/truetype/dejavu"


def F(name: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(os.path.join(FONT_DIR, name), size)


def serif(size: int, bold: bool = True) -> ImageFont.FreeTypeFont:
    return F("DejaVuSerif-Bold.ttf" if bold else "DejaVuSerif.ttf", size)


def hand(size: int) -> ImageFont.FreeTypeFont:
    try:
        return F("DejaVuSans-Oblique.ttf", size)
    except OSError:
        return F("DejaVuSans.ttf", size)


random.seed(20261101)

# ================= island geometry =================
CX, CY, R = 505, 545, 300


def coast_r(theta: float) -> float:
    """Distance from island centre to coastline at angle theta."""
    r = R * (1.0
             + 0.17 * math.sin(3 * theta + 1.2)
             + 0.11 * math.sin(5 * theta + 0.4)
             + 0.06 * math.sin(7 * theta + 2.0)
             + 0.04 * math.sin(11 * theta + 3.0))
    r -= 46 * math.exp(-((theta + 0.10) ** 2) / (2 * 0.11 ** 2))   # Portly Parrot Bay (E)
    r -= 34 * math.exp(-((theta - math.pi) ** 2) / (2 * 0.10 ** 2))  # Dead Man's Cove (W)
    r -= 26 * math.exp(-((theta - 0.55) ** 2) / (2 * 0.09 ** 2))    # Gilded Lagoon (SE)
    return r


def coast(n: int = 320) -> list:
    pts = []
    for i in range(n):
        t = 2 * math.pi * i / n
        rr = coast_r(t) * (1 + 0.010 * (random.random() - 0.5))
        pts.append((CX + rr * math.cos(t), CY + rr * math.sin(t)))
    return pts


def in_sea(x: float, y: float, pad: float = 14.0) -> bool:
    dx, dy = x - CX, y - CY
    r = math.hypot(dx, dy)
    if r < 12:
        return False
    return r > coast_r(math.atan2(dy, dx)) + pad


# ================= drawing helpers =================
def halo_label(d, cx, cy, text, font, fill=INK, stroke=CREAM, sw=3, anchor="mm"):
    d.text((cx, cy), text, font=font, fill=fill, anchor=anchor,
           stroke_width=sw, stroke_fill=stroke)


def dashed_polyline(d, pts, width, fill, dash=17.0, gap=13.0):
    segs = [(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]
    lens = [math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in segs]
    total = sum(lens)

    def at(s):
        for (a, b), L in zip(segs, lens):
            if s <= L or L == 0:
                t = 1.0 if L == 0 else s / L
                return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
            s -= L
        return pts[-1]

    s = 0.0
    while s < total:
        e = min(s + dash, total)
        d.line([at(s), at(e)], fill=fill, width=width)
        s = e + gap


def dotted_path(d, pts, color=INK_SOFT, step=13.0):
    segs = [(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]
    lens = [math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in segs]
    total = sum(lens)
    s = 0.0
    while s < total:
        rem = s
        for (a, b), L in zip(segs, lens):
            if rem <= L or L == 0:
                t = 1.0 if L == 0 else rem / L
                x, y = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
                r = 3.0 if (int(s / step) % 2) else 2.2
                d.ellipse([x - r, y - r, x + r, y + r], fill=color)
                break
            rem -= L
        s += step


def rot_label(img, text, cx, cy, font, angle, fill=INK, stroke=CREAM, sw=2):
    probe = ImageDraw.Draw(Image.new("RGBA", (4, 4)))
    bbox = probe.textbbox((0, 0), text, font=font, stroke_width=sw)
    w = bbox[2] - bbox[0] + 10
    h = bbox[3] - bbox[1] + 10
    tmp = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    td = ImageDraw.Draw(tmp)
    td.text((5 - bbox[0], 5 - bbox[1]), text, font=font, fill=fill,
            stroke_width=sw, stroke_fill=stroke)
    tmp = tmp.rotate(angle, expand=True, resample=Image.BICUBIC)
    img.paste(tmp, (int(cx - tmp.width / 2), int(cy - tmp.height / 2)), tmp)


# ================= doodle icons =================
def icon_skull(d, x, y):
    d.polygon([(x - 30, y + 16), (x - 22, y - 4), (x - 12, y - 12), (x + 6, y - 14),
               (x + 20, y - 2), (x + 27, y + 16)], fill=ISLAND, outline=INK, width=2)
    d.ellipse([x - 12, y - 12, x + 12, y + 8], fill=(242, 234, 210), outline=INK, width=2)
    d.ellipse([x - 8, y - 8, x - 2, y - 2], fill=INK)
    d.ellipse([x + 2, y - 8, x + 8, y - 2], fill=INK)
    d.polygon([(x - 3, y + 2), (x + 3, y + 2), (x, y + 7)], fill=INK)


def icon_mountain(d, x, y):
    d.polygon([(x - 42, y + 40), (x - 6, y - 14), (x + 34, y + 40)], fill=ISLAND, outline=INK, width=2)
    d.polygon([(x - 10, y + 2), (x - 6, y - 14), (x + 2, y - 8), (x - 2, y + 2)], fill=CREAM, outline=INK_SOFT)
    d.polygon([(x + 14, y + 40), (x + 30, y + 10), (x + 44, y + 40)], fill=ISLAND, outline=INK, width=2)
    d.ellipse([x - 21, y - 26, x - 7, y - 12], outline=INK_SOFT, width=1)
    d.ellipse([x + 11, y - 34, x + 25, y - 20], outline=INK_SOFT, width=1)
    d.line([(x - 24, y + 30), (x + 10, y + 34)], fill=INK_SOFT, width=1)
    d.line([(x - 14, y + 20), (x + 4, y + 24)], fill=INK_SOFT, width=1)


def icon_widow(d, x, y):
    d.polygon([(x - 16, y + 36), (x + 2, y - 34), (x + 22, y + 36)], fill=ISLAND, outline=INK, width=2)
    d.line([(x - 10, y + 24), (x + 2, y - 10), (x + 12, y + 24)], fill=INK_SOFT, width=1)
    d.line([(x + 2, y - 34), (x + 2, y - 44)], fill=INK, width=2)
    d.polygon([(x + 2, y - 44), (x + 14, y - 40), (x + 2, y - 36)], fill=INK)


def icon_tree(d, x, y, s=1.0):
    d.polygon([(x - 11 * s, y + 22 * s), (x, y - 14 * s), (x + 11 * s, y + 22 * s)],
              fill=ISLAND, outline=INK, width=2)
    d.line([(x, y - 14 * s), (x, y - 22 * s)], fill=INK_SOFT, width=2)


def icon_woods(d, x, y):
    icon_tree(d, x - 16, y + 12, 1.1)
    icon_tree(d, x + 7, y + 16, 1.0)
    icon_tree(d, x + 20, y + 6, 0.85)
    icon_tree(d, x - 2, y + 2, 1.25)


def icon_wreck(d, x, y):
    d.polygon([(x - 22, y + 4), (x - 16, y + 18), (x + 18, y + 18), (x + 24, y + 4)],
              fill=ISLAND, outline=INK, width=2)
    d.line([(x - 2, y + 4), (x - 2, y - 24)], fill=INK, width=2)
    d.polygon([(x - 2, y - 24), (x + 16, y - 18), (x - 2, y - 10)], fill=INK)
    for px in (x - 14, x, x + 14):
        d.line([(px, y + 11), (px + 3, y + 14)], fill=INK_SOFT, width=1)


def icon_marsh(d, x, y):
    d.ellipse([x - 34, y - 8, x + 34, y + 20], fill=(219, 195, 142))
    for dx in (-26, -12, 0, 12, 26):
        bx = x + dx
        d.line([(bx - 3, y), (bx - 1, y - 14)], fill=INK_SOFT, width=2)
        d.line([(bx + 1, y - 2), (bx + 4, y - 13)], fill=INK_SOFT, width=2)
        d.line([(bx, y), (bx, y - 16)], fill=INK, width=1)
    for p in ((x - 16, y + 8), (x + 8, y + 12), (x + 20, y + 6)):
        d.ellipse([p[0] - 2, p[1] - 2, p[0] + 2, p[1] + 2], outline=INK_SOFT, width=1)


def icon_parrot(d, x, y):
    d.line([(x, y + 16), (x, y - 6)], fill=INK, width=4)
    d.ellipse([x - 17, y - 27, x + 15, y + 2], fill=ISLAND, outline=INK, width=2)
    d.ellipse([x + 10, y - 34, x + 24, y - 18], fill=ISLAND, outline=INK, width=2)
    d.polygon([(x + 23, y - 27), (x + 31, y - 23), (x + 23, y - 21)], fill=INK)
    d.ellipse([x + 14, y - 30, x + 17, y - 27], fill=INK)
    d.line([(x - 16, y - 14), (x - 26, y + 2), (x - 14, y + 2)], fill=INK, width=2)
    d.line([(x - 6, y - 2), (x - 9, y + 8)], fill=INK_SOFT, width=2)


def icon_inn(d, x, y):
    d.rectangle([x - 20, y - 8, x + 20, y + 18], fill=ISLAND, outline=INK, width=2)
    d.polygon([(x - 24, y - 8), (x, y - 26), (x + 24, y - 8)], fill=ISLAND, outline=INK, width=2)
    d.rectangle([x - 4, y + 2, x + 7, y + 18], fill=INK)
    d.rectangle([x - 14, y - 2, x - 8, y + 4], outline=INK)
    d.line([(x, y - 26), (x, y - 34)], fill=INK, width=2)
    ax, ay = x + 36, y + 10
    d.ellipse([ax - 7, ay - 14, ax + 7, ay], outline=INK, width=2)
    d.line([(ax, ay - 14), (ax, ay + 8)], fill=INK, width=2)
    d.arc([ax - 12, ay - 6, ax + 12, ay + 16], 200, 340, fill=INK, width=2)
    d.line([(ax - 12, ay + 2), (ax + 12, ay + 8)], fill=INK, width=2)


def icon_lagoon(d, x, y):
    d.ellipse([x - 30, y - 16, x + 30, y + 16], fill=(216, 190, 134), outline=INK_SOFT, width=1)
    for sx, sy in ((-16, -4), (8, -8), (18, 4), (-4, 8)):
        d.line([(x + sx - 4, y + sy), (x + sx + 4, y + sy)], fill=GOLD, width=2)
        d.line([(x + sx, y + sy - 4), (x + sx, y + sy + 4)], fill=GOLD, width=2)


def icon_kraken(d, x, y):
    for dx, ang in ((-34, -0.5), (-18, -1.1), (6, -1.6), (28, -0.7)):
        pts = []
        for i in range(9):
            t = i / 8.0
            pts.append((x + dx * t + 18 * math.sin(t * 4 + ang), y + 8 + 64 * t))
        for i in range(len(pts) - 1):
            w = max(1, int(7 * (1 - i / (len(pts) - 1))))
            d.line([pts[i], pts[i + 1]], fill=INK, width=w)
    d.ellipse([x - 26, y + 2, x + 26, y + 30], fill=ISLAND, outline=INK, width=2)
    d.ellipse([x - 12, y + 8, x - 6, y + 14], fill=INK)
    d.ellipse([x + 6, y + 8, x + 12, y + 14], fill=INK)


def icon_serpent(d, x, y):
    pts = []
    for i in range(17):
        t = i / 16.0
        pts.append((x - 90 + 180 * t, y + 14 * math.sin(t * 2 * math.pi - 1.0) + math.sin(t * 7) * 3))
    for i in range(len(pts) - 1):
        w = max(1, int(6 * (1 - i / (len(pts) - 1))))
        d.line([pts[i], pts[i + 1]], fill=INK, width=w)
    hx, hy = pts[-1][0] + 2, pts[-1][1] - 6
    d.ellipse([hx - 9, hy - 7, hx + 9, hy + 7], fill=ISLAND, outline=INK, width=2)
    d.ellipse([hx + 3, hy - 3, hx + 6, hy], fill=INK)
    d.polygon([(hx + 9, hy - 2), (hx + 17, hy + 1), (hx + 9, hy + 4)], fill=INK)
    d.line([pts[0], (pts[0][0] - 10, pts[0][1] + 6)], fill=INK, width=3)


def icon_ship(d, x, y):
    d.polygon([(x - 34, y + 2), (x - 28, y + 20), (x + 26, y + 20), (x + 36, y + 2)],
              fill=ISLAND, outline=INK, width=2)
    d.line([(x - 2, y + 2), (x - 2, y - 34)], fill=INK, width=3)
    d.polygon([(x - 2, y - 32), (x - 26, y - 14), (x - 4, y - 12)], fill=INK)
    d.polygon([(x, y - 30), (x + 22, y - 10), (x + 2, y - 8)], outline=INK, width=2)
    d.line([(x - 2, y - 34), (x - 2, y - 42)], fill=INK, width=2)
    d.polygon([(x - 2, y - 42), (x + 10, y - 38), (x - 2, y - 34)], fill=INK)
    d.line([(x - 14, y + 12), (x - 22, y + 12)], fill=INK_SOFT, width=1)
    d.line([(x + 18, y + 12), (x + 26, y + 12)], fill=INK_SOFT, width=1)


def icon_compass(d, cx, cy, s=78):
    d.ellipse([cx - s, cy - s, cx + s, cy + s], outline=INK, width=3)
    d.ellipse([cx - s + 15, cy - s + 15, cx + s - 15, cy + s - 15], outline=INK_SOFT, width=1)
    for dx, dy, fill in ((0, -1, INK), (0, 1, INK_SOFT), (1, 0, None), (-1, 0, None)):
        tip = (cx + dx * s, cy + dy * s)
        lx = cx + dx * (s - 30) - dy * 16
        ly = cy + dy * (s - 30) + dx * 16
        rx = cx + dx * (s - 30) + dy * 16
        ry = cy + dy * (s - 30) - dx * 16
        base = (cx + dx * (s - 52), cy + dy * (s - 52))
        poly = [tip, (lx, ly), base, (rx, ry)]
        if fill:
            d.polygon(poly, fill=fill, outline=INK, width=1)
        else:
            d.polygon(poly, outline=INK, width=2)
    for ang in (math.pi / 4, 3 * math.pi / 4, 5 * math.pi / 4, 7 * math.pi / 4):
        tip = (cx + math.cos(ang) * s * 0.72, cy + math.sin(ang) * s * 0.72)
        bx = (cx + math.cos(ang) * s * 0.34, cy + math.sin(ang) * s * 0.34)
        px, py = -math.sin(ang) * 13, math.cos(ang) * 13
        d.polygon([tip, (tip[0] + px, tip[1] + py), bx, (tip[0] - px, tip[1] - py)],
                  outline=INK_SOFT, width=1)


def icon_islet(d, x, y):
    d.ellipse([x - 30, y - 12, x + 30, y + 12], fill=ISLAND, outline=INK, width=2)
    d.line([(x, y + 10), (x - 4, y - 16)], fill=INK, width=3)
    for a in (-40, -15, 10, 35, 60):
        ex = x - 4 + 14 * math.cos(math.radians(a))
        ey = y - 16 + 14 * math.sin(math.radians(a))
        d.line([(x - 4, y - 16), (ex, ey)], fill=INK, width=2)


# ================= places =================
PLACES = [
    ("Skull Rock",           (315, 365), (315, 408), icon_skull,     30),
    ("Mount Grumble",        (525, 340), (525, 306), icon_mountain,  30),
    ("Widow's Peak",         (765, 350), (765, 394), icon_widow,     30),
    ("Whispering Woods",     (400, 462), (400, 512), icon_woods,     28),
    ("Dead Man's Cove",      (300, 628), (300, 664), icon_wreck,     28),
    ("Soggy Bottom Marsh",   (430, 688), (430, 726), icon_marsh,     28),
    ("Portly Parrot Bay",    (815, 505), (690, 560), None,           26),
    ("The Gilded Lagoon",    (688, 712), (676, 742), icon_lagoon,    26),
    ("The Jolly Anchor Inn", (560, 628), (690, 640), icon_inn,       26),
    ("X Marks the Spot",     (560, 762), (560, 800), None,           28),
    ("Kraken's Deep",        (895, 400), (880, 505), icon_kraken,    26),
]


def build():
    # ---- parchment base + texture ----
    img = Image.new("RGB", (W, H), PARCH)
    noise = Image.effect_noise((W, H), 64).convert("L")
    img = Image.blend(img, Image.merge("RGB", (noise, noise, noise)), 0.09)

    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    for _ in range(24):  # old stains
        x, y = random.randint(0, W), random.randint(0, H)
        r = random.randint(26, 120)
        od.ellipse([x - r, y - r, x + r, y + r], fill=(170, 133, 84, random.randint(16, 44)))
    for i in range(12):  # vignette
        t = i / 12.0
        inset = int(14 + 52 * t)
        od.rectangle([inset, inset, W - inset, H - inset],
                     outline=(138, 106, 64, int(30 * t)), width=2)
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    d = ImageDraw.Draw(img)

    # ---- island ----
    pts = coast()
    d.polygon(pts, fill=ISLAND)
    d.line(pts + [pts[0]], fill=INK, width=6, joint="curve")
    shrink = [(CX + (p[0] - CX) * 0.988, CY + (p[1] - CY) * 0.988) for p in pts]
    d.line(shrink + [shrink[0]], fill=INK_SOFT, width=2, joint="curve")
    for i in range(0, len(pts), 6):
        a = pts[i]
        b = pts[(i + 2) % len(pts)]
        mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
        tx, ty = b[0] - a[0], b[1] - a[1]
        L = math.hypot(tx, ty) or 1
        nx, ny = -ty / L, tx / L
        out = 1 if in_sea(mx + nx * 8, my + ny * 8) else -1
        d.line([(mx + nx * 4 * out, my + ny * 4 * out),
                (mx + nx * 13 * out, my + ny * 13 * out)], fill=INK_SOFT, width=1)

    # ---- land texture + sea ----
    stipple = 0
    while stipple < 420:
        x = random.uniform(CX - R, CX + R)
        y = random.uniform(CY - R, CY + R)
        dx, dy = x - CX, y - CY
        if math.hypot(dx, dy) < coast_r(math.atan2(dy, dx)) - 8:
            d.ellipse([x, y, x + 1.6, y + 1.6], fill=(150, 112, 70))
            stipple += 1
    for _ in range(150):  # little waves
        ang = random.uniform(0, 2 * math.pi)
        rr = random.uniform(R + 40, 505)
        x, y = CX + rr * math.cos(ang), CY + rr * math.sin(ang)
        if not in_sea(x, y, 10):
            continue
        s = random.randint(5, 10)
        d.arc([x - s, y - s // 2, x + s, y + s // 2], 210, 330, fill=INK_PALE, width=1)

    # ---- rivers + bridge ----
    river_w = [(535, 392), (540, 436), (545, 472), (528, 508), (518, 548),
               (514, 602), (506, 660), (500, 718), (498, 776), (504, 824)]
    river_e = [(738, 384), (728, 438), (716, 496), (708, 556), (702, 618), (700, 680)]

    def draw_river(rp):
        d.line(rp, fill=INK_SOFT, width=7, joint="curve")
        d.line(rp, fill=PARCH, width=3, joint="curve")
        d.line(rp, fill=INK, width=1, joint="curve")

    draw_river(river_w)
    draw_river(river_e)
    d.rectangle([505, 505, 549, 519], fill=(206, 181, 128), outline=INK, width=2)  # deck
    d.line([(505, 506), (549, 518)], fill=INK, width=1)
    d.line([(508, 500), (508, 518)], fill=INK, width=3)  # posts
    d.line([(546, 500), (546, 518)], fill=INK, width=3)

    # ---- dotted trails ----
    dotted_path(d, [(315, 395), (330, 440), (360, 462), (390, 470)])
    dotted_path(d, [(305, 645), (350, 665), (420, 690), (470, 668), (520, 646)])
    dotted_path(d, [(765, 390), (740, 455), (720, 535), (700, 615), (694, 680)])

    # ---- red route: bay -> woods -> mountain -> bridge -> X ----
    route = [(770, 545), (700, 528), (620, 508), (556, 498), (500, 478), (452, 462),
             (412, 452), (432, 420), (468, 398), (512, 372), (540, 384), (556, 420),
             (560, 454), (550, 486), (532, 510), (530, 512), (516, 560), (520, 610),
             (540, 660), (556, 705), (560, 742)]
    dashed_polyline(d, route, 5, RED, dash=17, gap=14)
    d.ellipse([route[0][0] - 6, route[0][1] - 6, route[0][0] + 6, route[0][1] + 6],
              outline=RED, width=3)
    d.ellipse([route[-1][0] - 6, route[-1][1] - 6, route[-1][0] + 6, route[-1][1] + 6],
              outline=RED, width=3)

    # ---- X marks the spot ----
    d.line([(525, 735), (595, 789)], fill=RED, width=10)
    d.line([(595, 735), (525, 789)], fill=RED, width=10)
    for a in range(0, 360, 12):
        d.arc([510, 712, 610, 812], a, a + 7, fill=RED, width=3)

    # ---- place icons + labels ----
    for name, ipos, lpos, icon, size in PLACES:
        if icon is not None:
            icon(d, *ipos)
    for name, ipos, lpos, icon, size in PLACES:
        halo_label(d, lpos[0], lpos[1], name, serif(size))

    # ---- the jokes (charm) ----
    # pier + parrot + caption
    d.line([(774, 526), (800, 512)], fill=INK, width=3)
    d.line([(778, 522), (782, 518)], fill=INK_SOFT, width=2)
    d.line([(786, 517), (790, 513)], fill=INK_SOFT, width=2)
    icon_parrot(d, 800, 500)
    halo_label(d, 745, 440, "The parrot knows", hand(16))
    halo_label(d, 745, 459, "the way (he won't tell)", hand(16))
    # ye are here
    halo_label(d, 812, 592, "Ye are here", hand(17))
    d.line([(800, 582), (788, 552)], fill=INK_SOFT, width=2)
    d.polygon([(788, 552), (779, 557), (785, 564)], fill=INK_SOFT)
    # ship
    icon_ship(d, 905, 640)
    halo_label(d, 905, 672, "The Gilded Gull", hand(19))
    # serpent
    icon_serpent(d, 600, 900)
    halo_label(d, 600, 858, "Here be sea monsters —", hand(17))
    halo_label(d, 600, 880, "the serpent is friendly, mostly", hand(17))
    # kraken caption
    halo_label(d, 880, 536, "Do NOT feed the Kraken", hand(18))
    # dig here
    halo_label(d, 360, 806, "Dig here —", hand(17))
    halo_label(d, 360, 828, "mind the crabs", hand(17))
    # inn sign + leader
    d.line([(600, 640), (655, 641)], fill=INK_SOFT, width=1)
    rot_label(img, "No refunds", 614, 606, hand(17), -7)
    # seagulls patrol
    d.line([(776, 170), (786, 162), (796, 170)], fill=INK_SOFT, width=2)
    d.line([(800, 174), (809, 167), (818, 174)], fill=INK_SOFT, width=2)
    halo_label(d, 845, 176, "beware of aggressive seagulls", hand(15))

    # ---- decoration ----
    icon_islet(d, 185, 778)
    icon_islet(d, 878, 830)
    icon_compass(d, 185, 285)
    halo_label(d, 185, 191, "N", serif(24))

    # scale bar: 1 inch = 96 px at 96 dpi
    bx, by, cell = 96, 884, 24
    for i in range(4):
        d.rectangle([bx + i * cell, by, bx + (i + 1) * cell, by + 10],
                    fill=INK if i % 2 == 0 else CREAM, outline=INK, width=1)
    d.line([(bx, by - 4), (bx, by + 14)], fill=INK, width=2)
    d.line([(bx + 96, by - 4), (bx + 96, by + 14)], fill=INK, width=2)
    halo_label(d, bx + 48, by - 16, "1 inch = 3 leagues", hand(17))
    halo_label(d, bx + 48, by + 30, "(or thereabouts)", hand(15))

    halo_label(d, 512, 196, "The Uncharted Sea", hand(22))
    rot_label(img, "no actual treasure was harmed", 885, 992, hand(14), -4)

    # ---- frame + title banner ----
    d.rectangle([12, 12, W - 12, H - 12], outline=INK, width=4)
    d.rectangle([20, 20, W - 20, H - 20], outline=INK_SOFT, width=1)
    for cx, cy in ((26, 26), (W - 26, 26), (26, H - 26), (W - 26, H - 26)):
        d.ellipse([cx - 4, cy - 4, cx + 4, cy + 4], fill=INK)
    d.polygon([(140, 44), (152, 97), (140, 150), (884, 150), (872, 97), (884, 44)],
              fill=(227, 202, 148), outline=INK, width=3)
    halo_label(d, 512, 84, "Treasure Map of", serif(30))
    halo_label(d, 512, 126, "the Isle of Misplaced Fortune", serif(36))

    # ---- save with size guard ----
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    if buf.tell() > MAX_BYTES:
        q = img.quantize(colors=256, method=Image.Quantize.FASTOCTREE,
                         dither=Image.Dither.FLOYDSTEINBERG).convert("RGB")
        buf = io.BytesIO()
        q.save(buf, format="PNG", optimize=True)
    data = buf.getvalue()
    assert len(data) <= MAX_BYTES, f"PNG too large: {len(data)} bytes"
    with open(OUT, "wb") as fh:
        fh.write(data)
    print(f"wrote {OUT}  {len(data)} bytes  {img.size[0]}x{img.size[1]}px")


if __name__ == "__main__":
    build()