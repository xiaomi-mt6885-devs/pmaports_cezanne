#!/usr/bin/sh

sleep 5
uclampset --pid $(pidof gnome-shell) -m 900 2>&1 >/dev/null || true

echo "Configured gnome-shell uclamp..."
