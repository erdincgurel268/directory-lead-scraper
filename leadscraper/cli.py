"""Command line interface: scrape a listing, or enrich a CSV with public business emails."""
import argparse
from concurrent.futures import ThreadPoolExecutor

import pandas as pd

from .emails import find_email
from .listing import load_config, scrape


def cmd_scrape(args) -> None:
    cfg = load_config(args.config)
    df = scrape(cfg)
    if df.empty:
        print("No rows collected.")
        return
    df.to_csv(cfg["output"], index=False, encoding="utf-8-sig")
    print(f"Saved {len(df)} rows to {cfg['output']}")


def cmd_enrich(args) -> None:
    df = pd.read_csv(args.input, dtype=str).fillna("")
    if args.column not in df.columns:
        raise SystemExit(f"column '{args.column}' not found in {args.input}")
    sites = df[args.column].tolist()
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        df["email"] = list(pool.map(find_email, sites))
    df.to_csv(args.output, index=False, encoding="utf-8-sig")
    found = int((df["email"] != "").sum())
    print(f"Saved {args.output}. Emails found: {found}/{len(df)}")


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(prog="leadscraper")
    sub = parser.add_subparsers(dest="command", required=True)

    p_scrape = sub.add_parser("scrape", help="scrape a paginated listing from a YAML config")
    p_scrape.add_argument("config")
    p_scrape.set_defaults(func=cmd_scrape)

    p_enrich = sub.add_parser("enrich", help="add public business emails to a CSV with a website column")
    p_enrich.add_argument("input")
    p_enrich.add_argument("--output", default="enriched.csv")
    p_enrich.add_argument("--column", default="website")
    p_enrich.add_argument("--workers", type=int, default=4)
    p_enrich.set_defaults(func=cmd_enrich)

    args = parser.parse_args(argv)
    args.func(args)
