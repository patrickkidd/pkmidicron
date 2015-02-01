#!/bin/sh

rm -f /Users/patrick/Library/Preferences/com.vedanamedia.PKMidiCron.plist
# killall -u $USER cfprefsd
defaults delete com.vedanamedia.PKMidiCron
true # prevent exit code
