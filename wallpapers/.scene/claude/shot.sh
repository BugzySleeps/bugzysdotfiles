#!/bin/sh
# shot.sh [out.png] — renders scene.qml (idle) to ../../claude.png, the still the picker and the palette use.
#   PLAY=1 shot.sh /tmp/x.png   a frame with fake music, to check how it moves
here=$(cd "$(dirname "$0")" && pwd)
out=${1:-$here/../../claude.png}
SCENE="$here" SHOT=$(realpath -m "$out") timeout 20 qs -p "$here/shot" >/dev/null 2>"$here/shot/log.txt" || { cat "$here/shot/log.txt"; exit 1; }
echo "saved $out"
