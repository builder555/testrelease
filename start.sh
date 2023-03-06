#!/bin/bash
./ws_serve/ws_serve &
pid1=$!

./serve/serve &
pid2=$!

sleep 5
open http://localhost:8080/

trap "kill $pid1 $pid2" EXIT
wait $pid1 $pid2