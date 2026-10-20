"""Checker tests against a local HTTP server - fully offline."""

import http.server
import threading
import unittest
import warnings

warnings.filterwarnings("ignore", category=ResourceWarning)

from magnify.checkers import _probe, sweep
from magnify.sites import Site


class _Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/found-user":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"hello profile")
        elif self.path == "/regex-maybe":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"no such user here")
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, *args):
        pass


class TestCheckers(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
        cls.port = cls.server.server_address[1]
        cls.thread = threading.Thread(target=cls.server.serve_forever,
                                      daemon=True)
        cls.thread.start()
        cls.base = f"http://127.0.0.1:{cls.port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def test_found_by_status(self):
        site = Site("Local", self.base + "/{u}")
        result = _probe(site, "found-user", 5.0)
        self.assertEqual(result["state"], "found")

    def test_missing_by_status(self):
        site = Site("Local", self.base + "/{u}")
        result = _probe(site, "nobody-here", 5.0)
        self.assertEqual(result["state"], "missing")

    def test_found_by_regex(self):
        site = Site("LocalR", self.base + "/regex-maybe", method="regex",
                    not_found_regex="no such user")
        result = _probe(site, "x", 5.0)
        self.assertEqual(result["state"], "missing")

    def test_connection_error_is_tolerated(self):
        site = Site("Dead", "http://127.0.0.1:1/{u}")
        result = _probe(site, "x", 2.0)
        self.assertEqual(result["state"], "unknown")

    def test_sweep_collects_hits(self):
        site = Site("Local", self.base + "/{u}")
        hits = sweep(["found-user", "missing-one"], threads=4,
                     timeout=5.0, sites=[site])
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0]["username"], "found-user")

    def test_on_result_fires_for_every_probe(self):
        site = Site("Local", self.base + "/{u}")
        seen = []
        sweep(["found-user", "missing-one", "also-missing"],
              threads=4, timeout=5.0, sites=[site],
              on_result=seen.append)
        self.assertEqual(len(seen), 3)
        states = sorted(r["state"] for r in seen)
        self.assertEqual(states, ["found", "missing", "missing"])

    def test_progress_still_fires_for_hits(self):
        site = Site("Local", self.base + "/{u}")
        notes = []
        sweep(["found-user", "missing-one"], threads=4, timeout=5.0,
              sites=[site], progress=notes.append)
        self.assertEqual(len(notes), 1)
        self.assertIn("found-user", notes[0])


if __name__ == "__main__":
    unittest.main()
