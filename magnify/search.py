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
import urllib.error
import urllib.parse
import urllib.request

UA = "magnify/0.1 (+https://github.com/12hrformat/magnify)"

# Accepted spellings for the SerpAPI key. The canonical name is
# SERPAPI_KEY; the aliases exist because environment variables are
# case-sensitive and these are easy to mistype.
SERPAPI_ALIASES = (
    "SERPAPI_KEY", "SERP_API_KEY", "SERPAPI", "serpapi_key",
    "SERPAPI_API_KEY",
)
# Accepted spellings for the SearXNG base URL.
SEARX_ALIASES = (
    "MAGNIFY_SEARX_URL", "SEARXNG_URL", "SEARX_URL", "MAGNIFY_SEARXNG_URL",
)


def _first_env(names: tuple[str, ...]) -> tuple[str, str] | None:
    """Return (name, value) for the first alias that is set.

    Matching is case-insensitive because environment variables are
    easy to type in the wrong case.
    """
    wanted = {n.upper(): n for n in names}
    for name, value in os.environ.items():
        canonical = wanted.get(name.upper())
        if canonical and value:
            return canonical, value
    return None


def serpapi_key() -> str | None:
    found = _first_env(SERPAPI_ALIASES)
    return found[1] if found else None


def searx_url() -> str | None:
    found = _first_env(SEARX_ALIASES)
    return found[1] if found else None


def near_miss_env() -> list[str]:
    """Environment vars that look like a backend but are misnamed.

    Catches things like `serpapi` or `serp_api` so we can tell the user
    exactly what to rename instead of silently doing nothing.
    """
    wanted = set(SERPAPI_ALIASES) | set(SEARX_ALIASES)
    hits: list[str] = []
    for name in os.environ:
        if name in wanted:
            continue
        upper = name.upper()
        if upper in wanted:
            hits.append(name)                # wrong case only
            continue
        stem = upper.replace("_", "")
        if stem in {w.replace("_", "") for w in wanted} | {
                "SERPAPIKEY", "SERPAPI", "SEARXURL", "SEARXNGURL",
                "MAGNIFYSEARXURL"}:
            hits.append(name)
    return hits


def backend() -> str | None:
    if searx_url():
        return "searx"
    if serpapi_key():
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
    key = serpapi_key() or ""
    url = ("https://serpapi.com/search.json?" +
           urllib.parse.urlencode({
               "q": query, "engine": "google", "api_key": key, "num": "10"}))
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=20.0) as resp:
        data = json.loads(resp.read().decode("utf-8", "replace"))
    if data.get("error"):
        raise ValueError(f"SerpAPI: {data['error']}")
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
    base = searx_url() or ""
    results: list[dict] = []
    for dork in dorks:
        try:
            if name == "searx":
                hits = _searx(dork, base, per_dork)
            else:
                hits = _serpapi(dork, per_dork)
        except urllib.error.HTTPError as exc:
            detail = ""
            try:
                body = json.loads(exc.read().decode("utf-8", "replace"))
                detail = body.get("error", "")
            except (OSError, ValueError):
                pass
            msg = f"HTTP {exc.code}"
            if exc.code == 401:
                msg += " - check your API key"
            elif exc.code == 429:
                msg += " - rate limit / quota exhausted"
            if detail:
                msg += f" ({detail})"
            results.append({"dork": dork, "error": msg, "hits": []})
            continue
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            results.append({"dork": dork, "error": str(exc), "hits": []})
            continue
        results.append({"dork": dork, "hits": hits})
        time.sleep(delay)  # politeness
    return results
