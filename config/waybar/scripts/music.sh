#!/usr/bin/env bash
# cava bars + what cmus/swiftify is playing, for waybar; prints nothing when neither player is open

players=cmus,swiftify
dir=$(mktemp -d -t waybar-music.XXXXXX)
trap 'trap - EXIT TERM; rm -rf "$dir"; kill 0' EXIT TERM  # (reset first: kill 0 hits us too, and would rerun this forever)

cat > "$dir/cava" <<CONF
[general]
bars = 10
framerate = 30

[input]
method = pipewire
source = auto

[output]
method = raw
raw_target = /dev/stdout
data_format = ascii
ascii_max_range = 7
CONF

# keep the latest "status|artist|title" (\x1f-separated, so an empty artist isn't merged away) in $dir/now
: > "$dir/now"
playerctl -p "$players" -F metadata --format $'{{status}}\x1f{{artist}}\x1f{{title}}' 2>/dev/null |
    while IFS= read -r line; do printf '%s\n' "$line" > "$dir/now"; done &

esc() { local s=${1//&/"&amp;"}; s=${s//</"&lt;"}; printf '%s' "${s//>/"&gt;"}"; }

shopt -s extglob
parent=$PPID
last=
cava -p "$dir/cava" | sed -u 's/;//g; y/01234567/▁▂▃▄▅▆▇█/; s/^▁*$//' |
while IFS= read -r bars; do
    [[ -e /proc/$parent ]] || kill 0  # waybar went away: take down cava + playerctl too
    IFS=$'\x1f' read -r status artist title < "$dir/now" 2>/dev/null
    if [[ -z $title ]]; then
        out=
    else
        song=${title%.@(flac|mp3|ogg|opus|m4a|wav)}; [[ -n $artist ]] && song="$artist — $song"
        (( ${#song} > 40 )) && song="${song:0:39}…"
        [[ $status == Playing ]] && icon= || icon=
        out="$icon  $(esc "$song")"
        [[ -n $bars ]] && out="<span alpha='60%'>$bars</span>  $out"
    fi
    [[ $out != "$last" ]] && printf '%s\n' "$out" && last=$out
done
