# directory-lead-scraper

A small, config-driven Python toolkit for turning public business listing pages into a clean spreadsheet of leads, and for finding a public contact email on each business's own website.

It was built from real freelance work on Australian business directories, then generalized so it is not tied to any single site or client.

## What it does

- **Scrape paginated listings** from a YAML config (CSS selectors, no code changes per site).
- **Resume after interruptions**: finished pages are recorded, so a crashed or stopped run continues where it left off.
- **Remove duplicates** on the columns you choose.
- **Find a public email** on a company's homepage, `/contact` and `/contact-us`, with conservative filtering:
  - placeholder addresses (`john@doe.com`, `email@example.com`) are rejected
  - the address must belong to the company's own domain (or a common free-mail provider)
  - links to Google, Facebook, directories etc. are never treated as a company website
  - addresses are **never guessed or generated**
- **Respect robots.txt** and rate-limit requests.

## Install

Python 3.9+ is recommended.

```bash
python -m venv venv
# Windows (PowerShell):  venv\Scripts\activate
# macOS / Linux:         source venv/bin/activate
pip install -r requirements.txt
```

## Quick start

Scrape the demo config (a sandbox site built for scraping practice):

```bash
python -m leadscraper scrape configs/books_demo.yaml
```

Add public business emails to any CSV that has a `website` column:

```bash
python -m leadscraper enrich leads.csv --output leads_with_email.csv --column website
```

The output reports how many emails were found, for example `Emails found: 118/600`. Coverage depends entirely on what businesses publish; small trades often publish none.

## Writing a config

```yaml
start_url: "https://example.com/listings?page={page}"
first_page: 1
max_pages: 20
item_selector: "div.listing"
fields:
  company:
    selector: "h2 a"
  website:
    selector: "a.visit-website"
    attr: "href"
    absolute: true
dedupe_on: ["company"]
delay_seconds: 1.0
output: "output/leads.csv"
```

See `configs/books_demo.yaml` for a working example.

## Tests

```bash
pytest
```

## Responsible use

- Only collect **publicly available business information**. Do not use this to gather personal data about private individuals.
- Check and follow each website's terms of service and `robots.txt`. The tool checks `robots.txt` automatically but that does not replace reading a site's terms.
- Keep a sensible delay between requests.
- Do not commit scraped data. `output/`, `*.csv` and `*.xlsx` are git-ignored on purpose.

## Limitations

- Static HTML only. Pages that need JavaScript rendering are not supported yet.
- It does not attempt to bypass bot protection or logins.
- Email finding is best-effort; it returns an empty value instead of a guess.

## Roadmap

- Optional headless-browser fetcher for JavaScript-rendered pages
- Excel (`.xlsx`) export
- Optional LLM-assisted category normalization (suggestions flagged for review, never auto-filling missing data)

## License

MIT, see `LICENSE`.
