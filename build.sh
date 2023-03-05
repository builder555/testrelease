cd api
if [ -d dist ]; then
    rm -rf dist
fi
if [ -d build ]; then
    rm -rf build
fi
.venv/bin/pyinstaller ws_serve.py

cd ../ui
if [ -d dist ]; then
    rm -rf dist
fi
if [ -d build ]; then
    rm -rf build
fi
../api/.venv/bin/pyinstaller --add-data ./:./ serve.py

cd ..
