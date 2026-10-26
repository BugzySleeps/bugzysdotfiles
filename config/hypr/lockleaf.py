# Generates lockleaf.png (the hyprlock leaf with its clock hand): run from ~/.config/hypr
from PIL import Image, ImageDraw, ImageFilter, ImageOps, ImageChops

SS = 3                 # supersampling for smooth edges
N = 900                # final leaf canvas size
C = N * SS

def bez(p0, p1, p2, p3, n=60):
    return [((1-t)**3*p0[0] + 3*(1-t)**2*t*p1[0] + 3*(1-t)*t*t*p2[0] + t**3*p3[0],
             (1-t)**3*p0[1] + 3*(1-t)**2*t*p1[1] + 3*(1-t)*t*t*p2[1] + t**3*p3[1]) for t in [i / n for i in range(n + 1)]]

# right half of a heart-shaped leaf, notch at (0,0), tip at (0,-1.05); y grows downward
right = (bez((0, 0), (0.08, 0.13), (0.27, 0.19), (0.44, 0.08)) +
         bez((0.44, 0.08), (0.66, -0.06), (0.64, -0.40), (0.46, -0.63)) +
         bez((0.46, -0.63), (0.31, -0.83), (0.13, -0.94), (0, -1.06)))
left = [(-x, y) for x, y in reversed(right)]
outline = right + left

def squiggle(pts, amp=0.016, waves=34):
    """Push each point along the outline normal by a sine of the distance travelled."""
    import math
    dist = [0.0]
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        dist.append(dist[-1] + math.hypot(x1 - x0, y1 - y0))
    total, out = dist[-1], []
    for i, (x, y) in enumerate(pts):
        (xa, ya), (xb, yb) = pts[max(i - 1, 0)], pts[min(i + 1, len(pts) - 1)]
        tx, ty = xb - xa, yb - ya
        n = math.hypot(tx, ty) or 1
        nx, ny = ty / n, -tx / n
        o = amp * math.sin(2 * math.pi * waves * dist[i] / total)
        out.append((x + nx * o, y + ny * o))
    return out

outline = squiggle(outline)
# midrib path, slightly curved, used only for soft shading (not drawn as a line)
rib = bez((0, 0), (0.05, -0.3), (0.06, -0.7), (0, -1.06))
stem = bez((0, 0.0), (0.02, 0.12), (-0.03, 0.24), (-0.10, 0.34))

scale, ox, oy = C * 0.62, C * 0.5, C * 0.66
P = lambda pts: [(ox + x * scale, oy + y * scale) for x, y in pts]

shape = Image.new('L', (C, C), 0)
d = ImageDraw.Draw(shape)
d.polygon(P(outline), fill=255)
for i, (x, y) in enumerate(P(stem)):          # tapered stem
    r = (0.028 - 0.016 * i / len(stem)) * scale
    d.ellipse((x - r, y - r, x + r, y + r), fill=255)

# the darker (right) half: everything right of the midrib
half = Image.new('L', (C, C), 0)
ImageDraw.Draw(half).polygon(P(rib + [(1.5, -1.06), (1.5, 0.5), (0, 0.5)]), fill=255)
half = ImageChops.multiply(half, shape).filter(ImageFilter.GaussianBlur(C * 0.012))

# base colour: gradient from the tip (light) to the base (deep)
g = Image.linear_gradient('L').resize((C, C))           # 0 top -> 255 bottom
base = ImageOps.colorize(g, black='#7ee36f', mid='#2fb155', white='#0c6a37')
base = Image.composite(Image.new('RGB', (C, C), '#0a5a30'), base, half.point(lambda v: int(v * 0.42)))

# glossy highlight on the left lobe
R = int(C * 0.9)
hl = ImageOps.invert(Image.radial_gradient('L').resize((R, R)))
hlc = Image.new('L', (C, C), 0); hlc.paste(hl, (int(C * 0.18 - R / 2 + C * 0.17), int(C * 0.40 - R / 2)))
hlc = hlc.point(lambda v: int(max(0, v - 150) * 2.2))
base = Image.composite(Image.new('RGB', (C, C), '#eaffdc'), base, hlc.point(lambda v: int(v * 0.40)))

# deeper tone toward the edges, then a thin light rim
edge = shape.filter(ImageFilter.GaussianBlur(C * 0.03))
inner = ImageChops.subtract(shape, edge).point(lambda v: min(255, v * 2))
base = Image.composite(Image.new('RGB', (C, C), '#053a1d'), base, inner.point(lambda v: int(v * 0.45)))
rim = ImageChops.subtract(shape, shape.filter(ImageFilter.MinFilter(3 * SS + (SS % 2 == 0)))).filter(ImageFilter.GaussianBlur(SS))
base = Image.composite(Image.new('RGB', (C, C), '#c9f8b2'), base, rim.point(lambda v: int(v * 0.55)))

leaf = base.copy(); leaf.putalpha(shape)
leaf = leaf.rotate(-32, resample=Image.BICUBIC)          # tilt like the original
leaf = leaf.resize((N, N), Image.LANCZOS)
leaf = leaf.crop(leaf.getchannel('A').getbbox())

# even padding keeps it centred; soft drop shadow underneath
PAD = 60
out = Image.new('RGBA', (leaf.width + 2 * PAD, leaf.height + 2 * PAD), (0, 0, 0, 0))
sh = Image.new('L', out.size, 0); sh.paste(leaf.getchannel('A'), (PAD, PAD + 16))
sh = sh.filter(ImageFilter.GaussianBlur(22)).point(lambda v: int(v * 0.5))
s = Image.new('RGBA', out.size, (0, 0, 0, 0)); s.putalpha(sh)
out = Image.alpha_composite(out, s); out.alpha_composite(leaf, (PAD, PAD))
# clock decoration, centred on the image (hyprlock centres the time on it too)
DS = 3
deco = Image.new('RGBA', (out.width * DS, out.height * DS), (0, 0, 0, 0))
dd = ImageDraw.Draw(deco)
cx, cy = deco.width / 2, deco.height / 2
import math
ang, half, th = math.radians(10), 0.27 * out.width * DS, 0.034 * out.width * DS
dx, dy = math.cos(ang) * half, math.sin(ang) * half
dd.line([(cx - dx, cy - dy), (cx + dx, cy + dy)], fill=(234, 255, 220, 85), width=int(th))   # the hand
for ex, ey in ((cx - dx, cy - dy), (cx + dx, cy + dy)):                                     # round ends
    dd.ellipse((ex - th / 2, ey - th / 2, ex + th / 2, ey + th / 2), fill=(234, 255, 220, 85))
r = th * 0.62
dd.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(234, 255, 220, 235))                     # pivot
ux, uy, ur = cx + 0.17 * out.width * DS, cy - 0.17 * out.width * DS, th * 0.55
dd.ellipse((ux - ur, uy - ur, ux + ur, uy + ur), fill=(234, 255, 220, 200))                 # corner dot
out.alpha_composite(deco.resize(out.size, Image.LANCZOS))
out.save('lockleaf.png'); print(out.size)
