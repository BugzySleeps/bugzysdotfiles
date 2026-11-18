#!/usr/bin/env python3
"""Makes the still pictures the claude scene is built from (run it again after changing anything here):

  bg.jpg           the backdrop: near-black warming to brown behind the logo, an orange haze top right, grain
  glow.png         a soft orange glow (behind the logo; it swells with the music)
  cookie.png       the 6-cookie shape (as in liquid's widgets), dark glass with a warm outline
  cookie-line.png  the same, outline only
  dot.png          a small soft dot (the sparks)

The still ../../claude.png (the wallpaper itself, for the picker and the palette) is a grab of scene.qml: shot.sh.
"""
import math
import random
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter

HERE = Path(__file__).resolve().parent
W, H = 1920, 1080
LOGO = (0.73, 0.5)                               # where the logo sits (also in scene.qml)


def blob(size, centre, radius, colour, power=1.6, strength=1.0):
    """A colour layer and its mask: a round soft light at `centre` (px), fading out by `radius` (px)."""
    g = Image.radial_gradient("L").resize((int(radius * 2), int(radius * 2)), Image.BICUBIC)   # 0 middle, 255 edge
    g = g.point(lambda v: int(255 * strength * max(0.0, 1 - v / 255) ** power))
    mask = Image.new("L", size, 0)
    mask.paste(g, (int(centre[0] - radius), int(centre[1] - radius)))
    return Image.new("RGB", size, colour), mask


def backdrop():
    # worked out smoothly (floats) at a quarter size, then grown: no rings from 8-bit gradients
    w, h = W // 4, H // 4
    lights = [  # centre (0–1 of the screen), radius (0–1 of the height), colour, falloff power, strength
        ((0.5, 0.55), 1.35, (34, 17, 10), 1.2, 1.0),     # the room warming up
        (LOGO, 0.95, (58, 24, 11), 1.5, 1.0),            # brown behind the logo
        (LOGO, 0.45, (92, 36, 14), 2.2, 0.8),            # hotter close in
        ((1.02, -0.05), 0.9, (110, 40, 16), 2.0, 0.7),   # haze, top right
        ((0.08, 1.05), 0.7, (40, 16, 8), 2.0, 0.6),      # a little, bottom left
    ]
    px = []
    for y in range(h):
        for x in range(w):
            c = [14.0, 8.0, 6.0]
            for (lx, ly), r, col, pw, st in lights:
                d = math.hypot((x / w - lx) * W / H, y / h - ly) / r
                a = st * max(0.0, 1 - d) ** pw
                c = [c[i] + (col[i] - c[i]) * a for i in range(3)]
            # vignette
            vd = math.hypot((x / w - 0.5) / 0.75, (y / h - 0.5) / 0.95)
            v = 0.75 * min(1.0, max(0.0, (vd - 0.43) / 0.57)) ** 1.4
            c = [c[i] + ((4, 2, 1)[i] - c[i]) * v for i in range(3)]
            px.append(tuple(c))
    small = Image.new("RGB", (w, h))
    small.putdata([tuple(round(v) for v in p) for p in px])
    img = small.resize((W, H), Image.BICUBIC).filter(ImageFilter.GaussianBlur(3))
    # grain (the same in every channel, so it's not colour noise); it also hides what banding is left
    n = Image.effect_noise((W, H), 40).point(lambda x: int(128 + (x - 128) * 0.3))
    img = ImageChops.add(img, Image.merge("RGB", (n, n, n)), 1.0, -128)
    img.save(HERE / "bg.jpg", quality=92, subsampling=0)   # (grain: a PNG of it is 4 MB)


def glow():
    s = 512
    g = Image.radial_gradient("L").resize((s, s), Image.BICUBIC)
    a = g.point(lambda v: int(255 * math.exp(-((v / 255) ** 2) * 5.0) * max(0, 1 - v / 255)))
    out = Image.new("RGBA", (s, s), (255, 122, 61, 0))
    out.putalpha(a)
    out.save(HERE / "glow.png", optimize=True)


def cookie_points(s, inset):
    """The 6-cookie (liquid's Shapes.js: r = 1 + 0.075·cos 6θ, from the top), fitted in an s×s box."""
    n = 720
    rs = [1 + 0.075 * math.cos(6 * (i / n * 2 * math.pi - math.pi / 2)) for i in range(n)]
    m = max(rs)
    half = s / 2 - inset
    return [(s / 2 + math.cos(i / n * 2 * math.pi - math.pi / 2) * rs[i] / m * half,
             s / 2 + math.sin(i / n * 2 * math.pi - math.pi / 2) * rs[i] / m * half) for i in range(n)]


def cookie(name, fill):
    s, k = 512, 4                                # drawn 4× big, then shrunk: smooth edges
    big = Image.new("RGBA", (s * k, s * k), (0, 0, 0, 0))
    d = ImageDraw.Draw(big)
    pts = cookie_points(s * k, 8 * k)
    if fill:
        d.polygon(pts, fill=(40, 20, 12, 150))
    d.line(pts + [pts[0]], fill=(232, 140, 98, 170), width=5 * k, joint="curve")
    big.resize((s, s), Image.LANCZOS).save(HERE / name, optimize=True)


def dot():
    s = 64
    g = Image.radial_gradient("L").resize((s, s), Image.BICUBIC)
    out = Image.new("RGBA", (s, s), (255, 190, 150, 0))
    out.putalpha(g.point(lambda v: int(255 * max(0, 1 - v / 255) ** 2.2)))
    out.save(HERE / "dot.png", optimize=True)


if __name__ == "__main__":
    random.seed(7)
    backdrop()
    glow()
    cookie("cookie.png", True)
    cookie("cookie-line.png", False)
    dot()
    print("made", ", ".join(p.name for p in sorted([*HERE.glob("*.png"), *HERE.glob("*.jpg")])))
