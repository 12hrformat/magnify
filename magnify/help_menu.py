"""Help content: connection guides for every optional backend.

Kept in one module so the in-tool help always matches the env vars
actually read by search.py / llm.py / emailintel.py.
"""

from __future__ import annotations

import os

from . import search, ui

SEARX_GUIDE = """\
CONNECT A SEARCH BACKEND  (enables dork execution)

  Two options. Pick one:

  ┌─────────────────────────────────────────────────────────────────┐
  │  A. SearXNG      FREE · unlimited · you self-host it            │
  │  B. SerpAPI      paid · 100 free/month · zero setup             │
  └─────────────────────────────────────────────────────────────────┘

  ── OPTION A · SearXNG (free, recommended) ───────────────────────

  SearXNG is a metasearch engine that aggregates Google, Bing, Brave
  and others. Self-hosting means unlimited dork queries, no API key,
  and no dependence on someone else's quota.

  STEP 1 · Start the container

      docker run -d --name searxng -p 8888:8080 \\
        -v searxng-data:/etc/searxng searxng/searxng

      No Docker?  pip install searxng
      Docs:       https://docs.searxng.org

  STEP 2 · Enable the JSON API  (the step everyone misses!)

      SearXNG ships with its JSON API TURNED OFF. Without this you get
      HTTP 403 and magnify looks broken. Enable it by editing the
      settings file INSIDE the container.

      a) Copy it out so you can edit it locally:

           docker cp searxng:/etc/searxng/settings.yml ./settings.yml

      b) Open ./settings.yml in any editor and find the `search:`
         section. Add the `json` line so it looks like this:

             search:
               formats:
                 - html
                 - json          <-- ADD THIS LINE

         Exact command if you prefer no editor:

             sed -i '/^  formats:/a\\    - json' ./settings.yml

      c) Copy it back and restart:

           docker cp ./settings.yml searxng:/etc/searxng/settings.yml
           docker restart searxng

  STEP 3 · Confirm it works

      curl -s 'http://localhost:8888/search?q=test&format=json' | head -c 200

      Good  ->  JSON starting with {"query": ...
      Bad   ->  HTML, an error page, or "format not supported"

  STEP 4 · Connect magnify

      export MAGNIFY_SEARX_URL=http://localhost:8888

      Make it permanent by adding that line to ~/.bashrc (or ~/.zshrc).

  ── OPTION B · SerpAPI (hosted, zero setup) ──────────────────────

  The name is the #1 mistake here. It is SERPAPI_KEY, not SERP_API,
  not SERPAPI, not serpapi.

  STEP 1 · Sign up at https://serpapi.com
           Free tier = 100 searches per month.

  STEP 2 · Copy the key from your dashboard.

  STEP 3 · Export it - note the exact name and CAPITALS:

      export SERPAPI_KEY=your_key_here

      WRONG:  export serpapi=...        (missing _KEY)
      WRONG:  export SERP_API_KEY=...   (misplaced underscore)
      RIGHT:  export SERPAPI_KEY=...

  ── Which one? ───────────────────────────────────────────────────

      SearXNG   free · unlimited · runs on your machine · private
      SerpAPI   costs money past 100/mo · one command to start

  After either, menu [3] will offer to run your dorks automatically.
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
    near = search.near_miss_env()
    if near and not search.backend():
        ui.warn("these look like backend vars but are NOT read (check "
                "the exact name):")
        for name in near:
            ui.warn(f"    {name}")
        print()
    backend = None
    if search.searx_url():
        backend = "SearXNG (" + search.searx_url() + ")"
    elif search.serpapi_key():
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
    """Render a guide with light colorisation.

    Rules (deliberately simple so any guide reads well):
      - step headings / boxed options  -> bold cyan
      - WRONG / misses the point       -> red
      - RIGHT / works                  -> green
      - commands (indented 4+ spaces)  -> bold white-ish
      - everything else                -> plain
    """
    print()
    print(ui.cyan("  ╔" + "═" * 66 + "╗"))
    print(ui.cyan("  ║ ") + ui.bold(f"{title:<64}") + ui.cyan(" ║"))
    print(ui.cyan("  ╚" + "═" * 66 + "╝"))
    for line in body.rstrip().splitlines():
        stripped = line.strip()
        upper = stripped.upper()
        if not stripped:
            print()
        elif upper.startswith(("WRONG", "BAD", "DON'T", "DO NOT")):
            print("  " + ui.red(line))
        elif upper.startswith(("RIGHT", "GOOD")) or "✔" in stripped:
            print("  " + ui.green(line))
        elif upper.startswith("STEP ") or upper.startswith("OPTION "):
            print("  " + ui.bold(ui.cyan(line)))
        elif stripped.startswith("──"):
            print("  " + ui.bold(ui.blue(line)))
        elif line.startswith("    "):
            # indented command lines stand out
            print("  " + ui.cyan(line))
        else:
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
            ui.input(ui.dim("\n  press Enter to continue "))
        except (EOFError, KeyboardInterrupt):
            print()
            return
