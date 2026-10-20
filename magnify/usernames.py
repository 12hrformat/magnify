"""Username variant generation from a full name.

Mirrors the classic handle-derivation tricks used in recon:
separators, initial flips, ordering swaps and light leetspeak.
"""

from __future__ import annotations

import re

_SEPARATORS = ("", ".", "_", "-")

_LEET = {
    "a": ("a", "4", "@"),
    "e": ("e", "3"),
    "i": ("i", "1", "!"),
    "o": ("o", "0"),
    "s": ("s", "5", "$"),
    "t": ("t", "7"),
}


def _split_name(name: str) -> tuple[str, str]:
    parts = [p for p in re.split(r"\s+", name.strip()) if p]
    if not parts:
        return "", ""
    if len(parts) == 1:
        return parts[0], ""
    return parts[0], parts[-1]


def _leet_variants(word: str, limit: int = 4) -> list[str]:
    """Small bounded leetspeak expansion (not a full cartesian blowup)."""
    out = [word]
    for _ in range(limit):
        changed = False
        for cand in out:
            for i, ch in enumerate(cand):
                for repl in _LEET.get(ch, ()):
                    if repl != ch:
                        out.append(cand[:i] + repl + cand[i + 1:])
                        changed = True
                        break
                if changed:
                    break
            if len(out) >= limit + 1:
                break
        if not changed:
            break
    return out[: limit + 1]


def generate(name: str, limit: int = 40) -> list[str]:
    """Ordered, de-duplicated username candidates for a full name."""
    first, last = _split_name(name)
    if not first and not last:
        return []
    f, l = first.lower(), last.lower()
    out: list[str] = []

    def add(value: str) -> None:
        value = value.strip("._-")
        if value and value not in out:
            out.append(value)

    if f and l:
        fl, lf = f + l, l + f
        for sep in _SEPARATORS:
            add(f + sep + l)
            add(l + sep + f)
            add(f[0] + sep + l)
            add(f + sep + l[0])
            add(fl if sep == "" else "")
            add(lf if sep == "" else "")
        add(f + "x" + l)
        add(f[0] + l)
        add(f + l[0])
        add(f[0] + l[0])
        for v in _leet_variants(fl):
            add(v)
    for base in (f, l):
        add(base)
        if base:
            for year in ("90", "91", "95", "00", "1", "123"):
                add(base + year)
    return out[:limit]
