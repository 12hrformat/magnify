"""Terminal UI helpers: colors, menus, select tables, spinners."""

from __future__ import annotations

import contextlib
import os
import re
import sys
import threading
import time

_ANSI_RE = re.compile(r"\033\[[0-9;]*m")

# Indirection so tests can drive prompts without a real terminal.
input = input  # noqa: A001  (rebound by tests)


def _supports_color() -> bool:
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("FORCE_COLOR"):
        return True
    return sys.stdout.isatty()


COLOR = _supports_color()


def _c(code: str, text: str) -> str:
    if not COLOR:
        return text
    return f"\033[{code}m{text}\033[0m"


def bold(text: str) -> str:
    return _c("1", text)


def dim(text: str) -> str:
    return _c("2", text)


def red(text: str) -> str:
    return _c("31", text)


def green(text: str) -> str:
    return _c("32", text)


def yellow(text: str) -> str:
    return _c("33", text)


def blue(text: str) -> str:
    return _c("34", text)


def cyan(text: str) -> str:
    return _c("36", text)


def banner() -> None:
    art = r"""
   ▄▄▄▄███▄▄▄▄      ▄████████    ▄██████▄  ███▄▄▄▄    ▄█     ▄████████ ▄██   ▄
 ▄██▀▀▀███▀▀▀██▄   ███    ███   ███    ███ ███▀▀▀██▄ ███    ███    ███ ███   ██▄
 ███   ███   ███   ███    ███   ███    █▀  ███   ███ ███▌   ███    █▀  ███▄▄▄███
 ███   ███   ███   ███    ███  ▄███        ███   ███ ███▌  ▄███▄▄▄     ▀▀▀▀▀▀███
 ███   ███   ███ ▀███████████ ▀▀███ ████▄  ███   ███ ███▌ ▀▀███▀▀▀     ▄██   ███
 ███   ███   ███   ███    ███   ███    ███ ███   ███ ███    ███        ███   ███
 ███   ███   ███   ███    ███   ███    ███ ███   ███ ███    ███        ███   ███
  ▀█   ███   █▀    ███    █▀    ████████▀   ▀█   █▀  █▀     ███         ▀█████▀
"""
    # Strip trailing whitespace so we never emit lines wider than the
    # art itself (keeps it from wrapping on an 80-column terminal).
    print(cyan("\n".join(line.rstrip() for line in art.splitlines())))
    print(dim("  interactive OSINT orchestrator  |  authorized use only"))
    print()


def menu(title: str, items: list[tuple[str, str]]) -> str:
    """Print a numbered menu, return the chosen key."""
    print(blue(f"\n┌─ {title}"))
    for key, label in items:
        print(blue("│ ") + f"[{bold(key)}] {label}")
    print(blue("└" + "─" * 60))
    while True:
        try:
            choice = input(dim("magnify> ")).strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            return "quit"
        except Exception:
            # Any other input failure (closed stdin, broken pipe, a
            # container with no tty) must exit rather than spin.
            print()
            return "quit"
        keys = [k for k, _ in items]
        if choice in keys:
            return choice
        if choice == "quit":
            return "quit"
        print(red(f"  pick one of: {', '.join(keys)}"))


def ask(label: str, default: str = "") -> str:
    try:
        hint = dim(f" [{default}]") if default else ""
        value = input(f"{bold(label)}{hint}: ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return default
    return value or default


def confirm(label: str, default: bool = True) -> bool:
    hint = "[Y/n]" if default else "[y/N]"
    try:
        value = input(f"{bold(label)} {dim(hint)}: ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print()
        return default
    if not value:
        return default
    return value in ("y", "yes")


def select_table(title: str, options: list[str], columns: int = 4,
                 default: str = "") -> list[int]:
    """Interactive multi-select table.

    Shows options numbered in a grid. User enters e.g. ``1,3-5`` or
    ``all``. Returns selected indexes.
    """
    print(blue(f"\n┌─ {title}") + dim("  (e.g. 1,3-5  or  all  or  none)"))
    row: list[str] = []
    for i, opt in enumerate(options, 1):
        row.append(f"{bold(f'{i:>2})'):>5} {opt:<14}")
        if len(row) == columns:
            print(blue("│ ") + "  ".join(row))
            row = []
    if row:
        print(blue("│ ") + "  ".join(row))
    print(blue("└" + "─" * 60))
    while True:
        try:
            raw = input(f"{bold('select')} {dim(f'(default: {default})')}: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            raw = "none"
        raw = raw or default
        if raw == "all":
            return list(range(len(options)))
        if raw == "none":
            return []
        picked: list[int] = []
        ok = True
        for part in raw.replace(" ", "").split(","):
            if not part:
                continue
            if "-" in part:
                a, _, b = part.partition("-")
                if a.isdigit() and b.isdigit() and int(a) <= int(b):
                    picked.extend(range(int(a) - 1, int(b)))
                    continue
            elif part.isdigit():
                picked.append(int(part) - 1)
                continue
            ok = False
            break
        if ok and all(0 <= p < len(options) for p in picked):
            seen: set[int] = set()
            return [p for p in picked if not (p in seen or seen.add(p))]
        print(red("  invalid selection, try again"))


@contextlib.contextmanager
def spinner(message: str):
    """'Please wait' spinner for background-less terminal work."""
    if not sys.stdout.isatty():
        print(dim(f"  ... {message}"))
        yield
        return
    stop = threading.Event()
    frames = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"

    def _run() -> None:
        i = 0
        while not stop.is_set():
            sys.stdout.write(f"\r  {cyan(frames[i % len(frames)])} {message}")
            sys.stdout.flush()
            i += 1
            time.sleep(0.1)
        pad = " " * (len(message) + 6)
        sys.stdout.write(f"\r{pad}\r")
        sys.stdout.flush()

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    try:
        yield
    finally:
        stop.set()
        t.join(timeout=1.0)


class ProgressBar:
    """Thread-safe progress bar with live hit callback.

    Usage:
        bar = ProgressBar(total, label="sweeping")
        bar.update(1, note="johndoe @ GitHub")
        bar.finish()
    """

    _BLOCKS = "█"
    _EMPTY = "░"

    def __init__(self, total: int, label: str = "", width: int = 32,
                 hits: int = 0):
        self.total = max(total, 1)
        self.label = label
        self.width = width
        self.count = 0
        self.hits = hits
        self._lock = threading.Lock()
        self._interactive = sys.stdout.isatty() and COLOR

    def _bar(self) -> str:
        frac = self.count / self.total
        filled = int(self.width * frac)
        bar = self._BLOCKS * filled + self._EMPTY * (self.width - filled)
        pct = f"{frac * 100:5.1f}%"
        if COLOR:
            bar = cyan(bar[:filled]) + dim(bar[filled:])
        return f"{bar} {pct}"

    def render(self, note: str = "") -> None:
        with self._lock:
            counter = f"{self.count}/{self.total}"
            bar = self._bar()
            hits = f"  {green(str(self.hits) + ' hits')}" if self.hits else ""
            # Build from most- to least-important, dropping optional
            # pieces when the terminal is narrow.
            candidates = [
                f"  {self.label} {bar} {counter}{hits}  {dim(note[:48])}",
                f"  {self.label} {bar} {counter}{hits}",
                f"  {bar} {counter}{hits}",
                f"  {counter}{hits}",
            ]
            budget = max(_term_width() - 1, 10)
            line = next(
                (c for c in candidates if self._visible_len(c) <= budget),
                candidates[-1])
            if self._interactive:
                self._write_line(line)
            elif self.count in (1, self.total):
                print(line)

    @staticmethod
    def _visible_len(text: str) -> int:
        """Length ignoring ANSI escape sequences."""
        return len(_ANSI_RE.sub("", text))

    def _write_line(self, line: str) -> None:
        budget = max(_term_width() - 1, 10)
        visible = self._visible_len(line)
        if visible > budget:
            # truncate the visible content, preserving escape codes
            out, shown = [], 0
            i = 0
            while i < len(line) and shown < budget:
                match = _ANSI_RE.match(line, i)
                if match:
                    out.append(match.group())
                    i = match.end()
                    continue
                out.append(line[i])
                shown += 1
                i += 1
            line = "".join(out)
        else:
            line = line + " " * (budget - visible)
        sys.stdout.write("\r" + line)
        sys.stdout.flush()

    def update(self, step: int = 1, note: str = "", hit: bool = False) -> None:
        with self._lock:
            self.count = min(self.count + step, self.total)
            if hit:
                self.hits += 1
        self.render(note)

    def finish(self) -> None:
        self.count = self.total
        self.render()
        if self._interactive:
            sys.stdout.write("\n")
            sys.stdout.flush()


def _term_width() -> int:
    try:
        return os.get_terminal_size().columns
    except OSError:
        return 80



def info(text: str) -> None:
    print(f"  {blue('•')} {text}")


def ok(text: str) -> None:
    print(f"  {green('✔')} {text}")


def warn(text: str) -> None:
    print(f"  {yellow('!')} {text}")


def err(text: str) -> None:
    print(f"  {red('✖')} {text}")


def finding(text: str) -> None:
    print(f"    {green('+')} {text}")
