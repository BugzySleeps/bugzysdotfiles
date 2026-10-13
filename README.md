# dotfiles

Hyprland rice with a one-key theme switcher. Every theme recolors Hyprland borders,
waybar, kitty, alacritty, wofi, mako and fastfetch, and swaps the wallpaper.

## Install

```sh
git clone https://github.com/<you>/dotfiles ~/dotfiles
cd ~/dotfiles
./install.sh --packages      # or just ./install.sh if you install deps yourself
```

`install.sh` symlinks everything in `config/` into `~/.config/`, links `scripts/` to
`~/scripts` and `bin/*` plus `rice` into `~/.local/bin/`, then applies the `forest` rice
(`RICE=nord ./install.sh` to pick another). Anything already in the way is moved to
`~/.dotfiles-backup/<timestamp>/`, nothing is deleted.

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

## Rices

`catppuccin`, `dprk`, `drchaz`, `forest`, `gruvbox`, `hoppe`, `mary`, `mcveigher`,
`nord`, `nostalgia`, `tokyonight`, `weed`

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

- **Hyprland 0.55+** (this config uses the Lua config format), hyprpaper, hyprpolkitagent
- waybar, kitty, alacritty, wofi, mako, fastfetch, cava
- Python 3.11+ and python-evdev (infinite desktop scripts)
- grim, slurp, wl-clipboard (screenshots), libnotify, playerctl, brightnessctl,
  wireplumber, NetworkManager, dolphin
- MesloLGS Nerd Font
- Optional: `linux-wallpaperengine` + Wallpaper Engine on Steam for the `weed` rice

## Machine-specific bits

- The `weed` rice runs Steam Workshop wallpaper `2104261237` on monitor `eDP-1`. You need
  Wallpaper Engine on Steam with that item downloaded, and you may need to change
  `--screen-root` in `config/rice/themes/weed/theme.toml` to your monitor
  (`hyprctl monitors`).
- `config/hypr/hyprland.lua` uses `monitor = preferred, auto`. Add rules there for a
  specific setup.
