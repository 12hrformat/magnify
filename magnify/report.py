"""Report writer: Markdown + JSON."""

from __future__ import annotations

import json
import time

from . import __version__
from .session import Session


def _markdown(session: Session) -> str:
    t = session.target
    out: list[str] = []
    out.append(f"# magnify report — {t.display() or 'unnamed target'}")
    out.append("")
    out.append(f"- generated: {time.strftime('%Y-%m-%d %H:%M:%S %z')}")
    out.append(f"- tool: magnify v{__version__}")
    out.append(f"- runtime: {int(time.time() - session.started)}s")
    out.append("")

    if session.email_intel:
        out.append("## Email intelligence")
        out.append("")
        out.append("| check | result |")
        out.append("|---|---|")
        for key, value in session.email_intel.items():
            if key in ("email",):
                continue
            rendered = value if isinstance(value, str) else json.dumps(value)
            out.append(f"| {key} | {rendered[:200]} |")
        out.append("")

    if session.username_hits:
        out.append("## Username hits")
        out.append("")
        out.append("| username | site | url | evidence | verified |")
        out.append("|---|---|---|---|---|")
        for hit in session.username_hits:
            verified = "yes" if hit.get("reliable", True) else "heuristic"
            out.append(
                f"| {hit['username']} | {hit['site']} | {hit['url']} "
                f"| {hit.get('evidence', '')} | {verified} |")
        out.append("")
    elif session.usernames_checked:
        out.append("## Username hits")
        out.append("")
        out.append("_no accounts found for the tested variants._")
        out.append("")

    if session.dorks:
        out.append("## Dork battery")
        out.append("")
        for dork in session.dorks:
            out.append(f"```\n{dork}\n```")
        out.append("")

    if session.search_results:
        out.append("## Search results")
        out.append("")
        for entry in session.search_results:
            out.append(f"### `{entry.get('dork', '')}`")
            if entry.get("error"):
                out.append(f"_error: {entry['error']}_")
            for hit in entry.get("hits", []):
                out.append(f"- [{hit.get('title', '')}]({hit.get('url', '')})")
                if hit.get("snippet"):
                    out.append(f"  > {hit['snippet']}")
            out.append("")

    if session.ai_notes:
        out.append("## AI pivots")
        out.append("")
        if session.ai_notes.get("summary"):
            out.append(f"**Summary:** {session.ai_notes['summary']}")
            out.append("")
        for pivot in session.ai_notes.get("pivots", []):
            out.append(f"- {pivot}")
        extra = session.ai_notes.get("dorks", [])
        if extra:
            out.append("")
            out.append("Suggested dorks:")
            for dork in extra:
                out.append(f"```\n{dork}\n```")
        out.append("")

    out.append("---")
    out.append("")
    out.append("_magnify — authorized testing only. Verify every hit manually;_")
    out.append("_heuristic results can produce false positives._")
    out.append("")
    return "\n".join(out)


def save(session: Session, basepath: str) -> tuple[str, str]:
    """Write <basepath>.md and <basepath>.json; return paths."""
    md_path = basepath + ".md"
    json_path = basepath + ".json"
    with open(md_path, "w", encoding="utf-8") as fh:
        fh.write(_markdown(session))
    payload = {
        "target": vars(session.target),
        "email_intel": session.email_intel,
        "usernames_checked": session.usernames_checked,
        "username_hits": session.username_hits,
        "dorks": session.dorks,
        "search_results": session.search_results,
        "ai_notes": session.ai_notes,
        "generated": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "tool": f"magnify {__version__}",
    }
    with open(json_path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, default=str)
    return md_path, json_path
