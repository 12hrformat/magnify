"""Site database for username presence checks.

Each Site entry describes how to test whether a username exists on
that platform. `{u}` in the URL is replaced with the candidate.

Methods:
  status - HTTP missing_status (default 404) means "no account"
  regex  - body matching decides: not_found_regex -> absent,
           found_regex (optional) -> present, otherwise unknown

reliability=False entries are heuristic: platforms that sometimes
block bots or change markup. They still run, but findings are
labeled as unverified in output.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Site:
    name: str
    url: str                      # template, {u} = username
    method: str = "status"        # "status" | "regex"
    missing_status: tuple[int, ...] = (404,)
    found_regex: str | None = None
    not_found_regex: str | None = None
    headers: dict = field(default_factory=dict)
    reliable: bool = True
    notes: str = ""

    def target(self, username: str) -> str:
        return self.url.replace("{u}", username)


# Sites with a browser-like UA get one; everything else uses the
# honest magnify UA (and the README documents this).
_BROWSER_UA = {
    "User-Agent": ("Mozilla/5.0 (X11; Linux x86_64; rv:128.0) "
                   "Gecko/20100101 Firefox/128.0"),
}

SITES: list[Site] = [
    # ---- confirmed, status-based ----
    Site("GitHub", "https://github.com/{u}"),
    Site("GitLab", "https://gitlab.com/{u}"),
    Site("Bitbucket", "https://bitbucket.org/{u}/"),
    Site("Keybase", "https://keybase.io/{u}"),
    Site("HackerRank", "https://www.hackerrank.com/{u}"),
    Site("Devto", "https://dev.to/{u}"),
    Site("NPM", "https://www.npmjs.com/~{u}"),
    Site("PyPI", "https://pypi.org/user/{u}/"),
    Site("DockerHub", "https://hub.docker.com/v2/users/{u}/"),
    Site("CodePen", "https://codepen.io/{u}"),
    Site("Dribbble", "https://dribbble.com/{u}"),
    Site("Behance", "https://www.behance.net/{u}"),
    Site("Medium", "https://medium.com/@{u}"),
    Site("Substack", "https://{u}.substack.com"),
    Site("AboutMe", "https://about.me/{u}"),
    Site("Patreon", "https://www.patreon.com/{u}"),
    Site("Figma", "https://www.figma.com/@{u}"),
    Site("Pinterest", "https://www.pinterest.com/{u}/",
         headers=_BROWSER_UA, reliable=False),
    Site("VK", "https://vk.com/{u}"),
    Site("Duolingo", "https://www.duolingo.com/profile/{u}"),
    Site("Kaggle", "https://www.kaggle.com/{u}"),
    Site("Replit", "https://replit.com/@{u}"),
    Site("ProductHunt", "https://www.producthunt.com/@{u}"),
    Site("SoundCloud", "https://soundcloud.com/{u}"),
    Site("Vimeo", "https://vimeo.com/{u}"),
    Site("Imgur", "https://imgur.com/user/{u}"),
    Site("SlideShare", "https://www.slideshare.net/{u}"),
    Site("Linktree", "https://linktr.ee/{u}"),
    Site("Pastebin", "https://pastebin.com/u/{u}"),
    Site("DeviantArt", "https://www.deviantart.com/{u}"),
    Site("Chesscom", "https://api.chess.com/pub/player/{u}"),
    Site("Lichess", "https://lichess.org/api/user/{u}"),
    Site("HuggingFace", "https://huggingface.co/{u}"),
    Site("Bluesky", "https://public.api.bsky.app/xrpc/"
                    "app.bsky.actor.getProfile?actor={u}.bsky.social"),

    # ---- regex-based ----
    Site("HackerNews", "https://news.ycombinator.com/user?id={u}",
         method="regex", not_found_regex="No such user"),
    Site("Reddit", "https://www.reddit.com/user/{u}/about.json",
         headers=_BROWSER_UA, reliable=False,
         notes="403s anonymous bots frequently"),

    # ---- heuristic / needs verification (from docs/SITES.md) ----
    Site("Steam", "https://steamcommunity.com/id/{u}",
         headers=_BROWSER_UA, reliable=False),
    Site("Mastodon", "https://mastodon.social/@{u}", reliable=False),
    Site("Telegram", "https://t.me/{u}", reliable=False,
         notes="t.me pages vary; treat hits as leads only"),
    Site("Launchpad", "https://launchpad.net/~{u}"),
    Site("SourceForge", "https://sourceforge.net/u/{u}/profile"),
    Site("ArchiveOrg", "https://archive.org/details/@{u}", reliable=False),
    Site("Flickr", "https://www.flickr.com/people/{u}/", reliable=False),
    Site("Wattpad", "https://www.wattpad.com/user/{u}", reliable=False),
    Site("Goodreads", "https://www.goodreads.com/{u}", reliable=False),
    Site("Scribd", "https://www.scribd.com/{u}", reliable=False),
    Site("CashApp", "https://cash.app/${u}", reliable=False,
         notes="redirect heuristics only"),
]

# Sites skipped entirely in v1 (login walls / always-200 SPAs).
# Documented in docs/SITES.md.
SKIPPED = (
    "Instagram", "Twitter/X", "Twitch", "TikTok", "Tumblr",
    "LinkedIn (still used in dork generation)", "Spotify",
)
