# Generates the hyprlock password-dot shapes in dots/ (run from ~/.config/hypr).
# The patched hyprlock picks one per typed character: dots_text_format = img:...
# `rice` reruns it on every theme switch with LOCK_DOT set to the theme's text colour.
import math
import os
from PIL import Image, ImageDraw, ImageFilter

N, SS = 96, 8            # final size, supersampling
C = N * SS
COLOR = tuple(int(os.environ.get('LOCK_DOT', '#f1effa').lstrip('#')[i:i + 2], 16) for i in (0, 2, 4))

def finish(mask, name, soften=0.07):
    # round every corner: blur then threshold, then anti-alias down
    r = C * soften
    m = mask.filter(ImageFilter.GaussianBlur(r)).point(lambda v: 255 if v > 128 else 0)
    m = m.resize((N, N), Image.LANCZOS)
    im = Image.new('RGBA', (N, N), COLOR + (0,)); im.putalpha(m)
    im.save(f'dots/{name}.png')

def poly(pts):
    m = Image.new('L', (C, C), 0); ImageDraw.Draw(m).polygon([(x * C, y * C) for x, y in pts], fill=255); return m

finish(poly([(0.5, 0.06), (0.94, 0.5), (0.5, 0.94), (0.06, 0.5)]), 'diamond')
finish(poly([(0.5, 0.1), (0.95, 0.88), (0.05, 0.88)]), 'triangle', 0.08)
finish(poly([(0.12, 0.12), (0.88, 0.12), (0.88, 0.88), (0.12, 0.88)]), 'square', 0.09)

m = Image.new('L', (C, C), 0); d = ImageDraw.Draw(m)          # arch: round top, flat base
d.ellipse((0.14 * C, 0.08 * C, 0.86 * C, 0.80 * C), fill=255); d.rectangle((0.14 * C, 0.44 * C, 0.86 * C, 0.9 * C), fill=255)
finish(m, 'arch', 0.05)

m = Image.new('L', (C, C), 0)                                    # pill
ImageDraw.Draw(m).rounded_rectangle((0.04 * C, 0.28 * C, 0.96 * C, 0.72 * C), radius=0.22 * C, fill=255)
finish(m, 'pill', 0.02)

m = Image.new('L', (C, C), 0)                                    # circle
ImageDraw.Draw(m).ellipse((0.1 * C, 0.1 * C, 0.9 * C, 0.9 * C), fill=255)
finish(m, 'circle', 0.01)

pts = []                                                         # scalloped cookie, like the squiggles
for i in range(720):
    a = 2 * math.pi * i / 720
    r = 0.40 + 0.05 * math.cos(9 * a)
    pts.append((0.5 + r * math.cos(a), 0.5 + r * math.sin(a)))
finish(poly(pts), 'cookie', 0.015)

pts = []                                                         # four-leaf clover
for i in range(720):
    a = 2 * math.pi * i / 720
    r = 0.33 + 0.12 * abs(math.cos(2 * a)) ** 0.6
    pts.append((0.5 + r * math.cos(a + math.pi / 4), 0.5 + r * math.sin(a + math.pi / 4)))
finish(poly(pts), 'clover', 0.02)
