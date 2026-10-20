import json
import os
import tempfile
import unittest

from magnify import report
from magnify.session import Session, Target


class TestReport(unittest.TestCase):
    def _session(self) -> Session:
        s = Session(Target(name="John Doe", email="john@example.com"))
        s.email_intel = {"email": "john@example.com", "spf": "v=spf1 -all"}
        s.username_hits = [{
            "username": "johndoe", "site": "GitHub",
            "url": "https://github.com/johndoe",
            "evidence": "HTTP 200", "reliable": True,
        }]
        s.dorks = ['"John Doe" filetype:pdf']
        s.ai_notes = {"summary": "test", "pivots": ["pivot 1"], "dorks": []}
        return s

    def test_save_writes_both_files(self):
        session = self._session()
        with tempfile.TemporaryDirectory() as tmp:
            base = os.path.join(tmp, "out")
            md_path, json_path = report.save(session, base)
            self.assertTrue(os.path.exists(md_path))
            self.assertTrue(os.path.exists(json_path))
            with open(md_path) as fh:
                md = fh.read()
            self.assertIn("John Doe", md)
            self.assertIn("GitHub", md)
            self.assertIn("filetype:pdf", md)
            with open(json_path) as fh:
                data = json.load(fh)
            self.assertEqual(data["target"]["name"], "John Doe")
            self.assertEqual(len(data["username_hits"]), 1)


if __name__ == "__main__":
    unittest.main()
