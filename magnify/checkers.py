"""Threaded username presence sweep (sherlock-style, ~45 sites)."""

from __future__ import annotations

import concurrent.futures
import re
import urllib.error
import urllib.request
from typing import Callable

from .sites import SITES, Site

DEFAULT_UA = ("magnify/0.1 "
              "(+https://github.com/12hrformat/magnify; OSINT recon)")


def _probe(site: Site, username: str, timeout: float) -> dict:
    """Check one site. Never raises; returns a result dict."""
    url = site.target(username)
    headers = {"User-Agent": DEFAULT_UA, "Accept": "*/*"}
    headers.update(site.headers)
    req = urllib.request.Request(url, headers=headers, method="GET")
    result = {
        "site": site.name,
        "username": username,
        "url": url,
        "status": None,
        "state": "unknown",   # found | missing | unknown
        "evidence": "",
        "reliable": site.reliable,
    }
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status = resp.status
            final_url = resp.geturl()
            body = resp.read(65536).decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        status = exc.code
        final_url = url
        body = ""
        try:
            body = exc.read(65536).decode("utf-8", "replace")
        except OSError:
            pass
    except (urllib.error.URLError, OSError, ValueError) as exc:
        result["evidence"] = f"request failed: {exc}"
        return result

    result["status"] = status
    if final_url != url:
        result["final_url"] = final_url

    if site.method == "regex":
        if site.not_found_regex and re.search(site.not_found_regex, body, re.I):
            result["state"] = "missing"
            result["evidence"] = f"body matches /{site.not_found_regex}/"
        elif site.found_regex and re.search(site.found_regex, body, re.I):
            result["state"] = "found"
            result["evidence"] = f"body matches /{site.found_regex}/"
        else:
            result["evidence"] = "no marker matched"
    else:
        if status in site.missing_status:
            result["state"] = "missing"
            result["evidence"] = f"HTTP {status}"
        elif 200 <= status < 300:
            result["state"] = "found"
            result["evidence"] = f"HTTP {status}"
        elif 300 <= status < 400:
            result["evidence"] = f"HTTP {status} redirect"
        else:
            result["evidence"] = f"HTTP {status} (blocked or unknown)"
    return result


def sweep(usernames: list[str], threads: int = 16, timeout: float = 10.0,
          progress: Callable[[str], None] | None = None,
          sites: list[Site] | None = None) -> list[dict]:
    """Check every username against every site. Returns all results
    where state == 'found' (plus 'unknown' ones flagged for review)."""
    site_list = sites if sites is not None else SITES
    jobs = [(s, u) for u in usernames for s in site_list]
    hits: list[dict] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as pool:
        futures = {
            pool.submit(_probe, site, user, timeout): (site, user)
            for site, user in jobs
        }
        for fut in concurrent.futures.as_completed(futures):
            result = fut.result()
            if result["state"] == "found":
                hits.append(result)
                if progress:
                    progress(f"{result['username']} on {result['site']}")
    hits.sort(key=lambda r: (r["username"], r["site"]))
    return hits
