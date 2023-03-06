import http.server
import socketserver
import os

PORT = 8080
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=os.path.join(DIRECTORY,'ui'), **kwargs)


with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print("serving UI at port", PORT)
    httpd.serve_forever()
