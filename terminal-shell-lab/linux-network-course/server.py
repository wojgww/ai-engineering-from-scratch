"""Finite local HTTP lab for README.md, exercises 9–10 from the user's sheet.

HTTP/1.1 framing reference: https://www.rfc-editor.org/rfc/rfc9112.html.
Uses Python standard library, explicit Content-Length and Connection: close.
Default loopback binding and finite lifetime; never serves arbitrary files.
"""

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import threading

ROOT = Path(__file__).resolve().parent


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "ShellLab/1.0"
    sys_version = ""
    timeout = 120

    def respond(self, head=False):
        if self.path == "/":
            status, kind, body = 200, "text/html; charset=utf-8", (ROOT / "web/index.html").read_bytes()
        elif self.path == "/health":
            status, kind, body = 200, "text/plain; charset=utf-8", b"ok\n"
        else:
            status, kind, body = 404, "text/plain; charset=utf-8", b"Nie znaleziono strony.\n"
        self.send_response(status)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Connection", "close")
        self.send_header("X-Lab", "terminal-shell")
        self.end_headers()
        if not head:
            self.wfile.write(body)
        self.close_connection = True

    def do_GET(self):
        self.respond()

    def do_HEAD(self):
        self.respond(head=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bind", choices=("127.0.0.1", "0.0.0.0"), default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--duration", type=int, default=900, help="Lifetime in seconds (default 900)")
    args = parser.parse_args()
    if not 0 <= args.port <= 65535 or args.duration < 1:
        parser.error("port must be 0..65535 and duration >= 1")
    with ThreadingHTTPServer((args.bind, args.port), Handler) as server:
        timer = threading.Timer(args.duration, server.shutdown)
        timer.daemon = True
        timer.start()
        print(f"LISTEN {args.bind}:{server.server_port}; lifetime={args.duration}s", flush=True)
        try:
            server.serve_forever(poll_interval=0.1)
        except KeyboardInterrupt:
            pass
        finally:
            timer.cancel()


if __name__ == "__main__":
    main()
