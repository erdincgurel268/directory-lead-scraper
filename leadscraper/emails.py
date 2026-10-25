"""Find a business email on a company's own website, with conservative filtering."""
import re
from typing import List
from urllib.parse import urljoin, urlparse

from .net import polite_get

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")

# Strings that mark placeholder / junk addresses.
BAD_PARTS = (
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".css", ".js", "sentry", "wixpress",
    "example.", "yourdomain", "domain.com", "doe.com", "john@", "jane@", "yourname",
    "your-name", "youremail", "email@", "name@", "user@", "test@", "noreply", "no-reply",
    "donotreply", "@mysite", "@company.", "@yourcompany", "u003e", "%20",
)

# Links that are not a company's own website.
SOCIAL_BLOCK = (
    "google.", "facebook.", "instagram.", "linkedin.", "twitter.", "x.com", "youtube.",
    "yelp.", "truelocal.", "hotfrog.", "wix.com", "yellowpages.", "whitepages.",
)

FREE_MAIL = (
    "gmail.com", "yahoo.com", "yahoo.com.au", "outlook.com", "hotmail.com", "bigpond.com",
    "bigpond.net.au", "icloud.com", "live.com", "optusnet.com.au",
)

PREFERRED = (
    ("hr", "career", "recruit", "jobs", "employ"),
    ("info", "admin", "office", "enquir", "contact", "hello", "reception"),
)


def site_root(url: str) -> str:
    host = urlparse(url if url.startswith("http") else "http://" + url).netloc.lower()
    host = host.split(":")[0]
    return host[4:] if host.startswith("www.") else host


def email_matches_site(email: str, root: str) -> bool:
    """Accept the site's own domain (or a subdomain) and common free-mail providers."""
    dom = email.lower().split("@")[-1]
    if dom in FREE_MAIL:
        return True
    if not root:
        return False
    return dom == root or dom.endswith("." + root) or root.endswith("." + dom)


def pick_best_email(emails: List[str], root: str = "") -> str:
    """Choose one address: filter junk, require site match, prefer exact-domain role mailboxes."""
    cleaned = [e.lower() for e in dict.fromkeys(emails)
               if not any(bad in e.lower() for bad in BAD_PARTS)]
    cleaned = [e for e in cleaned if email_matches_site(e, root)]
    exact = [e for e in cleaned if e.split("@")[-1] == root]
    if exact:
        cleaned = exact
    for keys in PREFERRED:
        for e in cleaned:
            if any(k in e.split("@")[0] for k in keys):
                return e
    return cleaned[0] if cleaned else ""


def find_email(url: str, delay: float = 0.5) -> str:
    """Look for a public email on the homepage, /contact and /contact-us.

    Returns an empty string if nothing trustworthy is found. Never guesses addresses.
    """
    if not url or any(b in url.lower() for b in SOCIAL_BLOCK):
        return ""
    if not url.startswith("http"):
        url = "http://" + url
    root = site_root(url)
    found: List[str] = []
    for page in (url, urljoin(url, "/contact"), urljoin(url, "/contact-us")):
        resp = polite_get(page, delay=delay, timeout=8)
        if resp is not None and resp.status_code == 200:
            found.extend(EMAIL_RE.findall(resp.text))
        if pick_best_email(found, root):
            break
    return pick_best_email(found, root)
