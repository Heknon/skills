import os
from http.server import BaseHTTPRequestHandler, HTTPServer

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "data", "cache")
DATA_DIR = "/home/appuser/app/data/cache"

if __name__ == "__main__":
    os.makedirs(DATA_DIR, exist_ok=True)

    class H(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"ok")

    HTTPServer(("0.0.0.0", 80), H).serve_forever()
