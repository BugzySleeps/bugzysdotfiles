#!/usr/bin/env bash
# bugzysdotfiles installer: Hyprland rice with a one-key theme switcher.
#
#   curl -fsSL https://raw.githubusercontent.com/BugzySleeps/bugzysdotfiles/main/install.sh | bash
#   or, from a clone:  ./install.sh
#
# Works on Arch, Debian/Ubuntu (and anything based on them) and Gentoo. It:
#   1. installs the packages (asks first; uses sudo)
#   2. installs the MesloLGS Nerd Font if you don't have it
#   3. symlinks config/* into ~/.config, scripts/ to ~/scripts, bin/* and rice into ~/.local/bin
#      (anything in the way is moved to ~/.dotfiles-backup/<time>/, nothing is deleted)
#   4. applies a rice (theme)
#   5. installs hyprland-pets, the pet in the pull-down tab
#   6. optional extras: start Hyprland when you log in on tty1, fastfetch in new kitty windows,
#      and tty1 autologin so hyprlock is your login screen
#
# Options:
#   --yes            answer yes to everything (autologin still needs --autologin)
#   --no-packages    don't install packages
#   --no-pet         don't install hyprland-pets
#   --autologin      also set up tty1 autologin + hyprlock greeter (systemd only)
#   --rice NAME      which rice to apply (default: the one you're on, else forest; also RICE=NAME)
set -u

REPO="BugzySleeps/bugzysdotfiles"
CLONE="$HOME/dotfiles"
PETS_URL="https://github.com/BugzySleeps/hyprland-pets/releases/latest/download/install.sh"
MARK="bugzysdotfiles (added by install.sh)"
RICE=${RICE:-}
ARGS=("$@")

yes=0 packages=1 pet=1 autologin=0
while (( $# )); do
    case $1 in
        -y | --yes) yes=1 ;;
        --no-packages) packages=0 ;;
        --packages) ;;   # the old opt-in flag; packages are the default now
        --no-pet) pet=0 ;;
        --autologin) autologin=1 ;;
        --rice) shift; RICE=${1:?--rice needs a name} ;;
        -h | --help) sed -n '2,25p' "$0" 2>/dev/null | sed 's/^# \{0,1\}//'; exit 0 ;;
        *) echo "unknown option: $1 (try --help)"; exit 2 ;;
    esac
    shift
done

bold() { printf '\n\e[1m%s\e[0m\n' "$*"; }
good() { printf '  \e[32m✓\e[0m %s\n' "$*"; }
bad()  { printf '  \e[31m✗\e[0m %s\n' "$*"; }
meh()  { printf '  \e[33m~\e[0m %s\n' "$*"; }
die()  { printf '\e[31merror:\e[0m %s\n' "$*" >&2; exit 1; }

ask() {  # ask "question" [default y|n] -> 0 for yes. Reads the terminal, so it works under curl | bash.
    local def=${2:-y} reply
    (( yes )) && [[ $def == y ]] && return 0
    if ! { exec 9</dev/tty; } 2>/dev/null; then
        echo "  $1 (no terminal to ask on: skipping)"
        return 1
    fi
    if [[ $def == y ]]; then printf '  %s [Y/n] ' "$1"; else printf '  %s [y/N] ' "$1"; fi
    read -r reply <&9
    exec 9<&-
    [[ -z $reply ]] && reply=$def
    [[ $reply == [yY]* ]]
}
tty_run() {  # run a command with the terminal as stdin (sudo/emerge prompts work under curl | bash)
    if [[ -r /dev/tty ]]; then "$@" </dev/tty; else "$@"; fi
}

# ── distro ───────────────────────────────────────────────────────────────────
ids=""
[[ -r /etc/os-release ]] && ids="$(. /etc/os-release; echo " ${ID:-} ${ID_LIKE:-} ")"
case $ids in
    *" arch "*) distro=arch ;;
    *" gentoo "*) distro=gentoo ;;
    *" debian "* | *" ubuntu "*) distro=debian ;;
    *) distro=unknown ;;
esac

ARCH_PKGS=(hyprland hyprpaper hyprlock hyprpolkitagent xdg-desktop-portal-hyprland waybar kitty alacritty wofi
    mako fastfetch cava python python-evdev python-pillow grim slurp wl-clipboard jq libnotify playerctl
    brightnessctl wireplumber libpulse networkmanager dolphin mpv mpvpaper wl-screenrec cmus libratbag piper
    gnome-keyring fish ttf-meslo-nerd git curl)
DEBIAN_PKGS=(hyprland hyprpaper hyprlock hyprpolkitagent xdg-desktop-portal-hyprland waybar kitty alacritty wofi
    mako-notifier fastfetch cava python3 python3-evdev python3-pil grim slurp wl-clipboard jq libnotify-bin
    playerctl brightnessctl wireplumber pulseaudio-utils network-manager dolphin mpv mpvpaper wl-screenrec cmus
    ratbagd piper gnome-keyring fish git curl xz-utils fontconfig)
GENTOO_PKGS=(gui-wm/hyprland gui-apps/hyprpaper gui-apps/hyprlock sys-auth/hyprpolkitagent
    gui-libs/xdg-desktop-portal-hyprland gui-apps/waybar x11-terms/kitty x11-terms/alacritty gui-apps/wofi
    gui-apps/mako app-misc/fastfetch media-sound/cava dev-python/evdev dev-python/pillow gui-apps/grim
    gui-apps/slurp gui-apps/wl-clipboard app-misc/jq x11-libs/libnotify media-sound/playerctl
    app-misc/brightnessctl media-video/wireplumber media-libs/libpulse net-misc/networkmanager kde-apps/dolphin
    media-video/mpv gui-apps/mpvpaper media-video/wl-screenrec media-sound/cmus dev-libs/libratbag app-misc/piper
    gnome-base/gnome-keyring app-shells/fish dev-vcs/git net-misc/curl app-arch/xz-utils media-libs/fontconfig)
# Gentoo: newer than stable, from overlays (hyproverlay: current Hyprland, guru: mpvpaper/wl-screenrec)
GENTOO_KEYWORDS=("*/*::hyproverlay" gui-apps/mpvpaper media-video/wl-screenrec app-misc/brightnessctl
    app-misc/piper dev-libs/libratbag)

available() {  # print the packages this distro's repos actually have
    local p
    for p in "$@"; do
        case $distro in
            arch) pacman -Si "$p" >/dev/null 2>&1 && echo "$p" ;;
            debian) apt-cache policy "$p" 2>/dev/null | grep -q 'Candidate: [^(]' && echo "$p" ;;
            gentoo) [[ -n $(portageq best_visible / "$p" 2>/dev/null) ]] && echo "$p" ;;
        esac
    done
}

gentoo_prepare() {  # overlays, keywords and the hyprlock patch, before emerging
    if ! command -v eselect >/dev/null || ! eselect repository list >/dev/null 2>&1; then
        tty_run sudo emerge --noreplace app-eselect/eselect-repository dev-vcs/git || return 1
    fi
    local repo sync=()
    for repo in guru hyproverlay; do
        if eselect repository list -i 2>/dev/null | grep -qw "$repo"; then
            good "overlay $repo is enabled"
        else
            sudo eselect repository enable "$repo" >/dev/null && good "enabled overlay $repo" || return 1
            sync+=(-r "$repo")
        fi
    done
    (( ${#sync[@]} )) && { tty_run sudo emaint sync "${sync[@]}" || return 1; }
    local kw=/etc/portage/package.accept_keywords
    if [[ -f $kw ]]; then kw_file=$kw; else kw_file=$kw/bugzysdotfiles; fi
    local k add=()
    for k in "${GENTOO_KEYWORDS[@]}"; do
        grep -rqsF -- "$k" "$kw" || add+=("$k")
    done
    if (( ${#add[@]} )); then
        sudo mkdir -p "$(dirname "$kw_file")"
        printf '%s\n' "# $MARK" "${add[@]}" | sudo tee -a "$kw_file" >/dev/null
        good "accepted testing keywords for: ${add[*]} ($kw_file)"
    fi
    # random-shape password dots on the lock screen (rice falls back to plain dots without it)
    local pd=/etc/portage/patches/gui-apps/hyprlock
    if ! sudo cmp -s "$DOT/patches/hyprlock-shape-dots.patch" "$pd/shape-dots.patch" 2>/dev/null; then
        sudo mkdir -p "$pd" && sudo cp "$DOT/patches/hyprlock-shape-dots.patch" "$pd/shape-dots.patch" \
            && good "hyprlock will build with the shape-dots patch ($pd)"
        rebuild_hyprlock=1
    fi
}

debian_backports() {  # Debian stable only has Hyprland in backports: offer to turn them on
    backports=""
    local id codename
    id=$(. /etc/os-release; echo "${ID:-}"); codename=$(. /etc/os-release; echo "${VERSION_CODENAME:-}")
    [[ $id == debian && -n $codename ]] || return 0
    if apt-cache policy 2>/dev/null | grep -q " $codename-backports/"; then
        backports="$codename-backports"     # already on: take the Hyprland bits (and their deps) from there
    elif apt-cache policy hyprland 2>/dev/null | grep -q 'Candidate: [^(]'; then
        return 0                           # testing/sid: in the main archive
    elif ask "Hyprland is only in Debian's backports. Turn on $codename-backports?"; then
        printf 'Types: deb\nURIs: http://deb.debian.org/debian\nSuites: %s-backports\nComponents: main\nSigned-By: /usr/share/keyrings/debian-archive-keyring.gpg\n' \
            "$codename" | sudo tee /etc/apt/sources.list.d/backports.sources >/dev/null
        tty_run sudo apt-get update -qq && backports="$codename-backports" && good "enabled $codename-backports"
    fi
}

install_packages() {
    local want=() have=() missing=() p
    rebuild_hyprlock=0
    case $distro in
        arch) want=("${ARCH_PKGS[@]}") ;;
        debian) want=("${DEBIAN_PKGS[@]}"); tty_run sudo apt-get update -qq || return 1; debian_backports ;;
        gentoo) want=("${GENTOO_PKGS[@]}"); gentoo_prepare || return 1 ;;
    esac
    mapfile -t have < <(available "${want[@]}")
    for p in "${want[@]}"; do [[ " ${have[*]} " == *" $p "* ]] || missing+=("$p"); done
    case $distro in
        arch) tty_run sudo pacman -Syu --needed "${have[@]}" ;;   # -Syu: Arch doesn't do partial upgrades
        debian)
            local bp=() rest=()
            for p in "${have[@]}"; do
                if [[ -n $backports && $p == hypr* || -n $backports && $p == xdg-desktop-portal-hyprland ]]; then bp+=("$p"); else rest+=("$p"); fi
            done
            tty_run sudo apt-get install -y "${rest[@]}" || return 1
            (( ${#bp[@]} )) && tty_run sudo apt-get install -y -t "$backports" "${bp[@]}" ;;
        gentoo)
            tty_run sudo emerge --ask=$( ((yes)) && echo n || echo y ) --noreplace --changed-use "${have[@]}" || return 1
            (( rebuild_hyprlock )) && tty_run sudo emerge --oneshot gui-apps/hyprlock ;;
    esac || return 1
    if (( ${#missing[@]} )); then
        meh "not in your distro's repos: ${missing[*]}"
        if [[ $distro == arch ]]; then
            local aur
            aur=$(command -v paru || command -v yay)
            if [[ -n $aur ]] && ask "Install them from the AUR with $(basename "$aur")?"; then
                tty_run "$aur" -S --needed "${missing[@]}"
            fi
        fi
    fi
    if [[ $distro == debian ]]; then
        local v
        v=$(hyprland --version 2>/dev/null | grep -oE '0\.[0-9]+' | head -1)
        if [[ -z $v || ${v#0.} -lt 55 ]]; then
            meh "this config needs Hyprland 0.55+ (it uses the Lua config); your repos have ${v:-none}."
            meh "Install a newer Hyprland (build it, or use a source that packages it) before logging in."
        fi
    fi
    return 0
}

# ── 0. get the files ─────────────────────────────────────────────────────────
here=""
[[ -n ${BASH_SOURCE[0]:-} && -f ${BASH_SOURCE[0]} ]] && here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ -n $here && -d $here/config/rice ]]; then
    DOT=$here
else
    if ! command -v git >/dev/null; then
        case $distro in
            arch) tty_run sudo pacman -S --needed git ;;
            debian) tty_run sudo apt-get install -y git ;;
            gentoo) tty_run sudo emerge --noreplace dev-vcs/git ;;
        esac
        command -v git >/dev/null || die "need git to download the dotfiles"
    fi
    if [[ -d $CLONE/.git ]]; then
        git -C "$CLONE" pull -q --ff-only || die "couldn't update $CLONE (local changes?)"
        good "updated $CLONE"
    else
        [[ -e $CLONE ]] && die "$CLONE already exists and isn't a clone of the dotfiles"
        git clone -q "https://github.com/$REPO.git" "$CLONE" || die "couldn't download the dotfiles"
        good "downloaded to $CLONE"
    fi
    exec bash "$CLONE/install.sh" "${ARGS[@]}" </dev/null   # carry on with the downloaded copy
fi
bold "Installing bugzysdotfiles from $DOT ($distro)"

# ── 1. packages ──────────────────────────────────────────────────────────────
bold "Packages"
if (( ! packages )); then
    meh "skipped (--no-packages); the list is in README.md"
elif [[ $distro == unknown ]]; then
    meh "don't know this distro's package manager; install the list in README.md yourself"
elif ask "Install the packages for $distro now (uses sudo)?"; then
    install_packages || die "installing packages failed (fix the error above and run this again)"
    good "packages done"
else
    meh "skipped; the list is in README.md"
fi

# ── 2. font ──────────────────────────────────────────────────────────────────
bold "Font"
if fc-list 2>/dev/null | grep -qi "MesloLGS Nerd Font"; then
    good "MesloLGS Nerd Font is installed"
elif command -v curl >/dev/null && command -v fc-cache >/dev/null; then
    fonts="$HOME/.local/share/fonts/MesloNerdFont"
    mkdir -p "$fonts"
    if curl -fsSL https://github.com/ryanoasis/nerd-fonts/releases/latest/download/Meslo.tar.xz \
        | tar -xJ -C "$fonts" --wildcards 'MesloLGS*'; then
        fc-cache -f "$fonts" >/dev/null
        good "installed MesloLGS Nerd Font into $fonts"
    else
        bad "couldn't download MesloLGS Nerd Font (https://www.nerdfonts.com/font-downloads)"
    fi
else
    meh "install MesloLGS Nerd Font yourself: https://www.nerdfonts.com/font-downloads"
fi

# ── 3. link everything ───────────────────────────────────────────────────────
bold "Linking configs"
BACKUP="$HOME/.dotfiles-backup/$(date +%Y%m%d-%H%M%S)"
link() {   # link <source in repo> <target>
    local src=$1 dst=$2
    if [[ -L $dst && $(readlink -f "$dst") == "$(readlink -f "$src")" ]]; then
        good "${dst/#$HOME/\~}"
        return
    fi
    if [[ -e $dst || -L $dst ]]; then
        mkdir -p "$BACKUP"
        mv "$dst" "$BACKUP/"
        meh "moved the old ${dst/#$HOME/\~} to ${BACKUP/#$HOME/\~}/"
    fi
    mkdir -p "$(dirname "$dst")"
    ln -s "$src" "$dst"
    good "${dst/#$HOME/\~} -> ${src/#$HOME/\~}"
}
for dir in "$DOT"/config/*/; do
    name=$(basename "$dir")
    link "$DOT/config/$name" "$HOME/.config/$name"
done
link "$DOT/scripts" "$HOME/scripts"
for f in "$DOT"/bin/*; do
    link "$f" "$HOME/.local/bin/$(basename "$f")"
done
link "$DOT/config/rice/rice" "$HOME/.local/bin/rice"

# ── 4. rice ──────────────────────────────────────────────────────────────────
if [[ -z $RICE ]]; then   # keep the rice you're on when re-running
    RICE=$(cat "$DOT/config/rice/current" 2>/dev/null)
    RICE=${RICE:-forest}
fi
bold "Applying the $RICE rice"
if ! python3 -c 'import tomllib' 2>/dev/null; then
    bad "rice needs Python 3.11+; run 'rice $RICE' once you have it"
elif "$HOME/.config/rice/rice" "$RICE" >/dev/null 2>&1; then
    good "applied (switch any time with SUPER+T or 'rice <name>')"
else
    meh "couldn't fully apply it outside Hyprland; it's rendered, run 'rice reload' once you're in"
fi

# ── 5. hyprland-pets ─────────────────────────────────────────────────────────
bold "hyprland-pets"
if (( ! pet )); then
    meh "skipped (--no-pet)"
elif [[ -L $HOME/.local/bin/hyprland-pets ]]; then
    good "already installed"
elif ask "Install hyprland-pets (the pet in the pull-down tab)?"; then
    # hyprland.lua already starts it, so the pet installer leaves the config alone
    pet_args=(--no-config)
    (( yes )) && pet_args+=(--yes)
    (( packages )) || pet_args+=(--no-deps)
    if curl -fsSL "$PETS_URL" | bash -s -- "${pet_args[@]}"; then
        good "hyprland-pets installed"
    else
        bad "hyprland-pets didn't install; try again later with: curl -fsSL $PETS_URL | bash"
    fi
else
    meh "skipped (hyprland.lua will just skip starting it)"
fi

# ── 6. extras ────────────────────────────────────────────────────────────────
bold "Extras"
add_block() {  # add_block <file> <comment prefix> <text>: append once, between markers
    local f=$1 c=$2
    if [[ -f $f ]] && grep -qF "$MARK" "$f"; then
        good "${f/#$HOME/\~} already set up"
        return
    fi
    mkdir -p "$(dirname "$f")"
    printf '\n%s %s: begin\n%s\n%s %s: end\n' "$c" "$MARK" "$3" "$c" "$MARK" >>"$f"
    good "added to ${f/#$HOME/\~}"
}
if grep -qs "start-hyprland\|exec Hyprland\|exec hyprland" "$HOME/.bash_profile" "$HOME/.profile" "$HOME/.zprofile"; then
    good "Hyprland already starts when you log in"
elif ask "Start Hyprland automatically when you log in on tty1?"; then
    [[ -e $HOME/.bash_profile ]] || echo '[[ -f ~/.bashrc ]] && . ~/.bashrc' >"$HOME/.bash_profile"
    add_block "$HOME/.bash_profile" "#" 'if [[ -z $WAYLAND_DISPLAY && $XDG_VTNR -eq 1 ]]; then
    command -v start-hyprland >/dev/null && exec start-hyprland || exec Hyprland
fi'
fi
if grep -qs fastfetch "$HOME/.bashrc" "$HOME/.config/fish/config.fish" "$HOME"/.config/fish/conf.d/*.fish; then
    good "fastfetch already runs in new terminals"
elif ask "Show fastfetch when you open kitty?"; then
    add_block "$HOME/.bashrc" "#" '[[ $- == *i* && -n $KITTY_WINDOW_ID ]] && command -v fastfetch >/dev/null && fastfetch'
    if command -v fish >/dev/null; then
        add_block "$HOME/.config/fish/conf.d/bugzysdotfiles.fish" "#" 'if status is-interactive; and set -q KITTY_WINDOW_ID; and command -q fastfetch
    fastfetch
end'
    fi
fi
dropin=/etc/systemd/system/getty@tty1.service.d/autologin.conf
if [[ ! -d /run/systemd/system ]]; then
    (( autologin )) && meh "autologin needs systemd; skipped"
elif [[ -f $dropin ]]; then
    good "tty1 autologin is set up"
elif (( autologin )) || { (( ! yes )) && ask "Log in automatically on tty1, with hyprlock as the login screen?" n; }; then
    sed "s/--autologin bugzy/--autologin $USER/" "$DOT/system/getty-tty1-autologin.conf" \
        | sudo install -Dm644 /dev/stdin "$dropin" && sudo systemctl daemon-reload \
        && good "tty1 logs you in, Hyprland opens hyprlock first (undo: sudo rm $dropin)"
fi

bold "Done"
echo "  Log into Hyprland on tty1 (or run 'hyprctl reload' if you're already in it)."
echo "  SUPER+T picks a rice. Anything that was in the way is in ~/.dotfiles-backup/."
