# Does the build
Push-Location ui
npm run build
Pop-Location

pyinstaller api/ws_serve.py
pyinstaller --add-data "ui/dist;ui" ui/serve.py
