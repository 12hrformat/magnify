"""Shared session state: target identity + collected findings."""

from __future__ import annotations

import time
from dataclasses import dataclass, field


@dataclass
class Target:
    name: str = ""
    email: str = ""
    username: str = ""
    domain: str = ""
    emails: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        # Keep `email` (primary) and `emails` (all) consistent no matter
        # which one the caller populated.
        if self.email:
            self.emails = [self.email] + [e for e in self.emails
                                          if e != self.email]
        elif self.emails:
            self.email = self.emails[0]

    def empty(self) -> bool:
        return not any((self.name, self.email, self.username, self.domain))

    def display(self) -> str:
        parts = [
            ("name", self.name),
            ("email", self.email),
            ("username", self.username),
            ("domain", self.domain),
        ]
        return "  ".join(f"{k}={v}" for k, v in parts if v)

    @staticmethod
    def parse_emails(raw: str) -> list[str]:
        """Split a whitespace/comma separated email string."""
        out: list[str] = []
        for chunk in raw.replace(",", " ").split():
            if chunk and chunk not in out:
                out.append(chunk)
        return out


@dataclass
class Session:
    target: Target = field(default_factory=Target)
    username_hits: list[dict] = field(default_factory=list)
    usernames_checked: list[str] = field(default_factory=list)
    email_intel: dict = field(default_factory=dict)
    dorks: list[str] = field(default_factory=list)
    search_results: list[dict] = field(default_factory=list)
    ai_notes: dict = field(default_factory=dict)
    started: float = field(default_factory=time.time)

    def summary_counts(self) -> dict[str, int]:
        return {
            "username_hits": len(self.username_hits),
            "usernames_checked": len(self.usernames_checked),
            "dorks": len(self.dorks),
            "search_results": len(self.search_results),
            "email_intel_keys": len(self.email_intel),
            "ai_notes": len(self.ai_notes),
        }
