#!/usr/bin/env bash
# Feed cava's raw output into waybar as bar glyphs; prints nothing when silent

trap 'rm -f "$conf"; kill 0' EXIT TERM

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

cava -p "$conf" | sed -u 's/;//g; y/01234567/▁▂▃▄▅▆▇█/; s/^▁*$//'
