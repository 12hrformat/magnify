"""Progress bar tests (no tty required - uses a fake stdout)."""

import io
import unittest

from magnify import ui


class _FakeTTY(io.StringIO):
    def isatty(self):
        return True


class TestProgressBar(unittest.TestCase):
    def setUp(self):
        self._real_stdout = ui.sys.stdout
        self._real_color = ui.COLOR
        ui.COLOR = True
        self.out = _FakeTTY()
        ui.sys.stdout = self.out

    def tearDown(self):
        ui.sys.stdout = self._real_stdout
        ui.COLOR = self._real_color

    def test_counts_and_percentage(self):
        bar = ui.ProgressBar(10, label="sweep")
        bar.update(5)
        self.assertEqual(bar.count, 5)
        buf = self.out.getvalue()
        self.assertIn("50.0%", buf)
        self.assertIn("5/10", buf)

    def test_hit_counter(self):
        bar = ui.ProgressBar(4, label="sweep")
        bar.update(hit=True)
        bar.update(hit=True)
        bar.update()
        self.assertEqual(bar.hits, 2)
        self.assertIn("2 hits", self.out.getvalue())

    def test_note_is_shown(self):
        bar = ui.ProgressBar(4, label="sweep")
        bar.update(note="+ johndoe @ GitHub")
        self.assertIn("johndoe @ GitHub", self.out.getvalue())

    def test_never_exceeds_total(self):
        bar = ui.ProgressBar(3, label="sweep")
        for _ in range(10):
            bar.update()
        self.assertEqual(bar.count, 3)
        self.assertIn("100.0%", self.out.getvalue())

    def test_non_tty_falls_back_to_lines(self):
        out = io.StringIO()  # not a tty
        ui.sys.stdout = out
        bar = ui.ProgressBar(3, label="sweep")
        bar.update()
        bar.update()
        bar.update()
        bar.finish()
        text = out.getvalue()
        self.assertNotIn("\r", text)
        self.assertIn("1/3", text)
        self.assertIn("3/3", text)

    def test_finish_reaches_100(self):
        bar = ui.ProgressBar(5, label="sweep")
        bar.update(2)
        bar.finish()
        self.assertEqual(bar.count, 5)


if __name__ == "__main__":
    unittest.main()
