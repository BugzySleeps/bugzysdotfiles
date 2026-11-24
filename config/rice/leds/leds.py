"""leds: keeps DayBetter LED strips (and the mouse's LEDs) in the desktop's colours.
  · music playing (cmus, or the phone's Spotify): the album cover's colours (album.py). A P065 strip is one colour
    at a time (one zone), so it moves through them with the music: a flash and the next colour on each beat, the
    bass breathing in between. The mouse never follows the album: it keeps the theme's own `mouse` colour.
  · otherwise the shell's colour: liquid's (it writes ~/.local/state/ekitai/leds.json: the wallpaper's or a scene's
    colour, and whether to pulse), or for any other shell the theme's accent (~/.local/state/rice/palette.json).

  leds              run (the leds.service user unit does this)
  leds scan         list the strips in range
  leds set <hex>    one colour now, then exit (the service must be stopped: a strip takes one connection)
  leds fasttest     blinks red/blue: 4 s confirmed (slow), then 4 s unconfirmed (fast) — does the strip keep up?

The strip's address is found by scanning for its name (P065_…) and remembered in ~/.local/state/rice/leds-address;
put one in that file yourself to pick between several. Only one thing can talk to a strip at a time, so while this
runs the DayBetter app can't connect: `systemctl --user stop leds` first."""
import asyncio
import json
import math
import os
import sys
from pathlib import Path

from bleak import BleakScanner

sys.path.insert(0, str(Path(__file__).resolve().parent))
from p065 import Strip  # noqa: E402
from album import Album  # noqa: E402

STATE = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local/state"))
FEED = STATE / "ekitai/leds.json"
PALETTE = STATE / "rice/palette.json"
RICE = Path.home() / ".config/rice"
ADDR = STATE / "rice/leds-address"
NAMES = ("P065_",)

GAMMA = 2.0                        # LEDs are linear and a screen isn't: without this every colour washes out to white
SCALE = (1.0, 0.62, 0.72)          # and their green and blue are brighter than their red


def log(*a):
    print(*a, flush=True)


def led(hexc):
    """a screen colour, as the strip should be told it"""
    rgb = [int(hexc.lstrip("#")[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(round(255 * (c ** GAMMA) * s) for c, s in zip(rgb, SCALE))


async def find():
    if ADDR.is_file() and ADDR.read_text().strip():
        return ADDR.read_text().strip()
    log("scanning for a strip…")
    for d in await BleakScanner.discover(timeout=10):
        if d.name and d.name.startswith(NAMES):
            ADDR.parent.mkdir(parents=True, exist_ok=True)
            ADDR.write_text(d.address + "\n")
            log("found", d.name, d.address)
            return d.address
    return None


def shell():
    """the Quickshell config the current theme runs ("ekitai", "macshell", …)"""
    try:
        name = (RICE / "current").read_text().strip()
        for line in (RICE / "themes" / name / "theme.toml").read_text().splitlines():
            if line.startswith("quickshell"):
                return line.split("=", 1)[1].strip().strip('"')
    except Exception:
        pass
    return ""


def wanted():
    """the shell's colour and wishes: liquid's own feed, else the theme's accent (and pulse with the music)"""
    if shell() == "ekitai":
        try:
            return json.loads(FEED.read_text())
        except Exception:
            pass
    try:
        return {"colour": json.loads(PALETTE.read_text())["colors"]["accent"], "pulse": True}
    except Exception:
        return {}


class Beat:
    """the music's beat, from its own small cava (through cava-run, so it hears whichever output is playing, or the
    mic while the phone plays). Not just loudness: an onset detector on the bass, a jump well above the song's recent
    jumps (mean + 1.3 σ over the last 1.5 s), at most one every 170 ms. .level is the bass now (0–1), .beats counts."""
    FPS = 60
    CONF = "\n".join(["[general]", "bars = 16", f"framerate = {FPS}", "autosens = 1", "[input]", "method = pipewire",
                      "source = auto", "[output]", "method = raw", "raw_target = /dev/stdout", "data_format = ascii",
                      "ascii_max_range = 1000", "[smoothing]", "noise_reduction = 2"]) + "\n"

    def __init__(self):
        self.proc, self.level, self.beats = None, 0.0, 0
        self.prev, self.flux, self.last = [], [], 0.0

    async def want(self, on):
        if on and not self.proc:
            conf = Path(os.environ.get("XDG_RUNTIME_DIR", "/tmp")) / "leds-cava.conf"
            conf.write_text(self.CONF)
            self.proc = await asyncio.create_subprocess_exec(
                str(Path.home() / ".config/rice/cava-run"), str(conf),
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL, start_new_session=True)
            asyncio.create_task(self._read(self.proc))
        elif not on and self.proc:
            try:
                os.killpg(self.proc.pid, 15)               # cava-run and its cava
            except ProcessLookupError:
                pass
            self.proc, self.level = None, 0.0

    async def _read(self, proc):
        loop = asyncio.get_running_loop()
        while proc is self.proc:
            line = await proc.stdout.readline()
            if not line:
                break
            v = [int(x) / 1000 for x in line.decode().split(";") if x.strip()]
            if len(v) < 4:
                continue
            bass = (v[0] * 0.6 + v[1] + v[2] * 0.6) / 2.2  # the kick and the bass
            self.level = bass
            # the jump over the last few frames, against the song's recent jumps
            base = sum(self.prev) / len(self.prev) if self.prev else bass
            jump = max(0.0, bass - base)
            self.prev = (self.prev + [bass])[-3:]
            self.flux = (self.flux + [jump])[-int(self.FPS * 1.5):]
            m = sum(self.flux) / len(self.flux)
            sd = (sum((f - m) ** 2 for f in self.flux) / len(self.flux)) ** 0.5
            now = loop.time()
            if jump > m + 1.3 * sd and jump > 0.035 and bass > 0.15 and now - self.last > 0.17:
                self.last = now
                self.beats += 1


LOW = 0.12                         # how dim the strip gets between beats
FPS = 40


album = Album(log)


async def run():
    strip, back, beat = None, 2, Beat()
    seen, idx = 0, 0
    base = None                    # the colour now, fading toward the wanted one
    env, sent = 0.0, None
    while True:
        try:
            if not (strip and strip.connected):
                addr = await find()
                if not addr:
                    log("no strip found; trying again in", back, "s")
                    await asyncio.sleep(back)
                    back = min(back * 2, 120)
                    continue
                await drop(addr)
                strip = Strip(addr, log)
                await strip.connect()
                await strip.power(True)
                log("connected", addr)
                back, sent = 2, None
                run.strip = strip
            w = wanted()
            playing = album.playing or bool(w.get("playing"))
            pulse = bool(w.get("pulse") and playing)
            if pulse != getattr(run, "pulsing", False):
                log("pulsing with the music" if pulse else "steady")
                run.pulsing = pulse
            await beat.want(pulse)
            # the colours: the album's while music plays, else the shell's one
            cols = album.colours if album.playing and album.colours else ([w["colour"]] if w.get("colour") else [])
            if cols != getattr(run, "cols", None):
                run.cols, idx = cols, 0
                if cols:
                    log("colours", " ".join(cols))
            if cols:
                # a beat: a flash, and on to the album's next colour
                if pulse and beat.beats != seen:
                    seen = beat.beats
                    env = 1.0
                    if len(cols) > 1:
                        idx = (idx + 1) % len(cols)
                target = led(cols[idx % len(cols)])
                if base is None:
                    base = target
                # (in real time, not per update: the strip takes as many as the radio lets through)
                now = asyncio.get_running_loop().time()
                dt = min(0.25, now - getattr(run, "tick", now))
                run.tick = now
                base = tuple(b + (t - b) * (1 - math.exp(-dt / (0.09 if pulse else 0.25))) for b, t in zip(base, target))
                if pulse:
                    # the flash falls away fast (~120 ms); underneath, the light breathes with the bass
                    env *= math.exp(-dt / 0.12)
                    light = max(env, LOW + (1 - LOW) * min(1.0, beat.level * 1.1) * 0.7)
                else:
                    env += (1.0 - env) * (1 - math.exp(-dt / 0.3))
                    light = env
                out = tuple(round(c * light) for c in base)
                if sent is None or max(abs(a - b) for a, b in zip(out, sent)) > 1:
                    await strip.colour(*out, ack=False)    # waits for the write itself: paced by the radio
                    sent = out
                    run.writes = getattr(run, "writes", 0) + 1
                    run.wrote = True
                # every 20 s while pulsing: how it's keeping up (journalctl --user -u leds)
                t = asyncio.get_running_loop().time()
                if pulse and t - getattr(run, "statsAt", 0) > 20:
                    if getattr(run, "statsAt", 0):
                        log(f"sync: {(beat.beats - run.statsBeats) * 3} beats/min, {run.writes / 20:.0f} updates/s")
                    run.statsAt, run.statsBeats, run.writes = t, beat.beats, 0
            # a write takes its own time (the strip confirms each, ~56 ms): only wait when nothing went out
            if not getattr(run, "wrote", False):
                await asyncio.sleep(1 / FPS)
            run.wrote = False
        except Exception as e:                             # out of range, switched off, taken by the phone app…
            log("lost the strip:", e)
            try:
                await strip.close()
            except Exception:
                pass
            strip = None
            await asyncio.sleep(back)
            back = min(back * 2, 120)


async def drop(addr):
    """a connection BlueZ still holds (this was killed without letting go): a connected strip stops advertising, so
    it can't be found again until it's dropped"""
    p = await asyncio.create_subprocess_exec("bluetoothctl", "disconnect", addr, stdout=asyncio.subprocess.DEVNULL,
                                             stderr=asyncio.subprocess.DEVNULL)
    try:
        await asyncio.wait_for(p.wait(), 5)
    except asyncio.TimeoutError:
        p.kill()


def theme_mouse():
    """the current theme's mouse colour (its `mouse`, else its accent), from its theme.toml"""
    import tomllib
    try:
        name = (Path.home() / ".config/rice/current").read_text().strip()
        t = tomllib.loads((Path.home() / ".config/rice/themes" / name / "theme.toml").read_text())
        return t.get("mouse") or t.get("colors", {}).get("accent")
    except Exception:
        return wanted().get("colour")


async def mouse():
    """the mouse's LEDs (ratbag, ../mouse-color): always the theme's own mouse colour, never the album's (the user
    wants the mouse to stay put while music plays). `rice` sets it on a theme switch; this only puts it back if
    something else changed it (and catches a theme switch rice's own call missed). ratbagctl is slow and rewrites the
    mouse's profile, so a colour has to settle for a moment first."""
    done, seen, since = None, None, 0.0
    loop = asyncio.get_running_loop()
    while True:
        c = theme_mouse()
        if c != seen:
            seen, since = c, loop.time()
        if c and c != done and loop.time() - since > 1.5:
            p = await asyncio.create_subprocess_exec(str(Path.home() / ".config/rice/mouse-color"), c,
                                                     stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL)
            await p.wait()
            log("mouse", c)
            done = c
        await asyncio.sleep(2)


async def main():
    """run, letting go of the strip when stopped (so it advertises again for the next start, or the phone app)"""
    import signal
    loop, task = asyncio.get_running_loop(), asyncio.current_task()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, task.cancel)
    try:
        await asyncio.gather(run(), mouse(), album.follow())
    except asyncio.CancelledError:
        pass
    finally:
        s = getattr(run, "strip", None)
        if s:
            try:
                await asyncio.wait_for(s.close(), 4)
            except Exception:
                pass
        log("stopped")


async def scan():
    for d in await BleakScanner.discover(timeout=10):
        if d.name and d.name.startswith(NAMES):
            print(d.address, d.name)


async def once(hexc):
    s = Strip(await find())
    await s.connect()
    await s.power(True)
    await s.colour(*led(hexc))
    await s.close()


async def fasttest():
    from p065 import WRITE, frame
    s = Strip(await find(), log)
    await s.connect()
    await s.power(True)
    loop = asyncio.get_running_loop()
    for label, resp in (("1) confirmed writes (the way it is now)", True), ("2) unconfirmed writes (the fast way)", False)):
        log(label)
        t, n = loop.time(), 0
        while loop.time() - t < 4:
            n += 1
            await s.client.write_gatt_char(WRITE, frame(0x15, 255 if n % 2 else 0, 0, 0 if n % 2 else 255, 0xFF), response=resp)
            if not resp:
                await asyncio.sleep(0.025)
        log(f"   {n / 4:.0f} colour changes a second")
        await asyncio.sleep(1.5)
    await s.close()


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["scan"]:
        asyncio.run(scan())
    elif a[:1] == ["set"] and len(a) == 2:
        asyncio.run(once(a[1]))
    elif a[:1] == ["fasttest"]:
        asyncio.run(fasttest())
    elif not a:
        asyncio.run(main())
    else:
        sys.exit(__doc__)
