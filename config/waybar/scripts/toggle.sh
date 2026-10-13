#!/usr/bin/env bash
# SUPER+Tab: close waybar if it's up, launch it if not.
# Hyprland's layer rule animates the map/unmap (slide from top).
if pgrep -x waybar >/dev/null; then
    pkill -x waybar
else
    setsid -f waybar >/dev/null 2>&1
fi
