"""Help content: connection guides for every optional backend.

Kept in one module so the in-tool help always matches the env vars
actually read by search.py / llm.py / emailintel.py.
"""

from __future__ import annotations

import os

from . import ui

SEARX_GUIDE = """\
CONNECT A SEARCH BACKEND  (enables dork execution)

Option A - SearXNG (free, self-hosted, recommended)

  SearXNG is a metasearch engine that aggregates Google/Bing/Brave/etc.
  Running your own instance means unlimited dork queries with no API key
  and no rate limit on someone else's quota.

  1. docker run -d --name searxng -p 8888:8080 \\
       -v searxng-data:/etc/searxng searxng/searxng

     (no docker? pip install searxng, or see https://docs.searxng.org)

  2. SearXNG ships with the JSON API DISABLED. You must turn it on.
     Edit the container's settings.yml and make sure this block exists:

       search:
         formats:
           - html
           - json          <-- add this line

     Docker one-liner to append it:
       docker exec searxng sh -c \\
         "sed -i 's/^  formats:/  formats:\\n    - json/' /etc/searxng/settings.yml"

     then: docker restart searxng

  3. Verify the JSON API works:
       curl -s 'http://localhost:8888/search?q=test&format=json' | head -c 200

  4. Point magnify at it (in this shell, or add to ~/.bashrc):

       export MAGNIFY_SEARX_URL=http://localhost:8888

Option B - SerpAPI (hosted, paid, zero setup)

  1. Sign up at https://serpapi.com  (free tier = 100 searches/month)
  2. Copy your key from the dashboard
  3. export SERPAPI_KEY=your_key_here

Which one?
  SearXNG  - free, unlimited, you run it, works offline from 3rd parties
  SerpAPI  - costs money past the free tier, but one command to start

After either: menu [3] dork workshop will offer to execute your dorks.
"""

LLM_GUIDE = """\
CONNECT AN AI BACKEND  (enables pivot suggestions)

Any OpenAI-compatible /chat/completions endpoint works.

Option A - Ollama (free, local, private, recommended)

  1. Install:      curl -fsSL https://ollama.com/install.sh | sh
  2. Pull a model: ollama pull llama3.1
                   (or qwen2.5, mistral, phi3 - smaller = faster)
  3. Ollama serves an OpenAI-compatible API on port 11434 already.
  4. export MAGNIFY_LLM_URL=http://localhost:11434/v1
     export MAGNIFY_LLM_MODEL=llama3.1

Option B - any OpenAI-compatible host

  export MAGNIFY_LLM_URL=https://api.openai.com/v1
  export MAGNIFY_LLM_KEY=sk-...
  export MAGNIFY_LLM_MODEL=gpt-4o-mini

  Same 3 vars work for OpenRouter, Groq, Together, vLLM, LM Studio,
  llama.cpp server, etc.

Privacy note: your findings JSON is sent only to the URL you set.
With Ollama, nothing ever leaves your machine.

After either: menu [4] AI pivot will summarize findings and suggest
next steps plus extra dorks.
"""

EMAIL_GUIDE = """\
CONNECT EMAIL INTELLIGENCE BACKENDS  (both optional)

The core email checks (MX, SPF, DMARC, provider, gravatar, disposable)
need NO keys and work out of the box.

Optional extras:

  Have I Been Pwned  - breach history for an address
    1. Get a key: https://haveibeenpwned.com/API/Key
       (one-time ~$3.95 purchase)
    2. export HIBP_API_KEY=your_key_here

  emailrep.io  - reputation scoring
    1. Free key: https://emailrep.io/free
    2. export EMAILREP_API_KEY=your_key_here

Magnify detects the key and adds the lookup automatically - no other
configuration needed.
"""

LEGAL = """\
AUTHORIZED USE ONLY

magnify performs plain, anonymous HTTP GETs - no exploitation, no
brute forcing, no auth attacks. That does not make it legal to point
at anyone.

Use it for:
  - your own identities and accounts
  - your organisation's exposure (with permission)
  - engagements where you have written authorization
  - CTF / lab environments

Do NOT use it to stalk, harass, dox, or profile people without
consent. Aggregating scattered public data into one profile is exactly
what makes this powerful - and exactly why misuse is harmful.

Every hit should be verified manually before you act on it.
"""

ENV_VARS = [
    ("MAGNIFY_SEARX_URL", "SearXNG base URL - enables dork execution"),
    ("SERPAPI_KEY", "SerpAPI key - alternative dork backend"),
    ("MAGNIFY_LLM_URL", "OpenAI-compatible base URL - enables AI pivots"),
    ("MAGNIFY_LLM_MODEL", "model name (default: llama3.1)"),
    ("MAGNIFY_LLM_KEY", "API key for the LLM endpoint, if required"),
    ("HIBP_API_KEY", "Have I Been Pwned breach lookups"),
    ("EMAILREP_API_KEY", "emailrep.io reputation lookups"),
    ("NO_COLOR", "disable ANSI colors"),
]


def _status(name: str) -> str:
    return ui.green("set") if os.environ.get(name) else ui.dim("not set")


def show_status() -> None:
    """Live table of what is currently connected."""
    print(ui.bold("\n  current backend status"))
    for var, desc in ENV_VARS:
        print(f"    {ui.cyan(var):<28} {_status(var):<14} {ui.dim(desc)}")
    print()
    backend = None
    if os.environ.get("MAGNIFY_SEARX_URL"):
        backend = "SearXNG (" + os.environ["MAGNIFY_SEARX_URL"] + ")"
    elif os.environ.get("SERPAPI_KEY"):
        backend = "SerpAPI"
    if backend:
        ui.ok(f"dork execution: ready via {backend}")
    else:
        ui.warn("dork execution: not connected (dorks will be listed only)")
    if os.environ.get("MAGNIFY_LLM_URL"):
        ui.ok(f"AI pivots: ready via {os.environ['MAGNIFY_LLM_URL']}")
    else:
        ui.warn("AI pivots: not connected")
    print()


def _section(title: str, body: str) -> None:
    print(ui.bold(ui.cyan(f"\n  === {title} ===")))
    for line in body.rstrip().splitlines():
        print("  " + line)


def menu() -> None:
    """Interactive help menu."""
    items = [
        ("1", "connect a search backend (for google dorking)"),
        ("2", "connect an AI backend (pivot suggestions)"),
        ("3", "connect email intel backends (HIBP / emailrep)"),
        ("4", "show what is currently connected"),
        ("5", "legal / authorized use"),
        ("6", "all of the above"),
        ("b", "back"),
    ]
    while True:
        choice = ui.menu("help", items)
        if choice == "1":
            _section("connect a search backend", SEARX_GUIDE)
        elif choice == "2":
            _section("connect an AI backend", LLM_GUIDE)
        elif choice == "3":
            _section("connect email backends", EMAIL_GUIDE)
        elif choice == "4":
            show_status()
        elif choice == "5":
            _section("authorized use only", LEGAL)
        elif choice == "6":
            _section("connect a search backend", SEARX_GUIDE)
            _section("connect an AI backend", LLM_GUIDE)
            _section("connect email backends", EMAIL_GUIDE)
            _section("authorized use only", LEGAL)
            show_status()
        else:
            return
        try:
            input(ui.dim("\n  press Enter to continue "))
        except (EOFError, KeyboardInterrupt):
            print()
            return
