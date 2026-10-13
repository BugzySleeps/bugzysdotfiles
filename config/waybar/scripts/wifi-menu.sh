#!/usr/bin/env bash
# Wi-Fi picker: nmcli + wofi

menu() { wofi --dmenu --insensitive --prompt "$1" --width 420 --height 360 "${@:2}"; }

if [[ $(nmcli radio wifi) == disabled ]]; then
    choice=$(printf '󰖩  turn wifi on\n' | menu wifi) || exit
    nmcli radio wifi on
    exit
fi

declare -A ssid_for seen
lines=()
# ssid last so colons in names survive the split
while IFS=: read -r inuse signal security ssid; do
    ssid=${ssid//\\:/:}
    [[ -z $ssid || -n ${seen[$ssid]} ]] && continue
    seen[$ssid]=1
    mark="   "; [[ $inuse == '*' ]] && mark="󰄬  "
    lock="";  [[ -n $security && $security != "--" ]] && lock="  󰌾"
    line=$(printf '%s%-28s %3s%%%s' "$mark" "$ssid" "$signal" "$lock")
    lines+=("$line"); ssid_for[$line]=$ssid
done < <(nmcli -t -f in-use,signal,security,ssid dev wifi list --rescan auto)

choice=$( { printf '%s\n' "${lines[@]}"; printf '󰖪  turn wifi off\n󰒓  advanced (nmtui)\n'; } | menu wifi) || exit

case $choice in
    *"turn wifi off") nmcli radio wifi off; exit ;;
    *"advanced (nmtui)") exec kitty --class nmtui -e nmtui ;;
esac

ssid=${ssid_for[$choice]}
[[ -z $ssid ]] && exit

if nmcli -t -f name con show | grep -Fxq "$ssid"; then
    nmcli con up id "$ssid" && exit
fi
if [[ $choice == *"󰌾" ]]; then
    pw=$(menu "password for $ssid" --password --lines 1 < /dev/null) || exit
    nmcli dev wifi connect "$ssid" password "$pw"
else
    nmcli dev wifi connect "$ssid"
fi
