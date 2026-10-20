# magnify — site database reference

Every site magnify checks in the username sweep. `{u}` is the username
variant under test.

## Detection methods

- **status**: HTTP 404 (or similar) = account does not exist
- **regex**: site always answers 200, so we match/exclude body patterns
- **reliability**: how stable this check is over time (sites change!)

## Confirmed (high confidence)

| # | Site | User URL | Method | Notes |
|---|------|----------|--------|-------|
| 1 | GitHub | `https://github.com/{u}` | status 404 | rock solid |
| 2 | GitLab | `https://gitlab.com/{u}` | status 404 | rock solid |
| 3 | Bitbucket | `https://bitbucket.org/{u}/` | status 404 | |
| 4 | Keybase | `https://keybase.io/{u}` | status 404 | |
| 5 | HackerRank | `https://www.hackerrank.com/{u}` | status 404 | |
| 6 | dev.to | `https://dev.to/{u}` | status 404 | |
| 7 | npm | `https://www.npmjs.com/~{u}` | status 404 | note the `~` |
| 8 | PyPI | `https://pypi.org/user/{u}/` | status 404 | trailing slash |
| 9 | Docker Hub | `https://hub.docker.com/v2/users/{u}/` | status 404 | JSON API, no login wall |
| 10 | CodePen | `https://codepen.io/{u}` | status 404 | |
| 11 | Dribbble | `https://dribbble.com/{u}` | status 404 | |
| 12 | Behance | `https://www.behance.net/{u}` | status 404 | |
| 13 | Medium | `https://medium.com/@{u}` | status 404 | note the `@` |
| 14 | Substack | `https://{u}.substack.com` | status 404 | subdomain style |
| 15 | about.me | `https://about.me/{u}` | status 404 | |
| 16 | Patreon | `https://www.patreon.com/{u}` | status 404 | |
| 17 | Figma | `https://www.figma.com/@{u}` | status 404 | |
| 18 | Pinterest | `https://www.pinterest.com/{u}/` | status 404 | |
| 19 | VK | `https://vk.com/{u}` | status 404 | |
| 20 | Duolingo | `https://www.duolingo.com/profile/{u}` | status 404 | |
| 21 | Kaggle | `https://www.kaggle.com/{u}` | status 404 | |
| 22 | Replit | `https://replit.com/@{u}` | status 404 | |
| 23 | Product Hunt | `https://www.producthunt.com/@{u}` | status 404 | |
| 24 | SoundCloud | `https://soundcloud.com/{u}` | status 404 | |
| 25 | Vimeo | `https://vimeo.com/{u}` | status 404 | |
| 26 | Imgur | `https://imgur.com/user/{u}` | status 404 | |
| 27 | SlideShare | `https://www.slideshare.net/{u}` | status 404 | |
| 28 | Linktree | `https://linktr.ee/{u}` | status 404 | |
| 29 | Pastebin | `https://pastebin.com/u/{u}` | status 404 | |
| 30 | DeviantArt | `https://www.deviantart.com/{u}` | status 404 | |
| 31 | Chess.com | `https://api.chess.com/pub/player/{u}` | status 404 | JSON API |
| 32 | Lichess | `https://lichess.org/api/user/{u}` | status 404 | JSON API |
| 33 | Hugging Face | `https://huggingface.co/{u}` | status 404 | |
| 34 | Hacker News | `https://news.ycombinator.com/user?id={u}` | regex | body contains "No such user" |
| 35 | Reddit | `https://www.reddit.com/user/{u}` | status 404 | often 403s bots; tolerate |

## Needs verification (ask ChatGPT / test manually)

| # | Site | User URL | Question to verify |
|---|------|----------|--------------------|
| 36 | Steam | `https://steamcommunity.com/id/{u}` | does a missing custom URL return 404? |
| 37 | Roblox | `https://www.roblox.com/users/profile?username={u}` | does this endpoint still work for lookup? |
| 38 | Mastodon (mastodon.social) | `https://mastodon.social/@{u}` | 404 for missing users? |
| 39 | Bluesky | `https://public.api.bsky.app/xrpc/app.bsky.actor.getProfile?actor={u}.bsky.social` | 404 JSON for missing handle? |
| 40 | Telegram | `https://t.me/{u}` | does a missing user show a distinguishable body text? |
| 41 | Launchpad | `https://launchpad.net/~{u}` | 404 for missing? |
| 42 | SourceForge | `https://sourceforge.net/u/{u}/profile` | 404 for missing? |
| 43 | Archive.org | `https://archive.org/details/@{u}` | 404 for missing? |
| 44 | Flickr | `https://www.flickr.com/people/{u}/` | 404 for missing? |
| 45 | Wattpad | `https://www.wattpad.com/user/{u}` | 404 for missing? |
| 46 | Goodreads | `https://www.goodreads.com/{u}` | 404 for missing? |
| 47 | Quora | `https://www.quora.com/profile/{u}` | 404 or login wall? |
| 48 | Scribd | `https://www.scribd.com/{u}` | 404 for missing? |
| 49 | 9GAG | `https://9gag.com/u/{u}` | 404 for missing? |
| 50 | Cash App | `https://cash.app/${u}` | 404 for missing? |

## Known-unreliable / skipped in v1

| Site | Why skipped |
|------|-------------|
| Instagram | login wall for anonymous requests |
| Twitter / X | auth wall, 302 to login |
| Twitch | SPA always returns 200 |
| TikTok | often 200 for missing users |
| Tumblr | placeholder page, always 200 |
| LinkedIn | aggressive bot blocking (still used in *dorks*) |
| Spotify | no public profile by username |

## What to ask ChatGPT (per site)

> "I'm building a username-existence checker. For SITE, what is the public
> profile URL pattern for a username, and what HTTP status or body marker
> does a *nonexistent* username return to an anonymous request (no login,
> normal browser user-agent)?"

## Adding a site

Edit `magnify/sites.py` and append a `Site(...)` entry — no other code
changes needed.
