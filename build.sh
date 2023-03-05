if [ -d api/dist ]; then
    rm -rf api/dist
fi
if [ -d api/build ]; then
    rm -rf api/build
fi
api/.venv/bin/pyinstaller api/ws_serve.py

# cd ../ui
if [ -d ui/dist ]; then
    rm -rf ui/dist
fi
if [ -d ui/build ]; then
    rm -rf ui/build
fi
api/.venv/bin/pyinstaller --add-data ui:ui ui/serve.py
