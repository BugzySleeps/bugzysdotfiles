#!/usr/bin/env bash
# Screen recorder behind the waybar button (wl-screenrec: hardware H.264 through VAAPI, so it's
# light on the CPU). Recordings land in ~/Videos/Recordings.
#   record.sh status   waybar exec: prints the button as JSON, with a live timer while recording
#   record.sh toggle   left click: record the monitor you're on, or stop
#   record.sh region   right click: drag out an area with slurp and record that, or stop
#   record.sh folder   middle click: open the recordings folder
AUDIO=1   # 1 = also record what you hear (desktop audio), 0 = video only

dir="${XDG_VIDEOS_DIR:-$HOME/Videos}/Recordings"
run="${XDG_RUNTIME_DIR:-/tmp}/waybar-record"
pidf="$run.pid" filef="$run.file" startf="$run.start"

notify() { notify-send -a "Screen recorder" -i media-record "$@"; }
recording() { [[ -s $pidf ]] && kill -0 "$(<"$pidf")" 2>/dev/null; }
poke() {  # wake every bar's status loop so the button changes right away
    for f in "$run".fifo.*; do [[ -p $f ]] && echo >"$f" & done
    wait
}

start() {
    if ! command -v wl-screenrec >/dev/null; then
        notify "wl-screenrec isn't installed" "It's media-video/wl-screenrec in the guru overlay."
        exit 1
    fi
    local args=()
    if [[ $1 == region ]]; then
        local geom
        geom=$(slurp -d) || exit 0          # Esc cancels
        args+=(-g "$geom")
    else
        args+=(-o "$(hyprctl monitors -j | jq -r '.[] | select(.focused).name')")
    fi
    if (( AUDIO )); then
        args+=(--audio --audio-device "$(pactl get-default-sink).monitor")
    fi
    mkdir -p "$dir"
    local file="$dir/recording-$(date +%F_%H-%M-%S).mp4"
    setsid wl-screenrec "${args[@]}" -f "$file" >"$run.log" 2>&1 &
    echo $! >"$pidf"
    echo "$file" >"$filef"
    date +%s >"$startf"
    poke
    sleep 0.6
    if ! recording; then
        rm -f "$pidf" "$startf"
        poke
        notify -u critical "Couldn't start recording" "$(tail -n 3 "$run.log")"
    fi
}

stop() {
    local pid file
    pid=$(<"$pidf")
    file=$(<"$filef")
    kill -INT "$pid"                        # lets it finish writing the file
    for _ in {1..50}; do kill -0 "$pid" 2>/dev/null || break; sleep 0.1; done
    rm -f "$pidf" "$startf"
    poke
    (
        action=$(notify "Recording saved" "${file/#$HOME/\~}" -A open=Open -A folder="Show in folder")
        case $action in
            open) xdg-open "$file" ;;
            folder) xdg-open "$dir" ;;
        esac
    ) >/dev/null 2>&1 &
    disown
}

status() {
    # `read -t` on our own fifo is a 1 s sleep that a click can cut short, without spawning anything
    local fifo="$run.fifo.$$" last="" text cls tip
    mkfifo "$fifo" && exec 3<>"$fifo"
    trap 'rm -f "$fifo"' EXIT
    while :; do
        if recording; then
            local now t0
            printf -v now '%(%s)T' -1
            read -r t0 <"$startf" 2>/dev/null || t0=$now
            local s=$((now - t0))
            printf -v text '󰻃  %02d:%02d' $((s / 60)) $((s % 60))
            cls=recording tip="Recording: click to stop"
        else
            text='󰑊' cls=idle
            tip='Screen record\nLeft-click: this monitor\nRight-click: pick an area\nMiddle-click: recordings folder'
        fi
        local out="{\"text\": \"$text\", \"class\": \"$cls\", \"tooltip\": \"$tip\"}"
        if [[ $out != "$last" ]]; then
            printf '%s\n' "$out" || exit 0  # waybar went away
            last=$out
        fi
        read -r -t 1 -u 3 _
    done
}

case $1 in
    status) status ;;
    toggle | region) if recording; then stop; else start "$1"; fi ;;
    folder) mkdir -p "$dir" && xdg-open "$dir" >/dev/null 2>&1 & ;;
esac
