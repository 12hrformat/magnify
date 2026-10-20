"""Optional dork execution backends.

magnify never queries Google directly. Two supported paths:

1. SearXNG  - a self-hosted metasearch instance with json enabled
             (config: MAGNIFY_SEARX_URL, e.g. http://localhost:8888)
2. SerpAPI  - official API (config: SERPAPI_KEY)

If neither is configured, dorks are for manual pasting only.
"""

from __future__ import annotations

import json
import os
import time
import urllib.parse
import urllib.request

UA = "magnify/0.1 (+https://github.com/12hrformat/magnify)"


def backend() -> str | None:
    if os.environ.get("MAGNIFY_SEARX_URL"):
        return "searx"
    if os.environ.get("SERPAPI_KEY"):
        return "serpapi"
    return None


def _searx(query: str, base: str, limit: int) -> list[dict]:
    url = (base.rstrip("/") + "/search?" +
           urllib.parse.urlencode({"q": query, "format": "json"}))
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=20.0) as resp:
        data = json.loads(resp.read().decode("utf-8", "replace"))
    out = []
    for item in data.get("results", [])[:limit]:
        out.append({
            "title": item.get("title", ""),
            "url": item.get("url", ""),
            "snippet": item.get("content", "")[:300],
            "engine": item.get("engine", "searx"),
        })
    return out


def _serpapi(query: str, limit: int) -> list[dict]:
    key = os.environ["SERPAPI_KEY"]
    url = ("https://serpapi.com/search.json?" +
           urllib.parse.urlencode({
               "q": query, "engine": "google", "api_key": key, "num": "10"}))
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=20.0) as resp:
        data = json.loads(resp.read().decode("utf-8", "replace"))
    out = []
    for item in data.get("organic_results", [])[:limit]:
        out.append({
            "title": item.get("title", ""),
            "url": item.get("link", ""),
            "snippet": item.get("snippet", "")[:300],
            "engine": "serpapi",
        })
    return out


def run(dorks: list[str], per_dork: int = 5,
        delay: float = 1.0) -> list[dict]:
    """Execute the dork battery against the configured backend."""
    name = backend()
    if not name:
        return []
    base = os.environ.get("MAGNIFY_SEARX_URL", "")
    results: list[dict] = []
    for dork in dorks:
        try:
            if name == "searx":
                hits = _searx(dork, base, per_dork)
            else:
                hits = _serpapi(dork, per_dork)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            results.append({"dork": dork, "error": str(exc), "hits": []})
            continue
        results.append({"dork": dork, "hits": hits})
        time.sleep(delay)  # politeness
    return results
