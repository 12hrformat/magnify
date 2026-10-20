"""Email intelligence: syntax, DNS (MX/SPF/DMARC), provider mapping,
gravatar presence, disposable-domain detection, and optional breach
lookups (only when the user provides an API key)."""

from __future__ import annotations

import hashlib
import json
import os
import re
import urllib.request

from . import dns_query

EMAIL_RE = re.compile(
    r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")

DISPOSABLE_DOMAINS = {
    "mailinator.com", "guerrillamail.com", "10minutemail.com", "tempmail.com",
    "temp-mail.org", "yopmail.com", "trashmail.com", "sharklasers.com",
    "getairmail.com", "mailnesia.com", "maildrop.cc", "discard.email",
    "tempail.com", "tempr.email", "mohmal.com", "fakeinbox.com",
    "throwawaymail.com", "getnada.com", "emailondeck.com", "minutemail.com",
    "33mail.com", "mytemp.email", "linshiyouxiang.net", "mailcatch.com",
}

PROVIDER_MAP = {
    "gmail.com": "Google Gmail",
    "googlemail.com": "Google Gmail",
    "outlook.com": "Microsoft Outlook / 365",
    "hotmail.com": "Microsoft Outlook / 365",
    "live.com": "Microsoft Outlook / 365",
    "msn.com": "Microsoft Outlook / 365",
    "yahoo.com": "Yahoo Mail",
    "yahoo.co.uk": "Yahoo Mail",
    "proton.me": "Proton Mail",
    "protonmail.com": "Proton Mail",
    "pm.me": "Proton Mail",
    "icloud.com": "Apple iCloud",
    "me.com": "Apple iCloud",
    "aol.com": "AOL Mail",
    "gmx.com": "GMX",
    "gmx.de": "GMX",
    "mail.com": "Mail.com",
    "zoho.com": "Zoho Mail",
    "zohomail.com": "Zoho Mail",
    "fastmail.com": "Fastmail",
    "hey.com": "HEY",
    "tutanota.com": "Tutanota",
    "tuta.io": "Tutanota",
    "yandex.com": "Yandex Mail",
    "mail.ru": "Mail.ru",
}

# MX hostname fragments -> provider
MX_PROVIDER_MAP = {
    "google.com": "Google Workspace",
    "googlemail.com": "Google Workspace",
    "outlook.com": "Microsoft 365",
    "protection.outlook.com": "Microsoft 365",
    "pphosted.com": "Proofpoint",
    "mimecast": "Mimecast",
    "secureserver.net": "GoDaddy",
    "zoho.com": "Zoho",
    "zoho.eu": "Zoho",
    "fastmail.com": "Fastmail",
    "mail.protonmail.ch": "Proton Mail",
    "protonmail.ch": "Proton Mail",
    "mx.yandex.ru": "Yandex for Business",
    "barracudanetworks.com": "Barracuda",
    "messagelabs.com": "MessageLabs",
}


def valid_syntax(email: str) -> bool:
    return bool(EMAIL_RE.match(email))


def _http_json(url: str, headers: dict, timeout: float = 10.0) -> dict | None:
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8", "replace"))
    except Exception:
        return None


def _gravatar_exists(email: str) -> bool | None:
    digest = hashlib.md5(email.strip().lower().encode()).hexdigest()
    url = f"https://en.gravatar.com/{digest}.json"
    req = urllib.request.Request(url, headers={"User-Agent": "magnify/0.1"})
    try:
        with urllib.request.urlopen(req, timeout=8.0) as resp:
            return resp.status == 200
    except urllib.error.HTTPError as exc:  # noqa: F841
        return False
    except OSError:
        return None


def _hibp_breaches(email: str) -> list[str] | None:
    key = os.environ.get("HIBP_API_KEY")
    if not key:
        return None
    url = ("https://haveibeenpwned.com/api/v3/breachedaccount/"
           f"{email}?truncateResponse=false")
    req = urllib.request.Request(url, headers={
        "hibp-api-key": key, "User-Agent": "magnify/0.1"})
    try:
        with urllib.request.urlopen(req, timeout=12.0) as resp:
            data = json.loads(resp.read().decode("utf-8", "replace"))
            return [item.get("Name", "?") for item in data]
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return []  # clean
        return None
    except OSError:
        return None


def _emailrep(email: str) -> dict | None:
    key = os.environ.get("EMAILREP_API_KEY")
    if not key:
        return None
    return _http_json(
        f"https://emailrep.io/{email}",
        {"User-Agent": "magnify/0.1", "Key": key})


def lookup(email: str) -> dict:
    """Run the full email intel chain. Returns a findings dict."""
    findings: dict = {"email": email}
    if not valid_syntax(email):
        findings["error"] = "invalid email syntax"
        return findings

    domain = email.rsplit("@", 1)[1].lower()
    local = email.rsplit("@", 1)[0].lower()
    findings["domain"] = domain
    findings["local_part"] = local

    if "." not in local and len(local) <= 3:
        findings["possible_alias"] = (
            "very short local part - could be an alias or shared mailbox")

    findings["provider_by_domain"] = PROVIDER_MAP.get(domain)
    findings["disposable"] = domain in DISPOSABLE_DOMAINS

    # ---- DNS ----
    try:
        mx = dns_query.mx_records(domain)
        findings["mx"] = [{"priority": p, "host": h} for p, h in mx]
    except OSError as exc:
        findings["mx"] = []
        findings["mx_error"] = str(exc)

    mx_hosts = [h.lower() for _, h in findings.get("mx", [])]
    for frag, provider in MX_PROVIDER_MAP.items():
        if any(frag in h for h in mx_hosts):
            findings["provider_by_mx"] = provider
            break

    try:
        txts = dns_query.txt_records(domain)
        findings["spf"] = next((t for t in txts if t.lower().startswith("v=spf1")), None)
    except OSError:
        findings["spf"] = None

    try:
        dmarc_txts = dns_query.txt_records(f"_dmarc.{domain}")
        findings["dmarc"] = next(
            (t for t in dmarc_txts if t.lower().startswith("v=dmarc1")), None)
    except OSError:
        findings["dmarc"] = None

    if not mx and not findings.get("mx_error"):
        findings["warning"] = "no MX records - domain may not accept mail"

    # ---- weak signals ----
    findings["gravatar"] = _gravatar_exists(email)

    # ---- optional keyed services (never runs without user's key) ----
    breaches = _hibp_breaches(email)
    if breaches is not None:
        findings["hibp_breaches"] = breaches
    rep = _emailrep(email)
    if rep is not None:
        findings["emailrep"] = rep

    return findings


def summarize(findings: dict) -> list[str]:
    """Human-readable bullet lines for the report/terminal."""
    lines = []
    if findings.get("error"):
        return [f"error: {findings['error']}"]
    if findings.get("provider_by_domain"):
        lines.append(f"consumer provider: {findings['provider_by_domain']}")
    if findings.get("provider_by_mx"):
        lines.append(f"mail host: {findings['provider_by_mx']}")
    elif findings.get("mx"):
        hosts = ", ".join(m["host"] for m in findings["mx"][:3])
        lines.append(f"MX: {hosts}")
    else:
        lines.append("no MX records found")
    if findings.get("disposable"):
        lines.append("WARNING: disposable/throwaway provider")
    lines.append(f"SPF: {'present' if findings.get('spf') else 'missing'}")
    lines.append(f"DMARC: {'present' if findings.get('dmarc') else 'missing'}")
    grav = findings.get("gravatar")
    if grav is True:
        lines.append("gravatar profile exists (weak identity signal)")
    elif grav is False:
        lines.append("no gravatar profile")
    if "hibp_breaches" in findings:
        count = len(findings["hibp_breaches"])
        lines.append(f"HIBP breaches: {count}"
                     + (f" ({', '.join(findings['hibp_breaches'][:5])})"
                        if count else ""))
    if findings.get("possible_alias"):
        lines.append(f"note: {findings['possible_alias']}")
    return lines
