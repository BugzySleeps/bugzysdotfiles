# Generates locklarry.png (Larry the cow for hyprlock): solid white silhouette with a soft shadow.
# Run from ~/.config/hypr; source is ~/Pictures/larry.png (already cut out)
import os
from PIL import Image, ImageFilter

S = 3
src = Image.open(os.path.expanduser('~/Pictures/larry.png')).convert('RGBA')
alpha = src.getchannel('A').resize((src.width * S, src.height * S), Image.LANCZOS)
# fill the little gaps inside the outline so it reads as one shape
alpha = alpha.filter(ImageFilter.GaussianBlur(2 * S)).point(lambda v: 255 if v > 90 else 0).filter(ImageFilter.GaussianBlur(1.0))
W, H = alpha.size

P = 24 * S
out = Image.new('RGBA', (W + 2 * P, H + 2 * P), (0, 0, 0, 0))
sh = Image.new('L', out.size, 0); sh.paste(alpha, (P, P + 6 * S))
sh = sh.filter(ImageFilter.GaussianBlur(10 * S)).point(lambda v: int(v * 0.45))
shadow = Image.new('RGBA', out.size, (0, 0, 0, 0)); shadow.putalpha(sh)
out = Image.alpha_composite(out, shadow)
white = Image.new('RGBA', out.size, (0, 0, 0, 0))
m = Image.new('L', out.size, 0); m.paste(alpha, (P, P))
white.paste((255, 255, 255, 255), (0, 0), m)
out = Image.alpha_composite(out, white)
out.save('locklarry.png'); print(out.size)
