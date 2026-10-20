<!-- Logo: drop your image at assets/logo.png (or .svg) and update the
     filename below to match. Relative paths work on GitHub and PyPI. -->
<p align="center">
  <img src="assets/logo.png" alt="magnify" width="420">
</p>

# magnify

Interactive OSINT orchestrator for authorized reconnaissance. One
command, one menu, one report.

```
name / email / handle / website domain
   │
   ├─► email intelligence   MX · SPF · DMARC · provider · gravatar · disposable
   ├─► username hunt        name → 40 variants → sweep across ~45 sites
   ├─► dork workshop        interactive filetype/site/modifier tables
   │      └─► optional execution via your SearXNG or SerpAPI key
   └─► AI pivots            any OpenAI-compatible endpoint (local Ollama ok)
              │
              ▼
       report.md + report.json
```

**Authorized use only.** magnify helps you investigate *your own*
identities, your org's exposed footprint, or targets you have written
permission to test. Every network probe is a plain anonymous HTTP GET —
no exploitation, no brute force, no authentication attacks.

## Install

```sh
pip install .
magnify
```

Or straight from the repo without installing:

```sh
python3 -m magnify
```

Zero runtime dependencies — Python 3.10+ standard library only.

## Usage

### Interactive (the intended way)

```sh
$ magnify
   ▄▄▄▄███▄▄▄▄      ▄████████    ▄██████▄  ███▄▄▄▄    ▄█     ▄████████ ▄██   ▄
 ▄██▀▀▀███▀▀▀██▄   ███    ███   ███    ███ ███▀▀▀██▄ ███    ███    ███ ███   ██▄
 ███   ███   ███   ███    ███   ███    █▀  ███   ███ ███▌   ███    █▀  ███▄▄▄███
 ███   ███   ███   ███    ███  ▄███        ███   ███ ███▌  ▄███▄▄▄     ▀▀▀▀▀▀███
 ███   ███   ███ ▀███████████ ▀▀███ ████▄  ███   ███ ███▌ ▀▀███▀▀▀     ▄██   ███
 ███   ███   ███   ███    ███   ███    ███ ███   ███ ███    ███        ███   ███
 ███   ███   ███   ███    ███   ███    ███ ███   ███ ███    ███        ███   ███
  ▀█   ███   █▀    ███    █▀    ████████▀   ▀█   █▀  █▀     ███         ▀█████▀

  interactive OSINT orchestrator  |  authorized use only

full name []: Joe Mama
email (separated by spaces, if multiple) []: joe@example.com joe.mama@work.com
known username/handle []: joemama
website domain (if they have one) []:

┌─ magnify v0.1.0  —  name=Joe Mama  email=joe@example.com
│ [1] email lookup
│ [2] username hunt (name -> variants -> sweep)
│ [3] dork workshop (interactive table)
│ [4] AI pivot suggestions
│ [5] save report
│ [6] edit target
│ [q] quit
└────────────────────────────────────────────────────
```

### Scripted / non-interactive

```sh
magnify --name "Joe Mama" --email joe@example.com \
        --sweep --dorks --save joe-report --no-color
```

Multiple emails work in both modes — space- or comma-separated in the
prompt, or repeat the flag:

```sh
magnify --email joe@example.com --email joe.mama@work.com --dorks
```

## Target fields

| Field | Used for |
|---|---|
| `name` | username-variant generation and name-based dorks |
| `email` | email intelligence (MX/SPF/DMARC) and leak dorks. **Multiple allowed** — each address gets its own lookup and its own leak battery |
| `username` | a known handle, checked directly against every site |
| `website domain (if they have one)` | site-scoped infrastructure dorks (`site:example.com intitle:"index of"`). Only used if you set it — an email never leaks into this field |

## Configuration (all optional, all environment variables)

| Variable | Purpose |
|---|---|
| `MAGNIFY_SEARX_URL` | your SearXNG instance → dork workshop can execute queries |
| `SERPAPI_KEY` | SerpAPI alternative for dork execution |
| `MAGNIFY_LLM_URL` | OpenAI-compatible base URL (`http://localhost:11434/v1` for Ollama) |
| `MAGNIFY_LLM_MODEL` | model name (default `llama3.1`) |
| `MAGNIFY_LLM_KEY` | optional API key for the above |
| `HIBP_API_KEY` | optional Have I Been Pwned breach lookup |
| `EMAILREP_API_KEY` | optional emailrep.io reputation lookup |
| `NO_COLOR` | disable ANSI colors |

magnify does **not** scrape Google. Dork execution happens only through
backends you configure yourself, and the AI module sends data only to
the endpoint you point it at (a local LLM keeps everything local).

## Site list

See [docs/SITES.md](docs/SITES.md) for the full checked-sites table,
detection methods, and reliability flags. Add new sites by appending a
`Site(...)` entry in `magnify/sites.py`.

## Tests

```sh
python3 -m unittest discover -s tests -v
```

The suite is fully offline (it spins up a local HTTP server to test the
sweep engine).

## Naming note

This project may collide with other things called "magnify". If the
BlackArch maintainers prefer another name at packaging time, rename
freely — the code doesn't care.

## License

MIT — see [LICENSE](LICENSE).
