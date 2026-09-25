import argparse
import logging
import sqlite3
from http.server import BaseHTTPRequestHandler, HTTPServer

from tracker import config


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ok\n")


def init_db(path):
    with sqlite3.connect(path) as db:
        db.execute("create table if not exists items (id integer primary key, title text)")


def main():
    parser = argparse.ArgumentParser(prog="tracker")
    parser.add_argument("--init-db", action="store_true", help="create the database and exit")
    args = parser.parse_args()
    logging.basicConfig(level=config.LOG_LEVEL)
    if args.init_db:
        init_db(config.DB_PATH)
        return
    HTTPServer((config.HOST, config.PORT), Handler).serve_forever()
