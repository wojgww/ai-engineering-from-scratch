"""Verify the lab's HTTP framing, real process output and finite lifetime."""

import http.client
import importlib.util
from pathlib import Path
import socket
import subprocess
import sys
import threading
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("lab_server", ROOT / "server.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class HttpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = module.ThreadingHTTPServer(("127.0.0.1", 0), module.Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.port = cls.server.server_port

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=3)

    def request(self, path="/", method="GET"):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=3)
        try:
            conn.request(method, path)
            response = conn.getresponse()
            return response.status, dict(response.getheaders()), response.read()
        finally:
            conn.close()

    def test_get_matches_actual_page_and_framing(self):
        status, headers, body = self.request()
        self.assertEqual(status, 200)
        self.assertEqual(body, (ROOT / "web/index.html").read_bytes())
        self.assertEqual(int(headers["Content-Length"]), len(body))
        self.assertEqual(headers["Connection"], "close")

    def test_head_has_length_but_no_body(self):
        status, headers, body = self.request(method="HEAD")
        self.assertEqual(status, 200)
        self.assertEqual(body, b"")
        self.assertEqual(int(headers["Content-Length"]), len((ROOT / "web/index.html").read_bytes()))

    def test_health(self):
        self.assertEqual(self.request("/health")[::2], (200, b"ok\n"))

    def test_missing_path(self):
        self.assertEqual(self.request("/nie-ma")[0], 404)

    def test_cannot_serve_arbitrary_file(self):
        self.assertEqual(self.request("/../../server.py")[0], 404)

    def test_raw_http_like_nc(self):
        with socket.create_connection(("127.0.0.1", self.port), timeout=3) as conn:
            conn.sendall(b"GET /health HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n\r\n")
            chunks = []
            while True:
                chunk = conn.recv(4096)
                if not chunk:
                    break
                chunks.append(chunk)
        raw = b"".join(chunks)
        self.assertTrue(raw.startswith(b"HTTP/1.1 200 OK\r\n"))
        self.assertTrue(raw.endswith(b"\r\n\r\nok\n"))


class ProcessTests(unittest.TestCase):
    def test_real_stdout_stderr_and_stdin(self):
        run = subprocess.run([sys.executable, str(ROOT / "io_demo.py"), "--ticks", "2",
                              "--interval", "0", "--read-input"],
                             input="hello\n", text=True, capture_output=True, check=True, timeout=5)
        self.assertEqual(run.stdout.count("stdout tick="), 2)
        self.assertEqual(run.stderr.count("stderr tick="), 2)
        self.assertIn("stdin: b'hello", run.stdout)

    def test_invalid_interval(self):
        run = subprocess.run([sys.executable, str(ROOT / "io_demo.py"), "--interval", "nan"],
                             capture_output=True, timeout=5)
        self.assertEqual(run.returncode, 2)

    def test_server_terminates_itself(self):
        run = subprocess.run([sys.executable, str(ROOT / "server.py"), "--port", "0",
                              "--duration", "1"], capture_output=True, text=True, timeout=5, check=True)
        self.assertIn("LISTEN 127.0.0.1:", run.stdout)


if __name__ == "__main__":
    unittest.main()
