#!/usr/bin/env bash
# Feed cava's raw output into waybar as bar glyphs; prints nothing when silent

trap 'trap - EXIT TERM; rm -f "$conf"; kill 0' EXIT TERM  # (reset first: kill 0 hits us too, and would rerun this forever)

# waybar doesn't always take this script down with it (a killed waybar left cava running),
# so watch for waybar and leave when it's gone
( while pgrep -x waybar >/dev/null; do sleep 5; done; kill -TERM $$ ) &

conf=$(mktemp -t waybar-cava.XXXXXX)
cat > "$conf" <<EOF
[general]
bars = 14
framerate = 30

[input]
method = pipewire
source = auto

[output]
method = raw
raw_target = /dev/stdout
data_format = ascii
ascii_max_range = 7
EOF

~/.config/rice/cava-run "$conf" | sed -u 's/;//g; y/01234567/▁▂▃▄▅▆▇█/; s/^▁*$//'
