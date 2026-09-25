from http.server import HTTPServer, BaseHTTPRequestHandler

PORT = 7431


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"up 1\n")


if __name__ == "__main__":
    HTTPServer(("", PORT), Handler).serve_forever()
