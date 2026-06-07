"""
Stage 0 — Fetch raw documents for The Unofficial Guide (MDC off-campus housing).

This script does ONE thing: download the raw content of each source in
planning.md's Documents table and save it, unmodified, to documents/raw/ in a
consistent format (one .html file per source). It does NOT clean or chunk —
that is ingest.py's job. Keeping raw and cleaned stages separate means you can
re-clean without re-downloading, and you can inspect exactly what each site
returned.

Usage:
    python documents/fetch_sources.py

Some sites block automated requests (e.g. apartments.com returns 403, Reddit
serves a challenge page). For those, the script tells you to save the page
manually: open the URL in your browser, File -> Save Page As -> "Webpage, HTML
Only", and drop the file into documents/raw/ using the suggested filename.
"""

from __future__ import annotations

import time
from pathlib import Path

import requests

RAW_DIR = Path(__file__).resolve().parent / "raw"

# A real browser User-Agent — many sites reject the default python-requests UA.
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

REQUEST_TIMEOUT = 25     # seconds
POLITE_DELAY = 1.5       # seconds between requests — don't hammer servers

# (filename_stem, url) — stems mirror the Documents table order in planning.md.
SOURCES: list[tuple[str, str]] = [
    ("01_mdc_intl_housing",   "https://www.mdc.edu/internationalstudents/resources/housing.aspx"),
    ("02_mdc_faq_housing",    "https://faq.mdc.edu/knowledgebase/does-mdc-have-student-housing/"),
    # Swapped from apartments.com (hard 403 / Cloudflare) to rent.com, which
    # serves real listing HTML and covers the same "apartments near MDC" subtopic.
    ("03_rent_com_miami",     "https://www.rent.com/florida/miami-apartments"),
    ("04_fllat",              "https://fllat.com/miami/off-campus-housing-near-miami-dade-college"),
    ("05_collegefind",        "https://www.college-find.com/apartments/miami-dade-college"),
    ("06_student_com",        "https://www.student.com/us/miami/u/miami-dade-college"),
    ("07_roomchoice",         "https://www.roomchoice.com/schools/fl/miami-dade-college/"),
    ("08_campusrent",         "https://www.campusrent.com/miami-dade-college-apartments.cfm"),
    ("09_casita",             "https://www.casita.com/student-accommodation/usa/miami/miami-dade-college"),
    # old.reddit.com serves real HTML; www.reddit.com returns a JS-challenge page.
    ("10_reddit_miami",       "https://old.reddit.com/r/Miami/comments/ho17nc/looking_for_student_housing_optionsroommates/"),
]

# A page that returns a 200 but almost no real content is usually a bot/JS
# challenge, not the article. Flag those so they aren't mistaken for success.
MIN_BELIEVABLE_BYTES = 15_000


def fetch_one(stem: str, url: str) -> tuple[str, str]:
    """Fetch a single URL. Returns (status_label, detail)."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
    except requests.RequestException as err:
        return "ERROR", f"{type(err).__name__}: {err}"

    if resp.status_code != 200:
        return "BLOCKED", f"HTTP {resp.status_code} — save manually as {stem}.html"

    html = resp.text
    out = RAW_DIR / f"{stem}.html"
    out.write_text(html, encoding="utf-8")

    if len(html) < MIN_BELIEVABLE_BYTES:
        return ("SUSPECT",
                f"only {len(html)} bytes — likely a challenge page; "
                f"verify {out.name} or save manually")
    return "OK", f"{len(html):,} bytes -> {out.name}"


def main() -> None:
    RAW_DIR.mkdir(exist_ok=True)
    print(f"Saving raw HTML to: {RAW_DIR}\n")

    counts = {"OK": 0, "SUSPECT": 0, "BLOCKED": 0, "ERROR": 0}
    for stem, url in SOURCES:
        label, detail = fetch_one(stem, url)
        counts[label] += 1
        print(f"  [{label:<7}] {stem}: {detail}")
        time.sleep(POLITE_DELAY)

    print(f"\nSummary: {counts['OK']} ok, {counts['SUSPECT']} suspect, "
          f"{counts['BLOCKED']} blocked, {counts['ERROR']} error")
    blocked = counts["BLOCKED"] + counts["SUSPECT"] + counts["ERROR"]
    if blocked:
        print(f"\n{blocked} source(s) need a manual save. Open the URL in your "
              "browser,\nFile -> Save Page As -> 'Webpage, HTML Only', and place "
              f"it in\n{RAW_DIR} with the suggested filename. Then run ingest.py.")


if __name__ == "__main__":
    main()
