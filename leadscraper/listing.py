"""Config-driven scraper for paginated listing pages (static HTML)."""
import os
from typing import Any, Dict, List
from urllib.parse import urljoin

import pandas as pd
import yaml
from bs4 import BeautifulSoup

from .net import polite_get


def load_config(path: str) -> Dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    for key in ("start_url", "item_selector", "fields", "output"):
        if key not in cfg:
            raise ValueError(f"config is missing required key: {key}")
    cfg.setdefault("first_page", 1)
    cfg.setdefault("max_pages", 1)
    cfg.setdefault("delay_seconds", 1.0)
    cfg.setdefault("dedupe_on", [])
    cfg.setdefault("static", {})
    return cfg


def extract_items(html, cfg: Dict[str, Any], base_url: str) -> List[Dict[str, str]]:
    """Pull one dict per item from a page using CSS selectors from the config.

    html may be str or bytes; bytes let BeautifulSoup detect the page encoding.
    """
    soup = BeautifulSoup(html, "html.parser")
    rows: List[Dict[str, str]] = []
    for node in soup.select(cfg["item_selector"]):
        row: Dict[str, str] = dict(cfg["static"])
        for name, spec in cfg["fields"].items():
            target = node.select_one(spec["selector"])
            value = ""
            if target is not None:
                if spec.get("attr"):
                    value = target.get(spec["attr"], "") or ""
                else:
                    value = target.get_text(" ", strip=True)
                if spec.get("absolute") and value:
                    value = urljoin(base_url, value)
            row[name] = value.strip()
        rows.append(row)
    return rows


def _read_done(path: str) -> set:
    if not os.path.exists(path):
        return set()
    with open(path, encoding="utf-8") as f:
        return {line.strip() for line in f if line.strip()}


def scrape(cfg: Dict[str, Any]) -> pd.DataFrame:
    """Scrape all configured pages. Progress is saved, so an interrupted run resumes."""
    output = cfg["output"]
    os.makedirs(os.path.dirname(output) or ".", exist_ok=True)
    raw_path = output + ".raw.csv"
    done_path = output + ".done"
    done = _read_done(done_path)

    last = cfg["first_page"] + cfg["max_pages"] - 1
    for page in range(cfg["first_page"], last + 1):
        if str(page) in done:
            continue
        url = cfg["start_url"].format(page=page)
        resp = polite_get(url, delay=cfg["delay_seconds"])
        if resp is None or resp.status_code != 200:
            print(f"page {page}: skipped (blocked by robots.txt or request failed)")
            continue
        rows = extract_items(resp.content, cfg, url)
        if not rows:
            print(f"page {page}: no items found, stopping")
            break
        pd.DataFrame(rows).to_csv(raw_path, mode="a", header=not os.path.exists(raw_path),
                                  index=False, encoding="utf-8-sig")
        with open(done_path, "a", encoding="utf-8") as f:
            f.write(str(page) + "\n")
        print(f"page {page}: {len(rows)} items")

    if not os.path.exists(raw_path):
        return pd.DataFrame()
    df = pd.read_csv(raw_path, dtype=str).fillna("")
    if cfg["dedupe_on"]:
        df = df.drop_duplicates(subset=cfg["dedupe_on"])
    return df.reset_index(drop=True)
