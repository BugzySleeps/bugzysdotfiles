# dotfiles

Hyprland rice with a one-key theme switcher. Every theme recolors Hyprland borders,
waybar, kitty, alacritty, wofi, mako and fastfetch, and swaps the wallpaper.

## Install

One line, on **Arch, Debian/Ubuntu (or anything based on them) or Gentoo**:

```sh
curl -fsSL https://raw.githubusercontent.com/BugzySleeps/bugzysdotfiles/main/install.sh | bash
```

or from a clone: `git clone https://github.com/BugzySleeps/bugzysdotfiles ~/dotfiles && ~/dotfiles/install.sh`.

The installer goes through these steps and asks before anything that needs sudo:

1. **Packages.**
   - **Arch:** official repos; mpvpaper and wl-screenrec come from the AUR when paru or yay is installed.
   - **Debian stable:** turns on backports, which is where its Hyprland 0.55+ is.
   - **Gentoo:** turns on the guru and hyproverlay overlays, accepts the testing packages that need
     it, and builds hyprlock with `patches/hyprlock-shape-dots.patch`.
2. **Font.** MesloLGS Nerd Font goes into `~/.local/share/fonts`, unless you already have it.
3. **Links.**
   - `config/*` goes into `~/.config/`, and `scripts/` to `~/scripts`.
   - `bin/*` and `rice` go into `~/.local/bin/`.
   - Anything in the way is moved to `~/.dotfiles-backup/<timestamp>/`; nothing is deleted.
4. **A rice.** It keeps the one you're on, or starts with `forest`; pick another with `--rice nord`.
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
| `SUPER + T` | rice picker (wofi) |
| `SUPER + SHIFT + T` | next rice |
| `SUPER + Tab` | show / hide waybar (slides in from the top) |
| `Print` | screenshot a region |
| `SHIFT + Print` | screenshot the whole screen |
| `ALT + Print` | screenshot the focused window |
| `SUPER + Q` / `R` / `E` | kitty / app launcher / dolphin |
| `SUPER + Z` / `X` | previous / next workspace (infinite desktop) |

Screenshots go to `~/Pictures/Screenshots/` and the clipboard.

The record button on the waybar records the screen: left-click for the monitor you're on,
right-click to pick an area, middle-click for the folder. Recordings go to `~/Videos/Recordings/`.

## Rices

`catppuccin`, `chrome`, `dprk`, `drchaz`, `falling`, `forest`, `genesis`, `gentoo`, `grass`,
`gruvbox`, `hoppe`, `larry`, `mary`, `mcveigher`, `minimal`, `minimalistic`, `nord`, `nostalgia`,
`tokyonight`, `weed`

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
- mpv + mpvpaper (the `genesis` live wallpaper), wl-screenrec (the waybar record button),
  cmus (now-playing), libratbag + piper (mouse LED follows the rice)
- MesloLGS Nerd Font
- Optional: `linux-wallpaperengine` + Wallpaper Engine on Steam for the `weed` rice
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
