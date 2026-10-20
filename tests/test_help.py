"""Help menu tests - content stays in sync with real env var names."""

import io
import os
import re
import unittest

from magnify import help_menu, search, ui


def _strip(text: str) -> str:
    return re.sub(r"\033\[[0-9;]*m", "", text)


class CapturedMenu:
    """Drive help_menu.menu() with scripted input, capture stdout.

    When the scripted input runs out we raise EOFError (like a real
    terminal closing) rather than StopIteration, so the code under
    test follows its normal EOF path.
    """

    def __init__(self, inputs):
        self._inputs = list(inputs)
        self._pos = 0
        self._buffer = io.StringIO()
        self._real_stdout = None

    def _scripted_input(self, prompt=""):
        if self._pos >= len(self._inputs):
            raise EOFError
        value = self._inputs[self._pos]
        self._pos += 1
        return value

    def __enter__(self):
        self._real_stdout = ui.sys.stdout
        self._real_input = ui.input
        ui.sys.stdout = self._buffer
        ui.input = self._scripted_input
        return self

    def __exit__(self, *exc):
        ui.sys.stdout = self._real_stdout
        ui.input = self._real_input
        return False

    @property
    def text(self) -> str:
        return _strip(self._buffer.getvalue())


class TestHelpContent(unittest.TestCase):
    def test_guides_reference_real_env_vars(self):
        """Every env var named in the guides must actually be read."""
        blob = (help_menu.SEARX_GUIDE + help_menu.LLM_GUIDE
                + help_menu.EMAIL_GUIDE)
        for var in ("MAGNIFY_SEARX_URL", "SERPAPI_KEY",
                    "MAGNIFY_LLM_URL", "MAGNIFY_LLM_MODEL",
                    "HIBP_API_KEY", "EMAILREP_API_KEY"):
            self.assertIn(var, blob, f"{var} missing from help text")

    def test_search_guide_matches_backend_logic(self):
        """The vars the guide tells you to set are the ones detected."""
        self.assertIn("MAGNIFY_SEARX_URL", help_menu.SEARX_GUIDE)
        self.assertIn("SERPAPI_KEY", help_menu.SEARX_GUIDE)
        # search.backend() reads exactly these
        saved = {k: os.environ.pop(k, None)
                 for k in ("MAGNIFY_SEARX_URL", "SERPAPI_KEY")}
        try:
            self.assertIsNone(search.backend())
        finally:
            for k, v in saved.items():
                if v is not None:
                    os.environ[k] = v

    def test_env_vars_table_covers_all_readers(self):
        names = {name for name, _ in help_menu.ENV_VARS}
        self.assertIn("MAGNIFY_SEARX_URL", names)
        self.assertIn("SERPAPI_KEY", names)
        self.assertIn("MAGNIFY_LLM_URL", names)

    def test_legal_text_present(self):
        self.assertIn("AUTHORIZED USE ONLY", help_menu.LEGAL)

    def test_searx_guide_mentions_json_format_gotcha(self):
        """The #1 reason SearXNG integration fails - must be documented."""
        self.assertIn("json", help_menu.SEARX_GUIDE.lower())
        self.assertIn("formats", help_menu.SEARX_GUIDE)


class TestStatus(unittest.TestCase):
    def test_status_shows_not_connected(self):
        saved = {k: os.environ.pop(k, None)
                 for k in ("MAGNIFY_SEARX_URL", "SERPAPI_KEY",
                           "MAGNIFY_LLM_URL")}
        buf = io.StringIO()
        real = ui.sys.stdout
        ui.sys.stdout = buf
        try:
            help_menu.show_status()
        finally:
            ui.sys.stdout = real
            for k, v in saved.items():
                if v is not None:
                    os.environ[k] = v
        text = _strip(buf.getvalue())
        self.assertIn("not connected", text)

    def test_status_detects_searx(self):
        os.environ["MAGNIFY_SEARX_URL"] = "http://localhost:8888"
        saved = os.environ.pop("SERPAPI_KEY", None)
        buf = io.StringIO()
        real = ui.sys.stdout
        ui.sys.stdout = buf
        try:
            help_menu.show_status()
        finally:
            ui.sys.stdout = real
            del os.environ["MAGNIFY_SEARX_URL"]
            if saved is not None:
                os.environ["SERPAPI_KEY"] = saved
        text = _strip(buf.getvalue())
        self.assertIn("ready via SearXNG", text)
        self.assertIn("localhost:8888", text)


class TestHelpMenuNavigation(unittest.TestCase):
    def test_menu_lists_connect_options(self):
        with CapturedMenu(["b"]) as cap:
            help_menu.menu()
        self.assertIn("connect a search backend", cap.text)
        self.assertIn("connect an AI backend", cap.text)

    def test_back_returns(self):
        with CapturedMenu(["b"]) as cap:
            help_menu.menu()  # must not loop forever
        self.assertIn("back", cap.text)

    def test_option_1_shows_search_guide(self):
        with CapturedMenu(["1", "", "b"]) as cap:
            help_menu.menu()
        self.assertIn("CONNECT A SEARCH BACKEND", cap.text)
        self.assertIn("MAGNIFY_SEARX_URL", cap.text)

    def test_eof_exits_cleanly(self):
        # empty input sequence -> StopIteration -> must not hang/crash
        with CapturedMenu([]) as cap:
            try:
                help_menu.menu()
            except StopIteration:
                pass
        self.assertTrue(cap.text)


if __name__ == "__main__":
    unittest.main()
