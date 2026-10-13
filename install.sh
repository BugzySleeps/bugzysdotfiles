#!/usr/bin/env bash
# Symlink these dotfiles into place and apply a rice.
#
#   ./install.sh                 link configs, apply the "forest" rice
#   ./install.sh --packages      also install dependencies (Arch / Fedora / Debian-ish)
#   RICE=nord ./install.sh       pick which rice to apply
#
# Anything already in the way is moved to ~/.dotfiles-backup/<timestamp>/.
set -euo pipefail

DOT=$(cd "$(dirname "$0")" && pwd)
BACKUP=~/.dotfiles-backup/$(date +%Y%m%d-%H%M%S)
RICE=${RICE:-forest}

link() {   # link <source in repo> <target>
    local src=$1 dst=$2
    if [ -L "$dst" ] && [ "$(readlink -f "$dst")" = "$(readlink -f "$src")" ]; then
        return
    fi
    if [ -e "$dst" ] || [ -L "$dst" ]; then
        mkdir -p "$BACKUP"
        mv "$dst" "$BACKUP/"
        echo "  backed up $dst"
    fi
    mkdir -p "$(dirname "$dst")"
    ln -s "$src" "$dst"
    echo "  linked $dst"
}

install_packages() {
    if command -v pacman >/dev/null; then
        sudo pacman -S --needed hyprland hyprpaper hyprpolkitagent waybar kitty alacritty wofi mako \
            fastfetch cava python python-evdev grim slurp wl-clipboard libnotify playerctl \
            brightnessctl wireplumber networkmanager dolphin ttf-meslo-nerd
        echo "Optional (AUR): linux-wallpaperengine-git — needed for the 'weed' rice"
    elif command -v dnf >/dev/null; then
        sudo dnf install hyprland hyprpaper hyprpolkitagent waybar kitty alacritty wofi mako \
            fastfetch cava python3 python3-evdev grim slurp wl-clipboard libnotify playerctl \
            brightnessctl wireplumber NetworkManager dolphin
        echo "Install MesloLGS Nerd Font manually: https://www.nerdfonts.com/font-downloads"
    elif command -v apt >/dev/null; then
        sudo apt install hyprland hyprpaper waybar kitty alacritty wofi mako-notifier fastfetch cava \
            python3 python3-evdev grim slurp wl-clipboard libnotify-bin playerctl brightnessctl \
            wireplumber network-manager dolphin
        echo "Hyprland in apt may be too old for the Lua config (needs 0.55+)."
        echo "Install MesloLGS Nerd Font manually: https://www.nerdfonts.com/font-downloads"
    else
        echo "Unknown package manager — see the dependency list in README.md"
    fi
}

[ "${1:-}" = "--packages" ] && install_packages

echo "Linking configs…"
for dir in "$DOT"/config/*/; do
    name=$(basename "$dir")
    link "$DOT/config/$name" ~/.config/"$name"
done
link "$DOT/scripts" ~/scripts
for f in "$DOT"/bin/*; do
    link "$f" ~/.local/bin/"$(basename "$f")"
done
link "$DOT/config/rice/rice" ~/.local/bin/rice

python3 -c 'import tomllib' 2>/dev/null || { echo "rice needs Python 3.11+"; exit 1; }

echo "Applying rice: $RICE"
~/.config/rice/rice "$RICE"

[ -d "$BACKUP" ] && echo "Old files are in $BACKUP"
echo "Done. Log into Hyprland (or run 'hyprctl reload' if you're already in it)."
