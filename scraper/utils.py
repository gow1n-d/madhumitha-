"""
utils.py – Shared utilities: logging, HTTP, caching, hashing, text.
"""

from __future__ import annotations
import hashlib
import json
import logging
import time
import unicodedata
from pathlib import Path
from typing import Optional
from urllib.parse import urljoin, urlparse
from datetime import datetime, timezone

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from scraper.config import (
    USER_AGENT, REQUEST_TIMEOUT, REQUEST_DELAY,
    MAX_RETRIES, BACKOFF_FACTOR, VERIFY_TLS,
    CACHE_DIR, SCRAPER_LOG, FAILED_URLS_LOG,
    SCRAPER_VERSION,
)

# ── Logging setup ─────────────────────────────────────────────────────────────

def get_logger(name: str = "heritage_scraper") -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(logging.DEBUG)
    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)-8s] %(name)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S"
    )
    # Console – INFO and above
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(fmt)
    logger.addHandler(ch)
    # File – DEBUG and above
    SCRAPER_LOG.parent.mkdir(parents=True, exist_ok=True)
    fh = logging.FileHandler(SCRAPER_LOG, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)
    logger.addHandler(fh)
    return logger


log = get_logger()


# ── HTTP session ──────────────────────────────────────────────────────────────

def make_session() -> requests.Session:
    """Return a requests Session with retry logic and a descriptive UA."""
    session = requests.Session()
    retry = Retry(
        total=MAX_RETRIES,
        backoff_factor=BACKOFF_FACTOR,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET"],
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.headers.update({
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5,ta;q=0.3",
        "Accept-Encoding": "gzip, deflate, br",
    })
    return session


_GLOBAL_SESSION: Optional[requests.Session] = None


def get_session() -> requests.Session:
    global _GLOBAL_SESSION
    if _GLOBAL_SESSION is None:
        _GLOBAL_SESSION = make_session()
    return _GLOBAL_SESSION


# ── Cache ─────────────────────────────────────────────────────────────────────

def _cache_path(url: str) -> Path:
    key = hashlib.sha256(url.encode()).hexdigest()
    return CACHE_DIR / f"{key}.html"


def fetch_with_cache(
    url: str,
    session: Optional[requests.Session] = None,
    delay: float = REQUEST_DELAY,
    force: bool = False,
    encoding: str = "utf-8",
    timeout: int = REQUEST_TIMEOUT,
) -> Optional[str]:
    """
    Fetch *url*, returning the response text.
    Uses disk cache unless *force* is True.
    Returns None on unrecoverable error.
    """
    cached = _cache_path(url)
    if not force and cached.exists():
        log.debug("Cache hit: %s", url)
        return cached.read_text(encoding="utf-8", errors="replace")

    session = session or get_session()
    log.debug("Fetching: %s", url)
    time.sleep(delay)
    try:
        resp = session.get(url, timeout=timeout, verify=VERIFY_TLS)
        resp.raise_for_status()
    except requests.exceptions.SSLError as exc:
        log.error("TLS error for %s – %s", url, exc)
        log_failed_url(url, str(exc))
        return None
    except requests.exceptions.Timeout as exc:
        log.error("Timeout for %s – %s", url, exc)
        log_failed_url(url, "timeout")
        return None
    except requests.exceptions.HTTPError as exc:
        log.error("HTTP %s for %s – %s", resp.status_code, url, exc)
        log_failed_url(url, f"HTTP {resp.status_code}")
        return None
    except requests.exceptions.RequestException as exc:
        log.error("Request error for %s – %s", url, exc)
        log_failed_url(url, str(exc))
        return None

    text = resp.text
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cached.write_text(text, encoding="utf-8")
    return text


# ── Failed URL log ────────────────────────────────────────────────────────────

def log_failed_url(url: str, reason: str) -> None:
    entry = {
        "url": url,
        "reason": reason,
        "timestamp": utc_now(),
        "scraper_version": SCRAPER_VERSION,
    }
    FAILED_URLS_LOG.parent.mkdir(parents=True, exist_ok=True)
    with FAILED_URLS_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


# ── Hashing ───────────────────────────────────────────────────────────────────

def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# ── Time ─────────────────────────────────────────────────────────────────────

def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def today_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


# ── URL helpers ───────────────────────────────────────────────────────────────

def canonical_url(base: str, href: str) -> str:
    """Resolve a possibly-relative *href* against *base*."""
    return urljoin(base, href)


def domain_of(url: str) -> str:
    return urlparse(url).netloc


# ── Tamil text helpers ────────────────────────────────────────────────────────

def normalize_tamil(text: str) -> str:
    """
    Apply minimal Unicode normalization (NFC) to Tamil text.
    Does NOT transliterate or remove diacritics.
    """
    return unicodedata.normalize("NFC", text)


def contains_tamil(text: str) -> bool:
    """Return True if *text* contains any Tamil Unicode character."""
    return any("\u0B80" <= ch <= "\u0BFF" for ch in text)


# ── Robots.txt ────────────────────────────────────────────────────────────────

def check_robots_txt(base_url: str, session: Optional[requests.Session] = None) -> dict:
    """
    Fetch and return the raw robots.txt for *base_url*.
    Returns a dict with keys: url, status, content, crawl_allowed.
    crawl_allowed is a conservative heuristic only – always verify manually.
    """
    parsed = urlparse(base_url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    session = session or get_session()
    result = {
        "url": robots_url,
        "status": None,
        "content": None,
        "crawl_allowed": None,
    }
    try:
        resp = requests.get(robots_url, timeout=3, headers={"User-Agent": USER_AGENT})
        result["status"] = resp.status_code
        if resp.status_code == 200:
            result["content"] = resp.text[:4000]   # first 4 KB
            # Very conservative heuristic: flag if Disallow: / is present
            lines = [ln.strip().lower() for ln in resp.text.splitlines()]
            disallow_all = any(
                ln.startswith("disallow: /") and ln == "disallow: /"
                for ln in lines
            )
            result["crawl_allowed"] = not disallow_all
        elif resp.status_code == 404:
            result["crawl_allowed"] = True   # no robots.txt → assume allowed
        else:
            result["crawl_allowed"] = None
    except Exception as exc:
        result["status"] = "error"
        result["content"] = str(exc)
        result["crawl_allowed"] = None
    return result
