"""Dork battery generation.

Builds Google/Bing-style dorks from the session target and interactive
table selections. Execution is NOT done against Google directly;
dorks are handed to a user-configured SearXNG instance or SerpAPI
(see search.py) or simply listed for manual use.
"""

from __future__ import annotations

from dataclasses import dataclass, field

FILETYPES = [
    "pdf", "docx", "doc", "xlsx", "xls", "csv", "txt", "sql",
    "json", "xml", "env", "log", "key", "pem", "p12", "bak",
]

SITE_TABLE = [
    ("linkedin.com/in", '"{name}" site:linkedin.com/in'),
    ("twitter / x.com", '"{name}" (site:twitter.com OR site:x.com) "{name}"'),
    ("github.com", '"{email}" site:github.com'),
    ("facebook.com", '"{name}" site:facebook.com'),
    ("instagram.com", '"{name}" site:instagram.com'),
    ("about.me", '"{name}" site:about.me'),
    ("medium.com", '"{name}" site:medium.com'),
    ("keybase.io", '"{username}" site:keybase.io'),
    ("pypi.org", '"{email}" site:pypi.org'),
    ("npmjs.com", '"{email}" site:npmjs.com'),
    ("pastebin.com", '"{email}" site:pastebin.com'),
    ("reddit.com", '"{username}" site:reddit.com'),
    ("edu (academic)", '"{name}" site:edu filetype:pdf'),
    ("gov", '"{name}" site:gov'),
    ("news / press", '"{name}" (intext:founder OR intext:CEO OR intext:analyst)'),
    ("youtube", '"{name}" site:youtube.com'),
    ("tiktok", '"{name}" site:tiktok.com'),
]

MODIFIERS = [
    ("exact phrase", True),           # default on
    ("exclude linkedin noise", False),
    ("intitle:index of", False),
    ("intext:password", False),
    ("filetype:pdf (all sites)", False),
]

LEAK_PATTERNS = [
    '"{email}" password',
    '"{email}" (filetype:txt OR filetype:csv OR filetype:sql)',
    '"{email}" (filetype:env OR filetype:log OR filetype:bak)',
    '"{email}" (inurl:paste OR inurl:dump)',
    '"{local}" "{email_domain}" (confidential OR internal)',
]


@dataclass
class DorkConfig:
    filetypes: list[str] = field(default_factory=list)
    sites: list[str] = field(default_factory=list)     # labels from SITE_TABLE
    modifiers: list[str] = field(default_factory=list) # modifier labels
    include_leaks: bool = True


def _ctx(target) -> dict[str, str]:
    name = target.name or target.username or ""
    emails = list(getattr(target, "emails", []) or [])
    if not emails and target.email:
        emails = [target.email]
    email = target.email or (emails[0] if emails else "")
    local, _, domain = email.partition("@") if email else ("", "", "")
    username = target.username or (local if local else "")
    # `domain` is for *website* recon (index-of, admin panels). Never
    # fall back to a free-mail provider from the email address - dorking
    # gmail.com/outlook.com is meaningless and noisy.
    site_domain = target.domain
    return {
        "name": name,
        "email": email,
        "emails": emails,
        "username": username,
        "local": local,
        "domain": site_domain,
        "email_domain": domain,
    }


def build(target, config: DorkConfig) -> list[str]:
    """Generate the final de-duplicated dork battery."""
    ctx = _ctx(target)
    if not any(ctx.values()):
        return []

    phrase = f'"{ctx["name"]}"' if ctx["name"] else ""
    dorks: list[str] = []

    def add(template: str, extra: dict[str, str] | None = None) -> None:
        values = ctx if extra is None else {**ctx, **extra}
        try:
            rendered = template.format(**values)
        except KeyError:
            return
        rendered = " ".join(rendered.split())
        if rendered and rendered not in dorks:
            dorks.append(rendered)

    # site-table picks
    for label in config.sites:
        for tmpl_label, tmpl in SITE_TABLE:
            if tmpl_label == label:
                add(tmpl)

    # filetype battery, anchored on the name or username
    anchor = phrase or f'"{ctx["username"]}"'
    exclude = (" -site:facebook.com -site:instagram.com"
               if "exclude linkedin noise" in config.modifiers else "")
    for ft in config.filetypes:
        add(f"{anchor} filetype:{ft}{exclude}")

    # modifiers
    if "intitle:index of" in config.modifiers and ctx["domain"]:
        add(f'site:{ctx["domain"]} intitle:"index of"')
        add(f'site:{ctx["domain"]} inurl:admin OR inurl:backup')
    if "intext:password" in config.modifiers:
        add(f"{anchor} intext:password{exclude}")
        add(f'{anchor} "login" "password" filetype:txt')
    if "filetype:pdf (all sites)" in config.modifiers and phrase:
        add(f"{phrase} filetype:pdf (site:edu OR site:gov OR site:org)")

    # email leak / breach recon battery - once per address
    if config.include_leaks:
        for addr in ctx["emails"]:
            addr_local, _, addr_domain = addr.partition("@")
            extra = {
                "email": addr,
                "local": addr_local,
                "email_domain": addr_domain,
            }
            for tmpl in LEAK_PATTERNS:
                add(tmpl, extra)

    # domain recon if a domain is set
    if ctx["domain"]:
        add(f'site:{ctx["domain"]} ext:php | ext:html | ext:aspx')
        add(f'site:{ctx["domain"]} inurl:login | inurl:admin')

    return dorks
