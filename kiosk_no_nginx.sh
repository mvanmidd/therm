#!/bin/sh
# Launch a browser in kiosk mode on display 0
# Based on https://www.sylvaindurand.org/launch-chromium-in-kiosk-mode/
export DISPLAY=:0

xset -dpms
xset s off
xset s noblank


unclutter &
#chromium-browser 127.0.0.1:5000/chart --window-size=320,240 --start-fullscreen --kiosk --incognito \

chromium-browser 127.0.0.1/chart --window-size=320,240 --start-fullscreen --kiosk --incognito \
    --noerrdialogs --disable-translate --no-first-run --fast --fast-start --disable-infobars \
    --disable-features=TranslateUI --disk-cache-dir=/dev/null
