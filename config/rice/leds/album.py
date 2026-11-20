"""album: what's playing (cmus, or the phone's Spotify through the rice spotify bridge) and its cover's colours — a
small palette of its most vivid ones, for the LED strip to move through with the music. Shell-independent: it
asks MPRIS itself (playerctl), so it works under liquid, PureShell and MacShell alike."""
import asyncio
import colorsys
import hashlib
import os
import subprocess
import urllib.request
from pathlib import Path

from PIL import Image

PLAYERS = ("cmus", "spotify_rice")           # music only: browsers and videos don't count
CACHE = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "rice/album-art"


def _run(*cmd):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=4).stdout.strip()
    except Exception:
        return ""


def now_playing():
    """(player, status, track key, art url) of the music player worth following: a playing one, else the first"""
    found = []
    for p in _run("playerctl", "-l").split():
        if p.split(".")[0] not in PLAYERS:
            continue
        st = _run("playerctl", "-p", p, "status")
        found.append((p, st))
    if not found:
        return None
    p, st = next((f for f in found if f[1] == "Playing"), found[0])
    meta = _run("playerctl", "-p", p, "metadata", "--format", "{{xesam:artist}}|{{xesam:title}}|{{mpris:artUrl}}")
    artist, _, rest = meta.partition("|")
    title, _, art = rest.partition("|")
    return p, st, artist + "|" + title, art


def cover(player, key, art):
    """a local copy of the cover: downloaded (Spotify), a file:// one, or pulled out of the file cmus plays"""
    CACHE.mkdir(parents=True, exist_ok=True)
    out = CACHE / (hashlib.sha1((player + key + art).encode()).hexdigest()[:16] + ".jpg")
    if out.is_file() and out.stat().st_size:
        return out
    try:
        if art.startswith("file://"):
            return Path(urllib.request.url2pathname(art[7:]))
        if art.startswith("http"):
            with urllib.request.urlopen(art, timeout=6) as r:
                out.write_bytes(r.read())
            return out
        if player.startswith("cmus"):
            f = next((l[5:] for l in _run("cmus-remote", "-Q").splitlines() if l.startswith("file ")), "")
            if f:
                if f.lower().endswith(".flac"):
                    _run("metaflac", f"--export-picture-to={out}", f)
                else:
                    _run("ffmpeg", "-v", "quiet", "-y", "-i", f, "-an", "-c:v", "copy", "-frames:v", "1", "-f", "image2", str(out))
                if out.is_file() and out.stat().st_size:
                    return out
    except Exception:
        pass
    return None


def palette(path, n=4):
    """the cover's most vivid colours, as hex: quantised, scored by how much there is of each and how colourful it
    is, kept apart in hue so they read as different colours on a strip. A grey cover gives one soft colour."""
    try:
        im = Image.open(path).convert("RGB")
    except Exception:
        return []
    im.thumbnail((96, 96))
    q = im.quantize(colors=12, method=Image.Quantize.MEDIANCUT)
    pal = q.getpalette()
    picks = []
    for count, idx in sorted(q.getcolors(), reverse=True):
        r, g, b = pal[idx * 3: idx * 3 + 3]
        h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
        if v < 0.18:
            continue                                   # near black: an LED can't show it
        score = count * (0.15 + s) ** 2 * (0.4 + v)
        picks.append((score, h, s, v))
    picks.sort(reverse=True)
    chosen = []
    for score, h, s, v in picks:
        if s < 0.22 and chosen:
            continue                                   # greys only if there's nothing else
        if all(min(abs(h - c[0]), 1 - abs(h - c[0])) > 0.07 for c in chosen):
            chosen.append((h, s, v))
        if len(chosen) == n:
            break
    out = []
    for h, s, v in chosen:
        # an LED wants it bright and a little richer than the print
        r, g, b = colorsys.hsv_to_rgb(h, min(1, s * 1.15 + 0.05), max(0.75, v))
        out.append("#%02x%02x%02x" % (round(r * 255), round(g * 255), round(b * 255)))
    return out


class Album:
    """follows the music: .playing, .colours (the palette, [] when there's none), .key (the track)"""

    def __init__(self, log=print):
        self.log, self.playing, self.colours, self.key = log, False, [], None

    async def follow(self):
        loop = asyncio.get_running_loop()
        while True:
            np = await loop.run_in_executor(None, now_playing)
            self.playing = bool(np and np[1] == "Playing")
            if np and np[2] != "|" and np[2] != self.key:
                self.key = np[2]
                c = await loop.run_in_executor(None, cover, np[0], np[2], np[3])
                self.colours = await loop.run_in_executor(None, palette, c) if c else []
                self.log("album:", np[2].replace("|", " — "), " ".join(self.colours) or "(no cover)")
            elif not np:
                self.key, self.colours = None, []
            await asyncio.sleep(1.0)
