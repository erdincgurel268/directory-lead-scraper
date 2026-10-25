"""Polite HTTP helpers: robots.txt check, shared headers, simple rate limiting."""
import time
import threading
from typing import Dict
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import requests

USER_AGENT = "leadscraper/0.1 (+https://github.com/erdincgurel268/directory-lead-scraper)"
HEADERS = {"User-Agent": USER_AGENT}

_robots_cache: Dict[str, RobotFileParser] = {}
_lock = threading.Lock()


def allowed_by_robots(url: str, user_agent: str = USER_AGENT) -> bool:
    """Return True if robots.txt allows fetching url (or robots.txt is unavailable)."""
    parsed = urlparse(url)
    root = f"{parsed.scheme}://{parsed.netloc}"
    with _lock:
        parser = _robots_cache.get(root)
        if parser is None:
            parser = RobotFileParser()
            parser.set_url(root + "/robots.txt")
            try:
                resp = requests.get(root + "/robots.txt", headers=HEADERS, timeout=8)
                if resp.status_code == 200:
                    parser.parse(resp.text.splitlines())
                else:
                    parser.parse([])  # no robots.txt -> allow
            except requests.RequestException:
                parser.parse([])
            _robots_cache[root] = parser
    return parser.can_fetch(user_agent, url)


def polite_get(url: str, delay: float = 1.0, timeout: int = 15):
    """GET a URL after checking robots.txt; returns the Response or None."""
    if not allowed_by_robots(url):
        return None
    time.sleep(delay)
    try:
        return requests.get(url, headers=HEADERS, timeout=timeout)
    except requests.RequestException:
        return None
