"""spotify: your Spotify, playing anywhere (your phone), as a media player on this computer, so the shell reacts to it
like to cmus: the island, the music panel, album colours (wallpaper, glass, LED strips, the mouse), and play / pause /
skip / seek, which go back to Spotify. Nothing plays here.

  spotify login     once: log in in the browser (needs a Spotify app's Client ID in the state file, see below)
  spotify           run (the spotify.service user unit does this)
  spotify status    what Spotify says is playing

It asks Spotify's Web API what's playing (often while a track plays, rarely when nothing does) and shows it over
MPRIS as "Spotify", which Quickshell (and playerctl) see like any player. While your phone plays, the shell's
visualizers hear it through the microphone instead of this computer's sound (~/.config/rice/cava-run).

State: ~/.local/state/rice/spotify.json (private): {"client_id": "..."} from developer.spotify.com/dashboard (an app
with the redirect URI http://127.0.0.1:8888/callback and the Web API ticked), then the login's tokens."""
import asyncio
import base64
import hashlib
import json
import os
import secrets
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

STATE = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local/state")) / "rice"
CREDS = STATE / "spotify.json"
NOW = STATE / "spotify-now.json"          # for cava-run: is the phone playing (the mic stands in for the sound)
REDIRECT = "http://127.0.0.1:8888/callback"
SCOPES = "user-read-playback-state user-read-currently-playing user-modify-playback-state"
API = "https://api.spotify.com/v1"


def log(*a):
    print(*a, flush=True)


# ── auth ────────────────────────────────────────────────────────────
def load():
    try:
        return json.loads(CREDS.read_text())
    except Exception:
        return {}


def save(d):
    STATE.mkdir(parents=True, exist_ok=True)
    tmp = CREDS.with_suffix(".tmp")
    tmp.touch(mode=0o600)
    tmp.write_text(json.dumps(d, indent=1) + "\n")
    tmp.replace(CREDS)


def post_token(form):
    req = urllib.request.Request("https://accounts.spotify.com/api/token", data=urllib.parse.urlencode(form).encode(),
                                 headers={"Content-Type": "application/x-www-form-urlencoded"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())


def keep(d, tok):
    d["access_token"] = tok["access_token"]
    d["expires_at"] = time.time() + tok.get("expires_in", 3600) - 60
    if tok.get("refresh_token"):                     # Spotify may hand out a new one: the old then stops working
        d["refresh_token"] = tok["refresh_token"]
    save(d)
    return d


def login():
    d = load()
    cid = d.get("client_id") or sys.exit(f"spotify: put your app's client id in {CREDS}: {{\"client_id\": \"...\"}}")
    verifier = secrets.token_urlsafe(64)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    state = secrets.token_urlsafe(16)
    url = "https://accounts.spotify.com/authorize?" + urllib.parse.urlencode({
        "client_id": cid, "response_type": "code", "redirect_uri": REDIRECT, "scope": SCOPES,
        "code_challenge_method": "S256", "code_challenge": challenge, "state": state})
    got = {}

    class Back(BaseHTTPRequestHandler):
        def do_GET(self):
            q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            if not self.path.startswith("/callback"):
                self.send_response(404)
                self.end_headers()
                return
            got.update({k: v[0] for k, v in q.items()})
            ok = "code" in got and got.get("state") == state
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(("<body style='background:#111;color:#eee;font:20px sans-serif;padding:3em'>"
                              + ("Logged in. You can close this tab." if ok else "That didn't work: "
                                 + got.get("error", "no code")) + "</body>").encode())

        def log_message(self, *a):
            pass

    srv = HTTPServer(("127.0.0.1", 8888), Back)
    log("opening the Spotify login in your browser; if it doesn't open, go to:\n" + url)
    webbrowser.open(url)
    while "code" not in got and "error" not in got:
        srv.handle_request()
    srv.server_close()
    if got.get("state") != state or "code" not in got:
        sys.exit("spotify: login failed: " + got.get("error", "state mismatch"))
    keep(d, post_token({"grant_type": "authorization_code", "code": got["code"], "redirect_uri": REDIRECT,
                        "client_id": cid, "code_verifier": verifier}))
    log("logged in; start it with: systemctl --user enable --now spotify")


def token():
    d = load()
    if not d.get("refresh_token"):
        raise SystemExit("spotify: not logged in (run: spotify login)")
    if time.time() >= d.get("expires_at", 0):
        d = keep(d, post_token({"grant_type": "refresh_token", "refresh_token": d["refresh_token"],
                                "client_id": d["client_id"]}))
    return d["access_token"]


class Limited(Exception):
    def __init__(self, wait):
        self.wait = wait


def call(method, path, body=None):
    """the Web API: parsed JSON, or None (204: nothing playing / done)"""
    req = urllib.request.Request(API + path, method=method, data=json.dumps(body).encode() if body is not None else
                                 (b"" if method in ("PUT", "POST") else None),
                                 headers={"Authorization": "Bearer " + token(), "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            data = r.read()
            return json.loads(data) if data.strip() else None
    except urllib.error.HTTPError as e:
        if e.code == 429:
            raise Limited(int(e.headers.get("Retry-After", "30")))
        if e.code == 401:                            # the token went stale early: refresh once and try again
            d = load()
            d["expires_at"] = 0
            save(d)
        raise


# ── MPRIS ───────────────────────────────────────────────────────────
from dbus_fast import Variant  # noqa: E402
from dbus_fast.aio import MessageBus  # noqa: E402
from dbus_fast.service import PropertyAccess, ServiceInterface, dbus_property, method, signal  # noqa: E402

R = PropertyAccess.READ


class Root(ServiceInterface):
    def __init__(self):
        super().__init__("org.mpris.MediaPlayer2")

    @method()
    def Raise(self):
        pass

    @method()
    def Quit(self):
        pass

    @dbus_property(access=R)
    def CanQuit(self) -> "b":
        return False

    @dbus_property(access=R)
    def CanRaise(self) -> "b":
        return False

    @dbus_property(access=R)
    def HasTrackList(self) -> "b":
        return False

    @dbus_property(access=R)
    def Identity(self) -> "s":
        return "Spotify"

    @dbus_property(access=R)
    def DesktopEntry(self) -> "s":
        return "spotify"

    @dbus_property(access=R)
    def SupportedUriSchemes(self) -> "as":
        return []

    @dbus_property(access=R)
    def SupportedMimeTypes(self) -> "as":
        return []


class Player(ServiceInterface):
    def __init__(self, bridge):
        super().__init__("org.mpris.MediaPlayer2.Player")
        self.b = bridge

    def _do(self, verb, path, then=None):
        asyncio.get_running_loop().create_task(self.b.control(verb, path, then))

    @method()
    def PlayPause(self):
        self._do("PUT", "/me/player/pause" if self.b.playing else "/me/player/play")

    @method()
    def Play(self):
        self._do("PUT", "/me/player/play")

    @method()
    def Pause(self):
        self._do("PUT", "/me/player/pause")

    @method()
    def Stop(self):
        self._do("PUT", "/me/player/pause")

    @method()
    def Next(self):
        self._do("POST", "/me/player/next")

    @method()
    def Previous(self):
        self._do("POST", "/me/player/previous")

    @method()
    def Seek(self, offset: "x"):
        self.SetPosition("/", self.b.position_us() + offset)

    @method()
    def SetPosition(self, track: "o", pos: "x"):
        ms = max(0, int(pos / 1000))
        self._do("PUT", f"/me/player/seek?position_ms={ms}", then=lambda: self.b.jumped(ms))

    @method()
    def OpenUri(self, uri: "s"):
        pass

    @signal()
    def Seeked(self) -> "x":
        return self.b.position_us()

    @dbus_property(access=R)
    def PlaybackStatus(self) -> "s":
        return "Playing" if self.b.playing else "Paused" if self.b.track else "Stopped"

    @dbus_property(access=R)
    def Metadata(self) -> "a{sv}":
        t = self.b.track
        if not t:
            return {"mpris:trackid": Variant("o", "/org/mpris/MediaPlayer2/TrackList/NoTrack")}
        return {"mpris:trackid": Variant("o", "/rice/spotify/track/" + "".join(c for c in t["id"] if c.isalnum())),
                "mpris:length": Variant("x", t["length"] * 1000),
                "mpris:artUrl": Variant("s", t["art"]),
                "xesam:title": Variant("s", t["title"]),
                "xesam:artist": Variant("as", t["artists"]),
                "xesam:album": Variant("s", t["album"]),
                "xesam:url": Variant("s", t["url"])}

    @dbus_property(access=R)
    def Position(self) -> "x":
        return self.b.position_us()

    @dbus_property(access=R)
    def Rate(self) -> "d":
        return 1.0

    @dbus_property(access=R)
    def MinimumRate(self) -> "d":
        return 1.0

    @dbus_property(access=R)
    def MaximumRate(self) -> "d":
        return 1.0

    @dbus_property(access=R)
    def Volume(self) -> "d":
        return 1.0

    @dbus_property(access=R)
    def CanGoNext(self) -> "b":
        return bool(self.b.track)

    @dbus_property(access=R)
    def CanGoPrevious(self) -> "b":
        return bool(self.b.track)

    @dbus_property(access=R)
    def CanPlay(self) -> "b":
        return bool(self.b.track)

    @dbus_property(access=R)
    def CanPause(self) -> "b":
        return bool(self.b.track)

    @dbus_property(access=R)
    def CanSeek(self) -> "b":
        return bool(self.b.track)

    @dbus_property(access=R)
    def CanControl(self) -> "b":
        return True


# ── the bridge ──────────────────────────────────────────────────────
def parse(p):
    """Spotify's player state → (playing, track or None, progress ms, device name)"""
    if not p or not p.get("item"):
        return False, None, 0, ""
    it = p["item"]
    if it.get("type") == "episode":
        artists, album, imgs = [it.get("show", {}).get("name", "")], it.get("show", {}).get("name", ""), it.get("images", [])
    else:
        artists = [a["name"] for a in it.get("artists", [])]
        album, imgs = it.get("album", {}).get("name", ""), it.get("album", {}).get("images", [])
    art = max(imgs, key=lambda i: i.get("width") or 0)["url"] if imgs else ""
    track = {"id": it.get("id") or it.get("uri", "local"), "title": it.get("name", ""), "artists": artists,
             "album": album, "art": art, "length": it.get("duration_ms", 0),
             "url": it.get("external_urls", {}).get("spotify", "")}
    return bool(p.get("is_playing")), track, p.get("progress_ms", 0), p.get("device", {}).get("name", "")


class Bridge:
    def __init__(self):
        self.playing, self.track, self.device = False, None, ""
        self.progress, self.at = 0, time.monotonic()     # progress (ms) as of `at`
        self.wake = asyncio.Event()
        self.player = Player(self)

    def position_ms(self):
        p = self.progress + ((time.monotonic() - self.at) * 1000 if self.playing else 0)
        return int(min(p, self.track["length"]) if self.track else 0)

    def position_us(self):
        return self.position_ms() * 1000

    def jumped(self, ms):
        self.progress, self.at = ms, time.monotonic()
        self.player.Seeked()

    async def control(self, verb, path, then=None):
        try:
            await asyncio.to_thread(call, verb, path)
            if then:
                then()
        except Exception as e:
            log("control", path, "failed:", e)
        await asyncio.sleep(0.4)                          # then look again soon, to show what it did
        self.wake.set()

    def apply(self, playing, track, progress, device):
        changed = {}
        expect = self.position_ms()
        if (track or {}).get("id") != (self.track or {}).get("id") or (track or {}).get("art") != (self.track or {}).get("art"):
            changed["Metadata"] = None
            for k in ("CanGoNext", "CanGoPrevious", "CanPlay", "CanPause", "CanSeek"):
                changed[k] = None
            if track:
                log("now:", ", ".join(track["artists"]), "—", track["title"], f"({device})")
        if playing != self.playing or bool(track) != bool(self.track):
            changed["PlaybackStatus"] = None
        jump = track and self.track and track["id"] == self.track["id"] and abs(progress - expect) > 2500
        self.playing, self.track, self.device = playing, track, device
        self.progress, self.at = progress, time.monotonic()
        if changed:
            self.player.emit_properties_changed({k: getattr(self.player, k) for k in changed})
        if jump or "Metadata" in changed:
            self.player.Seeked()
        try:
            NOW.write_text(json.dumps({"playing": playing, "device": device}) + "\n")
        except Exception:
            pass

    async def run(self):
        bus = await MessageBus().connect()
        bus.export("/org/mpris/MediaPlayer2", Root())
        bus.export("/org/mpris/MediaPlayer2", self.player)
        await bus.request_name("org.mpris.MediaPlayer2.spotify_rice")
        log("on the bus as org.mpris.MediaPlayer2.spotify_rice")
        idle = 0
        while True:
            wait = 5
            try:
                p = await asyncio.to_thread(call, "GET", "/me/player?additional_types=episode")
                self.apply(*parse(p))
                if self.playing and self.track:
                    # often while playing (a skip on the phone shows quickly), and right as the track ends
                    left = (self.track["length"] - self.position_ms()) / 1000
                    wait = max(0.8, min(3, left + 0.6))
                    idle = 0
                else:
                    idle += 1                              # nothing on for a while: look less and less often
                    wait = 5 if idle < 60 else 15
            except Limited as e:
                log("rate limited; waiting", e.wait, "s")
                wait = e.wait
            except SystemExit as e:
                log(e)
                wait = 60
            except Exception as e:
                log("couldn't reach Spotify:", e)
                wait = 15
            self.wake.clear()
            try:
                await asyncio.wait_for(self.wake.wait(), wait)
            except asyncio.TimeoutError:
                pass


def status():
    playing, track, progress, device = parse(call("GET", "/me/player?additional_types=episode"))
    if not track:
        print("nothing playing")
    else:
        print(("▶ " if playing else "⏸ ") + ", ".join(track["artists"]), "—", track["title"],
              f"[{progress // 60000}:{progress // 1000 % 60:02d}] on {device}")


if __name__ == "__main__":
    a = sys.argv[1:]
    if a == ["login"]:
        login()
    elif a == ["status"]:
        status()
    elif not a:
        asyncio.run(Bridge().run())
    else:
        sys.exit(__doc__)
