"""
tnarch_inscriptions.py – Adapter for the TN Archaeology inscription book catalogue.
Source: https://tnarch.gov.in/inscription/book?page=N
"""

from __future__ import annotations
import re
import time
from typing import Iterator
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from scraper.adapters.base_adapter import BaseAdapter
from scraper.schema import (
    HeritageRecord, SourceRegistryEntry,
    SOURCE_CONFIRMED, SOURCE_PARTIAL, NEEDS_EXPERT_REVIEW, UNVERIFIED,
    CONFIDENCE_MEDIUM, CONFIDENCE_LOW, PERMISSION_UNKNOWN,
)
from scraper.utils import (
    fetch_with_cache, utc_now, today_iso, log,
    sha256_text, contains_tamil, normalize_tamil, canonical_url,
    REQUEST_DELAY,
)
from scraper.config import SCRAPER_VERSION


class TNArchInscriptionAdapter(BaseAdapter):
    """Scrapes the paginated inscription book listing on tnarch.gov.in."""

    source_name = "tnarch_inscription_books"
    organization = "Tamil Nadu Department of Archaeology"
    base_url = "https://tnarch.gov.in/inscription/book"
    list_url_template = "https://tnarch.gov.in/inscription/book?page={page}"

    def source_registry_entry(self) -> SourceRegistryEntry:
        return SourceRegistryEntry(
            organization=self.organization,
            base_url=self.base_url,
            page_title="Inscription Books – Tamil Nadu Archaeology",
            description=(
                "Paginated catalogue of inscription books published by the "
                "Tamil Nadu Department of Archaeology."
            ),
            access_date=today_iso(),
            robots_txt_url="https://tnarch.gov.in/robots.txt",
            pagination_type="query_param",
            js_required=False,
        )

    def fetch_records(self) -> Iterator[HeritageRecord]:
        page = 0
        seen_titles: set[str] = set()
        empty_pages = 0
        MAX_EMPTY = 3

        while True:
            if self._should_stop():
                break

            url = self.list_url_template.format(page=page)
            log.info("[TNArch-Inscriptions] Fetching page %d → %s", page, url)
            html = fetch_with_cache(url, session=self.session)

            if not html:
                log.warning("[TNArch-Inscriptions] No response for page %d – stopping.", page)
                break

            records, has_items = self._parse_list_page(html, url, page)

            if not has_items:
                empty_pages += 1
                log.info("[TNArch-Inscriptions] Empty page %d (consecutive=%d).", page, empty_pages)
                if empty_pages >= MAX_EMPTY:
                    log.info("[TNArch-Inscriptions] %d consecutive empty pages – done.", MAX_EMPTY)
                    break
            else:
                empty_pages = 0

            new_records = 0
            for rec in records:
                key = (rec.title or "").strip().lower()
                if key and key in seen_titles:
                    log.debug("[TNArch-Inscriptions] Duplicate title skipped: %r", rec.title)
                    continue
                if key:
                    seen_titles.add(key)
                # Fetch detail page if available
                if rec.source_url and rec.source_url != url:
                    rec = self._enrich_from_detail(rec)
                yield rec
                self._count += 1
                new_records += 1
                if self._should_stop():
                    break

            log.info("[TNArch-Inscriptions] Page %d yielded %d new records (total=%d).",
                     page, new_records, self._count)

            if not self._has_next_page(html):
                log.info("[TNArch-Inscriptions] No next-page link detected – done.")
                break

            page += 1
            time.sleep(REQUEST_DELAY)

    # ── Parsing helpers ───────────────────────────────────────────────────────

    def _parse_list_page(self, html: str, page_url: str, page_num: int):
        """
        Parse the inscription list page.
        Returns (list[HeritageRecord], has_items: bool).
        """
        soup = BeautifulSoup(html, "lxml")
        records: list[HeritageRecord] = []

        # tnarch.gov.in renders a Drupal view with rows in <div class="views-row">
        # or a table. Try both.
        rows = soup.select("div.views-row") or soup.select("tr.odd, tr.even")

        # Fallback: any card-like article or list item containing a link
        if not rows:
            rows = soup.select("article") or soup.select("li.views-row")

        # Last fallback: find all links that look like inscription book links
        if not rows:
            links = [
                a for a in soup.find_all("a", href=True)
                if "/inscription/" in a.get("href", "") or "/book/" in a.get("href", "")
            ]
            for a in links:
                href = canonical_url(self.base_url, a["href"])
                title = a.get_text(strip=True) or None
                if not title:
                    continue
                rec = self._make_record(
                    title=title,
                    source_url=href,
                    page_url=page_url,
                    page_num=page_num,
                    extra_fields={},
                )
                records.append(rec)
            return records, bool(records)

        for row in rows:
            title_el = (
                row.select_one("h3 a, h2 a, h4 a, .views-field-title a, .field-title a") or
                row.select_one("a")
            )
            if not title_el:
                continue

            title = title_el.get_text(strip=True)
            href = canonical_url(self.base_url, title_el.get("href", ""))

            # Extra fields from the row
            extra: dict = {}
            for td in row.select("td, .views-field"):
                label_el = td.select_one(".views-label, th")
                label = label_el.get_text(strip=True).rstrip(":") if label_el else None
                value = td.get_text(strip=True)
                if label and value and label.lower() != value.lower():
                    extra[label] = value

            description_el = row.select_one(".field-body, .views-field-body, p")
            description = description_el.get_text(strip=True) if description_el else None

            rec = self._make_record(
                title=title,
                source_url=href,
                page_url=page_url,
                page_num=page_num,
                extra_fields=extra,
                description=description,
            )
            records.append(rec)

        return records, bool(records)

    def _make_record(
        self,
        title: str,
        source_url: str,
        page_url: str,
        page_num: int,
        extra_fields: dict,
        description: str | None = None,
    ) -> HeritageRecord:
        now = utc_now()
        rec = HeritageRecord(
            record_type="inscription_publication",
            title=title,
            country="India",
            state="Tamil Nadu",
            source_url=source_url,
            source_page_title="Inscription Books – Tamil Nadu Archaeology",
            source_organization=self.organization,
            source_access_date=today_iso(),
            source_verified=SOURCE_PARTIAL,
            verification_method="automated_html_extraction",
            review_required=True,
            review_reason="Automated extraction – needs expert review for historical fields.",
            confidence_level=CONFIDENCE_LOW,
            reuse_permission_verified=PERMISSION_UNKNOWN,
            copyright_status="Government of Tamil Nadu – terms not explicitly stated",
            description=description,
            scraped_at=now,
            scraper_version=SCRAPER_VERSION,
            extraction_method="requests+beautifulsoup4",
            content_hash=sha256_text(title + (description or "")),
            extra={"list_page": page_url, "page_number": page_num, **extra_fields},
        )
        # Tamil text detection
        if title and contains_tamil(title):
            rec.local_name_ta = normalize_tamil(title)
        return rec

    def _enrich_from_detail(self, rec: HeritageRecord) -> HeritageRecord:
        """Fetch the detail page and add extra fields."""
        html = fetch_with_cache(rec.source_url, session=self.session)
        if not html:
            return rec

        soup = BeautifulSoup(html, "lxml")

        # Page title
        title_tag = soup.find("title")
        if title_tag and not rec.source_page_title:
            rec.source_page_title = title_tag.get_text(strip=True)

        # Body / description
        body = soup.select_one(".field-body, article .body, .node__content")
        if body:
            text = body.get_text(" ", strip=True)
            if text and not rec.description:
                rec.description = text[:2000]

        # Look for Tamil text in body
        if html and contains_tamil(html):
            # Extract all Tamil characters in the page
            tamil_segments = []
            for el in soup.find_all(string=True):
                if contains_tamil(el):
                    seg = normalize_tamil(el.strip())
                    if seg:
                        tamil_segments.append(seg)
            if tamil_segments and not rec.inscription_text_original:
                rec.inscription_text_original = " | ".join(tamil_segments[:5])

        # Images
        img = soup.select_one("article img, .field-image img, .field img")
        if img:
            src = img.get("src", "")
            if src:
                rec.image_source_url = canonical_url(rec.source_url, src)
                rec.image_caption = img.get("alt", "") or None
                rec.image_permission_status = PERMISSION_UNKNOWN
                rec.image_download_status = "pending"

        # District / location hints
        text_lower = (rec.description or "").lower()
        for district in _TN_DISTRICTS:
            if district.lower() in text_lower:
                rec.district = district
                rec.location_source = "text_extraction"
                break

        rec.source_verified = SOURCE_CONFIRMED if rec.description else SOURCE_PARTIAL
        return rec

    def _has_next_page(self, html: str) -> bool:
        soup = BeautifulSoup(html, "lxml")
        # Look for a "next" pager link
        next_link = (
            soup.find("a", rel="next") or
            soup.find("li", class_=lambda c: c and "pager-next" in c.lower()) or
            soup.find("a", string=re.compile(r"next|›|»", re.I))
        )
        return bool(next_link)


# Tamil Nadu districts for location extraction
_TN_DISTRICTS = [
    "Ariyalur", "Chengalpattu", "Chennai", "Coimbatore", "Cuddalore",
    "Dharmapuri", "Dindigul", "Erode", "Kallakurichi", "Kancheepuram",
    "Kanyakumari", "Karur", "Krishnagiri", "Madurai", "Mayiladuthurai",
    "Nagapattinam", "Namakkal", "Nilgiris", "Perambalur", "Pudukkottai",
    "Ramanathapuram", "Ranipet", "Salem", "Sivaganga", "Tenkasi",
    "Thanjavur", "Theni", "Thoothukudi", "Tiruchirappalli", "Tirunelveli",
    "Tirupathur", "Tiruppur", "Tiruvallur", "Tiruvannamalai", "Tiruvarur",
    "Vellore", "Viluppuram", "Virudhunagar",
    # Keeladi-specific
    "Sivaganga", "Madurai",
]
