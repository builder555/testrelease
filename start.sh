#!/bin/bash
cd "$(dirname "$0")"

if [ "$(uname)" == "Darwin" ]; then
    # for MacOS remove the quarantine attributes
    # this is needed because the mac will not execute binaries that are downloaded from the internet
    # see https://developer.apple.com/library/archive/technotes/tn2459/_index.html
    if xattr -p com.apple.quarantine ./ws_serve/ws_serve >/dev/null 2>&1; then
        find ./ -type file | xargs xattr -rd com.apple.quarantine
    fi
fi

./ws_serve/ws_serve &
pid1=$!

./serve/serve &
pid2=$!

sleep 5
open http://localhost:8080/

trap "kill $pid1 $pid2" EXIT
wait $pid1 $pid2