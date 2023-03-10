#!/bin/bash

pushd ui || exit 2
npm run build
popd || exit 2

pyinstaller api/ws_serve.py
pyinstaller --add-data ui/dist:ui ui/serve.py
