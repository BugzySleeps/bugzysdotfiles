#!/usr/bin/env bash
# cmus that lives in waybar instead of a workspace.
#   cmus.sh status   waybar module output (json)
#   cmus.sh toggle   left click: pull the cmus popup down / put it away (starts cmus if needed)
#   cmus.sh detach   right click: popup -> normal tiled window here, or window -> back into the bar
# "Docked" means the cmus window sits in the hidden special:cmus workspace.

special=cmus
signal=8  # matches "signal" in the waybar module

client() {  # json of the window running cmus: kitty --class cmus, or any terminal whose child is cmus
    local clients pid
    clients=$(hyprctl clients -j) || return
    jq -ce '.[] | select(.class == "cmus")' <<<"$clients" | head -n1 | grep . && return
    pid=$(pgrep -xo cmus) || return 1
    while (( pid > 1 )); do
        jq -ce --argjson p "$pid" '.[] | select(.pid == $p)' <<<"$clients" | head -n1 | grep . && return
        pid=$(ps -o ppid= -p "$pid" | tr -d ' ')
    done
    return 1
}

d() { hyprctl dispatch "$1" >/dev/null; }
refresh() { pkill -RTMIN+$signal -x waybar; }
special_shown() { hyprctl monitors -j | jq -e --arg n "special:$special" 'any(.[]; .specialWorkspace.name == $n)' >/dev/null; }

popup() {  # float it as a centred popup in the special workspace
    d "hl.dsp.window.move({ workspace = \"special:$special\", window = \"address:$1\", follow = false })"
    d "hl.dsp.window.float({ action = \"enable\", window = \"address:$1\" })"
    d "hl.dsp.window.resize({ window = \"address:$1\", x = 900, y = 520, relative = false })"
    d "hl.dsp.window.center({ window = \"address:$1\" })"
}

case $1 in
status)
    if ! pgrep -x cmus >/dev/null; then
        printf '{"text":"","tooltip":"cmus not running — click to start","class":"off"}\n'
        exit
    fi
    q=$(cmus-remote -Q 2>/dev/null)
    tag() { sed -n "s/^tag $1 //p" <<<"$q" | head -n1; }
    status=$(sed -n 's/^status //p' <<<"$q")
    title=$(tag title); artist=$(tag artist)
    [[ -z $title ]] && { title=$(sed -n 's/^file //p' <<<"$q"); title=${title##*/}; title=${title%.*}; }
    song=$title; [[ -n $artist && -n $title ]] && song="$artist — $title"
    (( ${#song} > 40 )) && song="${song:0:39}…"
    [[ $status == playing ]] && icon= || icon=
    where=window; client | jq -e --arg n "special:$special" '.workspace.name == $n' >/dev/null && where=docked
    jq -nc --arg t "$icon${song:+  $song}" --arg c "$where $status" \
        --arg tip "${song:-cmus} — left click: show/hide, right click: $([[ $where == docked ]] && echo 'pop out as window' || echo 'dock into bar')" \
        '{text: $t, tooltip: $tip, class: ($c | split(" "))}'
    ;;
toggle)
    if ! win=$(client); then
        setsid -f kitty --class cmus -e cmus >/dev/null 2>&1
        for _ in $(seq 25); do win=$(client) && break; sleep 0.2; done
        [[ -n $win ]] || exit 1
        popup "$(jq -r .address <<<"$win")"
        special_shown || d "hl.dsp.workspace.toggle_special(\"$special\")"
    elif jq -e --arg n "special:$special" '.workspace.name == $n' <<<"$win" >/dev/null; then
        d "hl.dsp.workspace.toggle_special(\"$special\")"
    else  # popped out as a window somewhere: go to it
        d "hl.dsp.focus({ window = \"address:$(jq -r .address <<<"$win")\" })"
    fi
    refresh
    ;;
detach)
    win=$(client) || exit 0
    addr=$(jq -r .address <<<"$win")
    if jq -e --arg n "special:$special" '.workspace.name == $n' <<<"$win" >/dev/null; then
        ws=$(hyprctl activeworkspace -j | jq -r .id)  # the normal workspace under the popup
        special_shown && d "hl.dsp.workspace.toggle_special(\"$special\")"
        d "hl.dsp.window.move({ workspace = \"$ws\", window = \"address:$addr\", follow = false })"
        d "hl.dsp.window.float({ action = \"disable\", window = \"address:$addr\" })"
        d "hl.dsp.focus({ window = \"address:$addr\" })"
    else
        popup "$addr"
    fi
    refresh
    ;;
esac
