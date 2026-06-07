"""
Ingestion and chunking for The Unofficial Guide (Off-Campus Housing for MDC Students).

Pipeline stage 1-2:  Document Ingestion -> Chunking
(Downstream stages — Embedding + ChromaDB, Retrieval, Generation — live elsewhere.)

This script implements the Documents + Chunking Strategy sections of planning.md:

    Documents      : web sources (HTML) + a Reddit discussion thread, saved locally
                     in this documents/ folder as .html / .txt / .md (optionally .pdf).
    Preprocessing  : strip HTML tags, navigation menus, ads, and footer content;
                     normalize whitespace; collapse duplicate blank lines;
                     preserve paragraph breaks before chunking.
    Chunk size     : 500 characters
    Overlap        : 100 characters

How to use:
    1. Run `python documents/fetch_sources.py` first to download raw HTML into
       documents/raw/, or save pages manually there (Save Page As -> "Webpage,
       HTML Only"). You can also drop .txt / .md / .pdf files in there.
    2. Run:   python documents/ingest.py
       The script prints a per-document and total chunk count and writes
       chunks.json next to this script for the embedding stage to load.
    3. Inspect cleaning:   python documents/ingest.py --inspect
       Prints one fully-cleaned document so you can confirm no nav text, HTML
       entities, or off-domain boilerplate survived before chunking.
"""

from __future__ import annotations

import html
import json
import re
import sys
from collections import Counter
from dataclasses import dataclass, asdict
from pathlib import Path

# --- Configuration (matches planning.md "Chunking Strategy") -----------------

CHUNK_SIZE = 500       # characters
OVERLAP = 100          # characters
DOCS_DIR = Path(__file__).resolve().parent
RAW_DIR = DOCS_DIR / "raw"          # where fetch_sources.py saves raw documents
OUTPUT_FILE = DOCS_DIR / "chunks.json"

# File types we know how to load. HTML is the primary type for this corpus.
TEXT_EXTENSIONS = {".txt", ".md"}
HTML_EXTENSIONS = {".html", ".htm"}
PDF_EXTENSIONS = {".pdf"}


# --- Optional dependencies (degrade gracefully if not installed) -------------

try:
    from bs4 import BeautifulSoup  # type: ignore[import]  # beautifulsoup4
    _HAVE_BS4 = True
except ImportError:
    _HAVE_BS4 = False

try:
    import pdfplumber  # type: ignore[import]
    _HAVE_PDFPLUMBER = True
except ImportError:
    _HAVE_PDFPLUMBER = False


@dataclass
class Chunk:
    """One retrievable unit. `id` is stable so re-ingesting overwrites cleanly."""
    id: str
    source: str        # original filename — used for source attribution later
    chunk_index: int   # position of this chunk within its source document
    text: str


# --- Cleaning ----------------------------------------------------------------

# Tags whose entire contents are always noise for a housing knowledge base.
_NOISE_TAGS = ["script", "style", "nav", "aside", "form",
               "button", "noscript", "svg", "iframe"]

# <header>/<footer> are usually site chrome, BUT a CMS article's own title and
# byline live in <header class="entry-header"> inside <article>. Remove these
# only when they are NOT inside an <article>, so article titles survive.
_SECTION_NOISE_TAGS = ["header", "footer"]

# Whole-token markers (matched against class/id/role split on -, _, space) for
# specific noise WIDGETS: cookie/consent banners, ads, share/social buttons,
# comment widgets, newsletter signups, breadcrumbs, modals/popups, skip-links.
# Deliberately NOT here: nav/menu/header/footer/sidebar — those are handled by
# the semantic _NOISE_TAGS below. As class substrings they false-match layout
# wrappers like "content-sidebar-wrap" that contain the main content.
_NOISE_HINTS = {
    "ad", "ads", "advert", "advertisement", "cookie", "consent", "gdpr",
    "newsletter", "subscribe", "social", "share", "sharing", "breadcrumb",
    "breadcrumbs", "modal", "popup", "lightbox", "promo", "skip", "comments",
}

# Structural elements are never removed by class/id heuristics — they hold the
# main content, and their class lists often include layout words like
# "content-sidebar" that would otherwise trigger a false positive.
_STRUCTURAL_TAGS = {"html", "body", "main", "article", "section", "[document]"}

# Exact element ids for known site chrome that the token rules deliberately skip
# (e.g. "header" was dropped from the token hints to protect layout wrappers,
# but a div whose id is literally "header" is page chrome). Matched exactly, so
# they can't false-match content. Covers old.reddit's nav bars and common ids.
_NOISE_IDS = {
    "header", "sr-header-area", "header-bottom-left", "header-bottom-right",
    "footer", "footer-parent", "side", "sidebar", "ad_main", "ad_main_top",
    "eu-cookie-policy", "redesign-beta-optin", "navbar", "topnav",
}

_TOKEN_SPLIT = re.compile(r"[-_\s]+")

# Link/line text that is pure UI chrome, not content (exact-line match). Also
# drops bare connector words left stranded on their own line when get_text
# splits an inline link out of a sentence (e.g. "... ago in Student Life").
_JUNK_LINE_RE = re.compile(
    r"^(read more|show more|see more|learn more|share|tweet|save|print|"
    r"sign in|log ?in|sign up|subscribe|menu|home|back to top|"
    r"in|on|by|at|of|the|and|or|"
    r"\d+\s*comments?|\d+\s*shares?|\d+\s*likes?)$",
    re.IGNORECASE,
)

# Footer / CMS-metadata boilerplate that survives as plain text (prefix /
# contains match): copyright + legal links, plus blog/FAQ post metadata such as
# "Last Updated:", "Tags:", "Posted in", "Filed under", "Categories:".
_BOILERPLATE_LINE_RE = re.compile(
    r"(^skip to\b|^copyright\b|©|\ball rights reserved\b|"
    r"^(privacy policy|terms of (use|service)|cookie policy|sitemap|"
    r"do not sell|last updated|tags?|posted (on|in|by)|filed under|"
    r"categor(y|ies)|share this|related posts?|leave a (comment|reply))\b)",
    re.IGNORECASE,
)


# A line that is only punctuation/brackets/bullets, or a bare "Map" link label —
# leftover from inline links that get_text split onto their own line.
_PUNCT_ONLY_RE = re.compile(r"^([\[\](){}|•·–—\-*:>\s]+|map)$", re.IGNORECASE)

# Stray separator punctuation to strip from the ENDS of a line (e.g. the trailing
# "[" left when an inline <a>Map</a> link is removed). Parentheses are excluded
# on purpose so phone numbers like "(645) 236-8019" survive intact.
_EDGE_PUNCT = " \t\r\n|[]{}•·–—*>:"


def _is_junk_line(line: str) -> bool:
    """True if a line is UI chrome, footer boilerplate, or a punctuation-only
    artifact — not content."""
    return bool(
        _JUNK_LINE_RE.match(line)
        or _BOILERPLATE_LINE_RE.search(line)
        or _PUNCT_ONLY_RE.match(line)
    )


def _is_noise_element(el) -> bool:
    """True if a tag's class/id/role marks it as a site-boilerplate widget."""
    if el.attrs is None:                  # already decomposed (parent removed)
        return False
    if el.name in _STRUCTURAL_TAGS:       # never strip content-bearing wrappers
        return False
    if (el.get("id") or "").lower() in _NOISE_IDS:   # exact-id site chrome
        return True
    css = el.get("class", []) or []
    if isinstance(css, str):              # bs4 returns str for malformed markup
        css = [css]
    attrs = " ".join(css + [el.get("id") or "", el.get("role") or ""]).lower()
    tokens = set(_TOKEN_SPLIT.split(attrs))
    return bool(tokens & _NOISE_HINTS)    # whole-token match, not substring


def clean_html(raw_html: str) -> str:
    """Strip HTML to readable text, removing nav/ads/footer/cookie banners/
    share buttons/comment widgets/boilerplate.

    Uses BeautifulSoup when available (tag-aware, matches the spec). Falls back
    to a coarse regex strip if bs4 isn't installed so the script still runs.
    """
    if _HAVE_BS4:
        soup = BeautifulSoup(raw_html, "html.parser")
        # Work from <body> only so the <head> (page <title>, meta) is dropped —
        # the "X | SiteName" title is title-spam that otherwise out-ranks real
        # content in retrieval. Fall back to the whole tree if there's no body.
        root = soup.body or soup
        # Drop always-noise sections (scripts, nav, asides, buttons, forms...).
        for tag in root(_NOISE_TAGS):
            tag.decompose()
        # Drop header/footer ONLY when they're site chrome (not an article's own
        # title/byline header inside <article>).
        for tag in root(_SECTION_NOISE_TAGS):
            if tag.find_parent("article") is None:
                tag.decompose()
        # Drop elements whose class/id/role marks them as boilerplate.
        # Collect first, then decompose: decomposing during iteration detaches
        # descendants and corrupts the walk.
        noise = [el for el in root.find_all(True) if _is_noise_element(el)]
        for el in noise:
            if el.attrs is not None:   # skip if already removed via a parent
                el.decompose()
        # Drop "Read more" / "Share" style links left in the body.
        for a in root.find_all("a"):
            if a.attrs is not None and _JUNK_LINE_RE.match(a.get_text(strip=True)):
                a.decompose()
        # get_text with newline separators so paragraph breaks survive.
        text = root.get_text(separator="\n")
        return text

    # Fallback: no bs4 — remove script/style blocks, then all remaining tags.
    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ",
                  raw_html, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<[^>]+>", "\n", text)  # tags -> line breaks
    return text


def normalize_whitespace(text: str) -> str:
    """Normalize whitespace, decode HTML entities, drop UI-chrome lines, and
    collapse duplicate blank lines while preserving paragraph breaks."""
    # Decode ALL HTML entities (&amp; &nbsp; &#39; &quot; ...) in one pass.
    text = html.unescape(text).replace("\xa0", " ")

    # Pass 1: trim each line, strip stray edge punctuation, drop UI-chrome lines
    # and short page-title/breadcrumb lines ("X | SiteName", "A | B | C").
    candidates = []
    for line in text.splitlines():
        line = line.strip().strip(_EDGE_PUNCT).strip()
        if not line or _is_junk_line(line):
            continue
        if len(line) < 80 and " | " in line:   # title / breadcrumb separator
            continue
        candidates.append(line)

    # Find repeated boilerplate: SHORT, DIGIT-FREE lines, NOT ending in sentence
    # punctuation, that occur 3+ times (nav menus, repeated site name). Guards:
    #   - digit-free protects repeated data like zip codes / prices in tables
    #   - the ".?!:" exclusion protects repeated content headings and questions
    #     (e.g. an FAQ's "Does MDC have student housing?" repeats but is content)
    def _dedupable(ln: str) -> bool:
        return (len(ln) <= 40 and ln[-1] not in ".?!:"
                and not any(ch.isdigit() for ch in ln))

    counts = Counter(ln.lower() for ln in candidates if _dedupable(ln))
    boilerplate = {key for key, n in counts.items() if n >= 3}

    # Pass 2: keep the first occurrence of each boilerplate line, drop repeats,
    # and collapse consecutive duplicates (case-insensitive).
    lines = []
    seen = set()
    for line in candidates:
        low = line.lower()
        if low in boilerplate:
            if low in seen:
                continue
            seen.add(low)
        if lines and low == lines[-1].lower():
            continue
        lines.append(line)
    text = "\n".join(lines)
    # Collapse runs of spaces/tabs within a line.
    text = re.sub(r"[ \t]+", " ", text)
    # Collapse 3+ newlines into exactly two (one blank line = paragraph break).
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def clean_text(raw: str, is_html: bool) -> str:
    """Full preprocessing per the spec: extract text, strip HTML/nav/footer,
    normalize whitespace, preserve paragraph breaks."""
    if is_html:
        raw = clean_html(raw)
    return normalize_whitespace(raw)


# --- Chunking ----------------------------------------------------------------

def chunk_text(text: str, chunk_size: int = CHUNK_SIZE,
               overlap: int = OVERLAP) -> list[str]:
    """Split text into overlapping character windows.

    Sliding window: each chunk is `chunk_size` chars; the next window starts
    `chunk_size - overlap` chars later, so consecutive chunks share `overlap`
    characters. This keeps information that straddles a boundary (e.g. a rental
    cost that starts at the end of one chunk) recoverable in the next chunk.

    Both boundaries are aligned to whitespace so chunks neither end nor begin
    mid-word: the END is nudged back to the last whitespace in the window, and
    the next START (which the overlap places mid-word) is nudged forward to the
    next whitespace. This keeps chunks readable as standalone thoughts while
    overlap stays ~100 chars.
    """
    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")

    text = text.strip()
    if not text:
        return []

    step = chunk_size - overlap          # 500 - 100 = 400 chars of new content
    chunks: list[str] = []
    start = 0
    n = len(text)

    while start < n:
        end = min(start + chunk_size, n)

        # If we're not at the document end, try to break on whitespace so we
        # don't split a word. Look back within the current window only.
        if end < n:
            window = text[start:end]
            cut = max(window.rfind(" "), window.rfind("\n"))
            # Only honor the break if it isn't pathologically early.
            if cut > step // 2:
                end = start + cut

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        if end >= n:
            break
        # Advance by step, measured from the *actual* end so overlap stays ~100.
        start = max(end - overlap, start + 1)
        # Snap the start forward to a word boundary if the overlap dropped us
        # mid-word, so the next chunk begins with a whole word.
        if not text[start - 1].isspace():
            nxt = text.find(" ", start)
            nl = text.find("\n", start)
            cands = [c for c in (nxt, nl) if c != -1 and c - start < overlap]
            if cands:
                start = min(cands) + 1

    return chunks


# --- Loading -----------------------------------------------------------------

def load_pdf(path: Path) -> str:
    if not _HAVE_PDFPLUMBER:
        raise RuntimeError(
            f"{path.name} is a PDF but pdfplumber is not installed. "
            "Add `pdfplumber==0.11.4` to requirements.txt and pip install it."
        )
    pages = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            pages.append(page.extract_text() or "")
    return "\n\n".join(pages)


def load_document(path: Path) -> tuple[str, bool]:
    """Return (raw_text, is_html) for a single file, or raise on unknown type."""
    ext = path.suffix.lower()
    if ext in HTML_EXTENSIONS:
        return path.read_text(encoding="utf-8", errors="ignore"), True
    if ext in TEXT_EXTENSIONS:
        return path.read_text(encoding="utf-8", errors="ignore"), False
    if ext in PDF_EXTENSIONS:
        return load_pdf(path), False
    raise ValueError(f"Unsupported file type: {path.name}")


def source_dir() -> Path:
    """Prefer documents/raw/ (where fetch_sources.py writes); fall back to the
    documents/ root so manually-pasted .txt files still work."""
    if RAW_DIR.is_dir() and any(RAW_DIR.iterdir()):
        return RAW_DIR
    return DOCS_DIR


def discover_documents(docs_dir: Path) -> list[Path]:
    supported = TEXT_EXTENSIONS | HTML_EXTENSIONS | PDF_EXTENSIONS
    return sorted(
        p for p in docs_dir.iterdir()
        if p.is_file() and p.suffix.lower() in supported
    )


# --- Orchestration -----------------------------------------------------------

def ingest(docs_dir: Path | None = None) -> list[Chunk]:
    """Load every supported document, clean it, and chunk it."""
    docs_dir = docs_dir or source_dir()
    documents = discover_documents(docs_dir)
    if not documents:
        print(f"No documents found in {docs_dir}.")
        print("Run `python documents/fetch_sources.py` first, or save your "
              "sources there as .html / .txt / .md (or .pdf), then re-run.")
        return []

    all_chunks: list[Chunk] = []
    for path in documents:
        try:
            raw, is_html = load_document(path)
        except (ValueError, RuntimeError) as err:
            print(f"  skip {path.name}: {err}")
            continue

        cleaned = clean_text(raw, is_html=is_html)
        pieces = chunk_text(cleaned)
        for i, piece in enumerate(pieces):
            all_chunks.append(
                Chunk(id=f"{path.stem}::{i}", source=path.name,
                      chunk_index=i, text=piece)
            )
        print(f"  {path.name}: {len(cleaned):>6} chars -> {len(pieces):>3} chunks")

    return all_chunks


def inspect(name: str | None = None) -> None:
    """Print one fully-cleaned document so you can read it and confirm no nav
    text, HTML entities, or off-domain boilerplate survived before chunking."""
    documents = discover_documents(source_dir())
    if not documents:
        print(f"No documents found in {source_dir()}.")
        return
    chosen = None
    if name:
        chosen = next((p for p in documents if name in p.name), None)
        if chosen is None:
            print(f"No document matching {name!r}; showing {documents[0].name} "
                  "instead. Available: "
                  + ", ".join(p.name for p in documents) + "\n")
    chosen = chosen or documents[0]
    raw, is_html = load_document(chosen)
    cleaned = clean_text(raw, is_html=is_html)
    print(f"===== CLEANED: {chosen.name} "
          f"({len(raw):,} raw chars -> {len(cleaned):,} cleaned) =====\n")
    print(cleaned)
    print(f"\n===== end ({len(chunk_text(cleaned))} chunks) =====")


def main() -> None:
    if not _HAVE_BS4:
        print("WARNING: beautifulsoup4 not installed — using a coarse regex "
              "HTML strip that will NOT remove nav/footer/ad sections.\n"
              "         Run: pip install beautifulsoup4\n")

    # `--inspect [name]` prints one cleaned document instead of chunking.
    if len(sys.argv) > 1 and sys.argv[1] == "--inspect":
        inspect(sys.argv[2] if len(sys.argv) > 2 else None)
        return

    print(f"Ingesting documents from: {source_dir()}")
    chunks = ingest()

    if not chunks:
        return

    OUTPUT_FILE.write_text(
        json.dumps([asdict(c) for c in chunks], indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"\nTotal: {len(chunks)} chunks from "
          f"{len({c.source for c in chunks})} documents")
    print(f"Wrote {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
