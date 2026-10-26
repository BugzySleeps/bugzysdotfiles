# Generates lockbox.png, the squiggly password box for hyprlock. Run from ~/.config/hypr.
# `rice` reruns it on every theme switch with LOCK_LINE / LOCK_FILL set to the theme's colours.
import math
import os
from PIL import Image, ImageDraw, ImageFilter

hexrgb = lambda h: tuple(int(h.lstrip('#')[i:i + 2], 16) for i in (0, 2, 4))
LINE = hexrgb(os.environ.get('LOCK_LINE', '#dddaec'))
FILL = hexrgb(os.environ.get('LOCK_FILL', '#2e264a'))

# ---- squiggly pill outline for the password box ----
SS = 4
BW, BH = 360, 66            # final size
w, h = BW * SS, BH * SS
pad = 7 * SS
r = (h - 2 * pad) / 2       # pill radius
L = w - 2 * pad - 2 * r     # straight length
amp, wave = 2.6 * SS, 18 * SS
cx0, cx1, cy = pad + r, w - pad - r, h / 2
per = 2 * L + 2 * math.pi * r
pts = []
n = 900
for i in range(n + 1):
    s = per * i / n
    if s < L:                                   # top edge, left to right
        x, y, nx, ny = cx0 + s, cy - r, 0, -1
    elif s < L + math.pi * r:                   # right cap
        a = -math.pi / 2 + (s - L) / r
        x, y, nx, ny = cx1 + r * math.cos(a), cy + r * math.sin(a), math.cos(a), math.sin(a)
    elif s < 2 * L + math.pi * r:               # bottom edge, right to left
        x, y, nx, ny = cx1 - (s - L - math.pi * r), cy + r, 0, 1
    else:                                       # left cap
        a = math.pi / 2 + (s - 2 * L - math.pi * r) / r
        x, y, nx, ny = cx0 + r * math.cos(a), cy + r * math.sin(a), math.cos(a), math.sin(a)
    o = amp * math.sin(2 * math.pi * s / (per / round(per / wave)))   # whole number of waves
    pts.append((x + nx * o, y + ny * o))

box = Image.new('RGBA', (w, h), (0, 0, 0, 0))
d = ImageDraw.Draw(box)
d.polygon(pts, fill=FILL + (170,))                          # translucent fill
glowl = Image.new('RGBA', (w, h), (0, 0, 0, 0))
ImageDraw.Draw(glowl).line(pts, fill=LINE + (140,), width=6 * SS, joint='curve')
glowl = glowl.filter(ImageFilter.GaussianBlur(4 * SS))
box = Image.alpha_composite(box, glowl)
ImageDraw.Draw(box).line(pts, fill=LINE + (255,), width=int(2.2 * SS), joint='curve')
box.resize((BW, BH), Image.LANCZOS).save('lockbox.png')

