# dotfiles

<p align="center"><img src="config/quickshell/ekitai/assets/logo/logo-wordmark.png" alt="ekitai" width="460"></p>

Hyprland rice with a one-key theme switcher. Every theme recolors Hyprland borders,
waybar, kitty, alacritty, wofi, mako and fastfetch, and swaps the wallpaper.

## Install

One line, on **Arch, Debian/Ubuntu (or anything based on them) or Gentoo**:

```sh
curl -fsSL https://raw.githubusercontent.com/BugzySleeps/bugzysdotfiles/main/install.sh | bash
```

or from a clone: `git clone --recurse-submodules https://github.com/BugzySleeps/bugzysdotfiles ~/dotfiles && ~/dotfiles/install.sh`.

The installer goes through these steps and asks before anything that needs sudo:

1. **Packages.**
   - **Arch:** official repos; wl-screenrec comes from the AUR when paru or yay is installed.
   - **Debian stable:** turns on backports, which is where its Hyprland 0.55+ is.
   - **Gentoo:** turns on the guru and hyproverlay overlays, accepts the testing packages that need
     it, and builds hyprlock with `patches/hyprlock-shape-dots.patch`.
2. **Font.** MesloLGS Nerd Font goes into `~/.local/share/fonts`, unless you already have it.
3. **Links.**
   - `config/*` goes into `~/.config/`, and `scripts/` to `~/scripts`.
   - `bin/*` and `rice` go into `~/.local/bin/`.
   - Anything in the way is moved to `~/.dotfiles-backup/<timestamp>/`; nothing is deleted.
4. **A rice.** It keeps the one you're on, or starts with `leaf`.
5. **[hyprland-pets](https://github.com/BugzySleeps/hyprland-pets)**, the pet in the pull-down tab.
6. **Extras.** Each one is asked separately:
   - start Hyprland when you log in on tty1
   - fastfetch in new kitty windows
   - tty1 autologin, so hyprlock is your login screen (systemd only, off unless you say yes or
     pass `--autologin`)

Run it again any time: it skips what's already done. Options go after `bash -s --` (or after
`./install.sh`): `--yes`, `--no-packages`, `--no-pet`, `--autologin`, `--rice NAME`.

Because the configs are symlinks, edits you make in `~/.config/...` land in this repo.

## Keybinds

| Key | Action |
| --- | --- |
| `SUPER + Escape` | lock the screen (the Quickshell lock on ekitai-qs, hyprlock on the others) |
| `SUPER + I` | settings (look, wallpaper, bar, widgets, lock, sound, notifications, keys) |
| `SUPER + SHIFT + V` | clipboard history |
| `ALT + Tab` | window switcher (live previews; let go of ALT to switch) |
| `SUPER + O` | workspace overview (drag windows between workspaces) |
| `Print` | screenshot a region, into the editor (draw, crop, save / copy) |
| `SUPER + T` | wallpaper picker on ekitai-qs (recolours everything); rice list on the others |
| `SUPER + SHIFT + T` | next rice |
| `SUPER + Tab` | show / hide the bar (waybar, or the Quickshell bar) |
| `SUPER + N` | control centre (Quickshell rice) |
| `SUPER + W` | edit desktop widgets (Quickshell rice) |
| `SUPER + wheel` / `=` / `-` | scroll the window row / widen / narrow a window |
| `Print` | screenshot a region |
| `SHIFT + Print` | screenshot the whole screen |
| `ALT + Print` | screenshot the focused window |
| `SUPER + Q` / `R` / `E` | kitty / app launcher / dolphin |
| `SUPER + .` | emoji (the launcher's `:` mode) |
| `SUPER + Z` / `X` | previous / next workspace (infinite desktop) |

Screenshots go to `~/Pictures/Screenshots/` and the clipboard.

The record button on the waybar records the screen: left-click for the monitor you're on,
right-click to pick an area, middle-click for the folder. Recordings go to `~/Videos/Recordings/`.

## Rices

`leaf`, `ekitai`, `ekitai-qs`

`ekitai-qs` is `ekitai` with a [Quickshell](https://quickshell.org) shell (`config/quickshell/ekitai`, its own
repo, [liquid](https://github.com/BugzySleeps/liquid), as a submodule)
in place of waybar, mako and wofi:

- **bar:** one slim borderless strip (or three islands, in settings), mostly icons: hover one to slide out its
  detail (the wifi name, the volume). Workspace dots stretch into a pill for the active one; the clock is the hour
  big, with the minutes and seconds stacked beside it. 液 opens the launcher; workspaces; clock (calendar); the playing
  track with live cava bars (media panel); cpu / memory meters, wifi, volume, a screen recorder
  (click: this monitor, right-click: an area, middle-click: the folder; a red dot and the time while
  recording), notifications and the control centre.
- **control centre** (`SUPER + N`): wifi, sound, mic and do-not-disturb toggles, volume and
  brightness sliders, cpu / ram / disk, notification history, lock / sleep / log out / reboot /
  power off (click twice).
- **music panel** (click the song in the bar): the cover blurred and tinted through the whole panel, the art
  (a slowly turning cookie in squiggle), a waterline visualizer whose bars stand in the liquid with their
  reflections rippling underneath, synced lyrics scrolling past with the current line big in the middle, a
  seek bar, controls, where the sound is going, and lyrics / library / art / eq / shuffle / repeat.
  **library** swaps the lyrics for cmus's library (searchable; click plays a song, right-click queues it) and its
  queue. **art** gives the shell and the window borders the album cover's colours, track by track
  (also in settings → look; `rice accent <image>|off` by hand).
  **eq** swaps the lyrics for a 10-band equaliser (31 Hz – 16 kHz, ±12 dB): presets (flat, bass, treble, vocal,
  pop, rock, jazz, classical), knobs you drag (scroll, double-click to flatten) joined by a curve, and an on/off
  switch. It works on everything that's playing, live, without rerouting anything: it sits in each stream's own
  PipeWire converter. Also `~/.config/rice/eq on|off|preset <name>`, and `qs -c ekitai ipc call music eq`.
- **welcome** (first login): the liquid rises and walks you through picking a wallpaper (your colours come from it), a shape (square / round / squiggle, plus glass) and the keys worth knowing. It shows once; see it again with `qs -c ekitai ipc call welcome open`.
- **launcher** (`SUPER + R`): type to search apps. The first character switches mode (or click the chips under the prompt):
  - `=` calculator: Enter copies the result.
  - `:` emoji (`:smile`, `:fire`, `:+1`): Enter types it into your window, Shift+Enter just copies. `SUPER + .` opens straight into it. The emoji names come from [gemoji](https://github.com/github/gemoji) (MIT).
  - `/` files in your home folder: Enter opens, Shift+Enter shows it in the file manager. Uses `fd` if installed, else `find`.
  - `!` web search: `!g` google, `!d` duckduckgo, `!y` youtube, `!w` wikipedia, `!gh` github, `!r` reddit, `!aw` arch wiki, `!gw` gentoo wiki, `!gp` gentoo packages. No bang searches DuckDuckGo.
  - `#` colours: pick one off the screen (uses `hyprpicker` if installed, else `slurp` + `grim`), recent picks, and the theme palette. Type a hex for rgb/hsl. Enter copies.
  - `>` run a command: Enter runs it, Shift+Enter in a terminal, with history and completion from your `$PATH`.
- **wallpaper picker** (`SUPER + T`, or right-click the desktop → change wallpaper): the default wallpaper plus every
  image in `~/Pictures/wallpapers`, as a fan of slanted cards; the selected one's name and palette show beneath. Picking one recolours the whole
  rice from it (bar, panels, borders, terminal, lock screen): your one-colour palette, turned to the image's main
  hue, or greys for a colourless image. The shell never reloads for it: the new wallpaper wipes up from the bottom
  while the colours crossfade. `←/→` or scroll, `Enter` to apply. Also `rice wall <image>` / `rice wall default`.
- **shape** (control center, or right-click the desktop): `square` (the default), `round` or `squiggle`, for
  everything at once.
  Round gives rounded boxes, pills, circle buttons and dot meters. Squiggle gives wavy-edged boxes, scalloped
  cookie buttons, workspace dots and album art (the art slowly turns while music plays), and wavy meters. Windows
  get rounded corners too. Saved in `~/.local/state/ekitai/look.json`; `qs -c ekitai ipc call look set round`.
- **glass** (control center, or right-click the desktop): liquid glass on top of any shape. The bar, panels, widgets
  and popups go see-through with a frosted blur behind them and a sheen of light across the top; see-through
  windows (the terminal) get frosted too. `qs -c ekitai ipc call look glass on|off|toggle`.
- **lock screen** (`SUPER + Escape`, the control center, and at login). ekitai means 液体, "liquid": glowing
  liquid rises from the bottom over your blurred wallpaper (a GPU shader, `shaders/liquid.frag`), bending the
  picture under its rolling surface, with bubbles and a bright waterline. The login box floats on the surface and
  rides the waves; every key drops a ripple, a wrong password splashes, and unlocking drains it all away. Passwords
  go through PAM (`login`), like hyprlock. If the shell crashes while locked, the session stays locked and the
  restarted shell locks again; if it can't lock at all, `rice lock` falls back to hyprlock.
  `qs -c ekitai ipc call lock preview` shows it without locking. If music's playing, it goes **underwater** while
  locked: a low-pass glides in as the liquid rises and back out as it drains (settings → lock screen; `rice/eq muffle`).
  It has its own **widgets** (the same ones as the desktop; the lyrics one sits under the clock): right-click the desktop → *edit lock screen*, or
  `qs -c ekitai ipc call lock edit`, to arrange them in the preview. Each one can **float on the liquid**, riding
  and tilting with the waves wherever you drag it, or stay fixed. It starts with music and the visualizer
  floating. Editing only works in the preview, never on the real lock.
- **logo:** a drop falling into rings of ripples. The shell draws it itself (`components/Logo.qml`), in the theme's
  colours: the bar's launcher tile (it drips when you hover), the control centre, settings, the wallpaper picker, the
  fetch widget (a drop every so often), the welcome screen, and the lock intro, where the drop lands with a plop just
  as the liquid starts to rise. Under 64 px it switches to a plainer version (two solid rings, a bigger drop). The
  files (SVG and PNG: the mark, a small one, one glowing on black, the wordmark) are in
  `config/quickshell/ekitai/assets/logo/`, made by the `make.py` there.
- **type:** Departure Mono, a pixel font, for all the text (sizes snap to its 11px grid so it stays crisp), with
  Symbols Nerd Font for icons. Both ship in `fonts/` and `install.sh` links them in.
- **dynamic island:** the middle of the bar (clock, song, cmus) swells down out of the bar like a drop stretching
  (spring physics) when something happens, then shrinks back: the volume / brightness level (liquid filling
  across it, sloshing as it moves), a new track with its
  cover, or a notification. Simple notifications show there instead of as a popup; ones with buttons, or urgent
  ones, still pop up. Pick what it shows in settings → bar (the old side vial is still there for volume).
  `qs -c ekitai ipc call island preview level|track|notify` to see each.
- **privacy while sharing:** the weather widget hides where you are while the screen is shared (a screencast:
  Discord, OBS, a browser) or recorded with the bar's recorder. Per widget: show · hide when sharing (the default) ·
  hide, in its settings.
- **settings** (`SUPER + I`, the control centre, or right-click the desktop): shape and glass, a wallpaper grid,
  what the bar shows, widget and lock-screen editing, volume and the EQ, do-not-disturb, and an about page with
  every key. Its own options live in `~/.local/state/ekitai/settings.json`.
- **clipboard history** (`SUPER + SHIFT + V`): everything you copy, text and images (with previews), searchable;
  Enter copies it back, Delete forgets it. Kept in memory only (`$XDG_RUNTIME_DIR`), so it's gone on reboot, and
  anything a password manager marks as a password is never kept.
- **window switcher** (`ALT + Tab`): your windows, most recent first, as a carousel of live previews.
- **workspace overview** (`SUPER + O`, or right-click the workspace dots): liquid floods up from the bottom like the lock screen, with every workspace floating on it as a tile of live window previews. Each workspace holds its own pool, deeper the more windows it has. Drag a window (it lifts off as a glowing droplet) onto another workspace to move it there: that pool rises to meet it and splashes when it lands. Click a window to focus it.
- **screenshot editor** (`Print`): drag out a region, then draw on it (pen, arrow, box), crop it, and save
  and/or copy it at full resolution. `SHIFT + Print` / `ALT + Print` still save straight away.
- **notes**: the control centre has a scratchpad; note widgets set to *scratchpad* show the same text.
  `qs -c ekitai ipc call widgets note "…"` adds a line from anywhere.
- **performance mode** (settings → look): while a window is fullscreen or on battery (or always / never), cava,
  the visualizers and the glass blur pause.
- **little sounds** (settings → sound, off by default): bubbles when unlocking, a click for screenshots, a tick for
  volume. Made from scratch by `sounds/make.py`.
- **notification sounds** (settings → sound, on by default): a sound whenever a notification arrives, in the island
  or as a popup (never in do-not-disturb). Any terminal style's opening sound (**ps2** by default, or **mine**) or a water drip.
- **terminal sounds** (settings → sound, on by default): a sound as a terminal opens and another as it closes, in
  five styles you can try from settings: **mine** (the default: my own clips, `sounds/term-mine-{open,close}.wav`,
  converted from mp3s), then four made by `sounds/make.py`: **ps2** (the cold console menu: a reverse swell into a
  deep boom and glass, sliding down into a "thoom" as it closes), **hud** (an FM zap and robotic beeps), **crt** (an
  old monitor powering on / the zwip as it shuts off) and **glitch** (a gated, stuttering digital buzz). To swap in
  other clips: `ffmpeg -i in.mp3 -af silenceremove=start_periods=1:start_threshold=-50dB -ar 48000 term-mine-open.wav`.
- **lock screen sounds** (settings → sound, on by default): the liquid sounds like water as it moves, each sound
  timed to its animation: a pour that thins out as it settles when locking, a surge, a muffled moment under water
  and a drain for the login intro, a drop for every key (a smaller plip deleting), a splash for a wrong password, and
  a gurgling drain that speeds up into a last slurp as it unlocks. Made by `sounds/make.py` (`lock-*.wav`).
- **login intro:** the first lock of a session opens with the logo glowing on the black, its drop falling just as the
  liquid rises over it, filling the
  screen, then draining to rest as the clock comes in (`qs -c ekitai ipc call lock previewIntro` to see it).
- **liquid touches:** the volume / brightness indicator is a vial at the right edge that fills to the level and
  sloshes when it changes;
  notifications drip in: a droplet falls, splats with a ripple, and spreads into the box.
- **desktop widgets:** clock (digital or analog), calendar, weather (open-meteo, by city), fetch,
  now playing, synced lyrics (lrclib), visualizer, notes, images, and a **claude** widget (Claude Code's token
  usage: the current 5-hour window and when it resets, today's total in / out / cache, the last 12 hours; read from
  `~/.claude/projects` by `rice/claude-usage`). Right-click the desktop to add
  one; `SUPER + W` to edit: drag to move (snaps to a grid), corner to resize, and per widget choose
  which workspaces it shows on (all, or any set), box or bare, and its own options. The layout is
  saved to `~/.local/state/ekitai/widgets.json`.

Any rice can do this: `quickshell = "<config>"` in its `theme.toml` runs `~/.config/quickshell/<config>`
instead of waybar + mako, and `rice` starts and stops it. Talk to it with
`config/rice/qs-ipc <target> <function>` (targets are listed in `services/Ui.qml`).

```sh
rice              # pick with wofi
rice <name>       # switch
rice next|prev    # cycle
rice list         # list (* = current)
rice reload       # re-render after editing a template
```

### How it works

```
config/rice/
├── rice                  the switcher (Python 3.11+)
├── themes/<name>/
│   ├── theme.toml        palette, wallpaper, border gradient, fastfetch style
│   ├── logo.txt          fastfetch logo ($1 / $2 = logo colours)
│   └── wallpaper.*
└── templates/            mirrors ~/.config; {{colors.accent}}-style placeholders
```

`rice <name>` renders every file in `templates/` into `~/.config/` with that theme's
values, then reloads Hyprland, waybar, kitty and mako and sets the wallpaper. The rendered
files are gitignored, so edit the template, not the output:

| Edit this | Not this |
| --- | --- |
| `config/rice/templates/waybar/config.jsonc` | `config/waybar/config.jsonc` |
| `config/rice/templates/waybar/colors.css` | `config/waybar/colors.css` |
| `config/rice/templates/hypr/rice.lua` | `config/hypr/rice.lua` |
| `config/rice/templates/kitty/rice.conf` | `config/kitty/rice.conf` |
| `config/rice/templates/alacritty/rice.toml` | `config/alacritty/rice.toml` |
| `config/rice/templates/wofi/style.css` | `config/wofi/style.css` |
| `config/rice/templates/mako/config` | `config/mako/config` |
| `config/rice/templates/fastfetch/config.jsonc` | `config/fastfetch/config.jsonc` |

Everything else (`hyprland.lua`, `waybar/style.css`, `kitty.conf`, …) is a normal
config file.

**New rice:** copy a folder in `config/rice/themes/`, change the colours and wallpaper,
run `rice <newname>`.

A theme can use `wallpaper_cmd = "..."` instead of `wallpaper = "..."` to run a live
wallpaper program; hyprpaper is stopped while it runs.

## Dependencies

The installer handles these. If you're installing them yourself:

- **Hyprland 0.55+** (this config uses the Lua config format), hyprpaper, hyprlock, hyprpolkitagent,
  xdg-desktop-portal-hyprland
- waybar, kitty, alacritty, wofi, mako, fastfetch, cava, fish
- Python 3.11+, python-evdev (infinite desktop scripts), Pillow (lock screen art)
- grim, slurp, wl-clipboard (screenshots), libnotify, playerctl, brightnessctl, wireplumber,
  libpulse (`pactl`), jq, NetworkManager, dolphin, gnome-keyring
- wl-screenrec (the waybar record button),
  cmus (now-playing), libratbag + piper (mouse LED follows the rice)
- MesloLGS Nerd Font
- Optional: hyprlock built with `patches/hyprlock-shape-dots.patch` for random-shape password
  dots; without it the lock screen uses plain dots

## Machine-specific bits

- The `genesis` rice plays `~/Videos/wallpapers-video/genesis-lite.mp4`, which isn't in the
  repo (too big). Put a video there, or change `wallpaper_cmd` in its `theme.toml`.
- The `weed` rice runs Steam Workshop wallpaper `2104261237` on monitor `eDP-1`. You need
  Wallpaper Engine on Steam with that item downloaded, and you may need to change
  `--screen-root` in `config/rice/themes/weed/theme.toml` to your monitor
  (`hyprctl monitors`).
- `config/hypr/hyprland.lua` uses `monitor = preferred, auto`. Add rules there for a
  specific setup.
- `system/getty-tty1-autologin.conf` is the autologin drop-in; the installer fills in your
  username.
