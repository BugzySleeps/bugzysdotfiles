"""leds: keeps DayBetter LED strips (and the mouse's LEDs) the wallpaper's colour. The liquid shell writes the colour to
~/.local/state/ekitai/leds.json (services/Leds.qml); this stays connected to the strip and fades to each new one,
and with pulse on (settings → wallpaper → led strips) throbs with the music's bass while a track plays.

  leds              run (the leds.service user unit does this)
  leds scan         list the strips in range
  leds set <hex>    one colour now, then exit (the service must be stopped: a strip takes one connection)

The strip's address is found by scanning for its name (P065_…) and remembered in ~/.local/state/rice/leds-address;
put one in that file yourself to pick between several. Only one thing can talk to a strip at a time, so while this
runs the DayBetter app can't connect: `systemctl --user stop leds` first."""
import asyncio
import json
import os
import sys
from pathlib import Path

from bleak import BleakScanner

sys.path.insert(0, str(Path(__file__).resolve().parent))
from p065 import Strip  # noqa: E402

STATE = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local/state"))
FEED = STATE / "ekitai/leds.json"
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


def wanted():
    try:
        return json.loads(FEED.read_text())
    except Exception:
        return {}


class Beat:
    """the music's bass, 0–1: its own small cava (through cava-run, so it hears whichever output is playing),
    running only while a track plays and the shell asks for pulsing"""
    CONF = "\n".join(["[general]", "bars = 8", "framerate = 50", "[input]", "method = pipewire", "source = auto",
                      "[output]", "method = raw", "raw_target = /dev/stdout", "data_format = ascii",
                      "ascii_max_range = 100", "[smoothing]", "noise_reduction = 20"]) + "\n"

    def __init__(self):
        self.proc, self.level = None, 0.0

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
        while proc is self.proc:
            line = await proc.stdout.readline()
            if not line:
                break
            v = [int(x) / 100 for x in line.decode().split(";") if x.strip()]
            if v:
                self.level = sum(v[:2]) / 2                # the lowest two bars: kick and bass


LOW = 0.18                         # how dim the strip gets between beats
FPS = 30


async def run():
    strip, back, beat = None, 2, Beat()
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
            pulse = bool(w.get("pulse") and w.get("playing"))
            if pulse != getattr(run, "pulsing", False):
                log("pulsing with the music" if pulse else "steady")
                run.pulsing = pulse
            await beat.want(pulse)
            if w.get("colour"):
                target = led(w["colour"])
                if base is None:
                    base = target
                if tuple(round(c) for c in base) != target and w["colour"] != getattr(run, "last", None):
                    log("colour", w["colour"], "→", target)
                run.last = w["colour"]
                base = tuple(b + (t - b) * 0.12 for b, t in zip(base, target))    # ~0.6 s fade
                # the pulse: quick up on a hit, slower down; steady (full) without music
                hit = min(1.0, beat.level ** 1.6 * 1.5) if pulse else 1.0
                env += (hit - env) * (0.75 if hit > env else (0.22 if pulse else 0.1))
                out = tuple(round(c * (LOW + (1 - LOW) * env)) for c in base)
                if sent is None or max(abs(a - b) for a, b in zip(out, sent)) > 1:
                    await strip.colour(*out, ack=False)    # waits for the write itself: paced by the radio
                    sent = out
            await asyncio.sleep(1 / FPS)
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


async def mouse():
    """the mouse's LEDs (ratbag, ../mouse-color) in the same colour: `rice` only sets them on a theme switch, so album
    colours and a scene's picked colour would leave them behind. Once the colour has settled (ratbagctl is slow, and
    writes the mouse's profile), the plain screen colour: the mouse's LED isn't the strip."""
    done, seen, since = None, None, 0.0
    loop = asyncio.get_running_loop()
    while True:
        c = wanted().get("colour")
        if c != seen:
            seen, since = c, loop.time()
        if c and c != done and loop.time() - since > 1.5:
            p = await asyncio.create_subprocess_exec(str(Path.home() / ".config/rice/mouse-color"), c,
                                                     stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL)
            await p.wait()
            log("mouse", c)
            done = c
        await asyncio.sleep(0.5)


async def main():
    """run, letting go of the strip when stopped (so it advertises again for the next start, or the phone app)"""
    import signal
    loop, task = asyncio.get_running_loop(), asyncio.current_task()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, task.cancel)
    try:
        await asyncio.gather(run(), mouse())
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


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["scan"]:
        asyncio.run(scan())
    elif a[:1] == ["set"] and len(a) == 2:
        asyncio.run(once(a[1]))
    elif not a:
        asyncio.run(main())
    else:
        sys.exit(__doc__)
