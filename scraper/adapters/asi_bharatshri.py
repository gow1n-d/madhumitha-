"""
asi_bharatshri.py – Adapter for the ASI BharatShri portal.
Source: https://bharatshri.asi.gov.in/index
"""

from __future__ import annotations
import re
from typing import Iterator

from bs4 import BeautifulSoup

from scraper.adapters.base_adapter import BaseAdapter
from scraper.schema import (
    HeritageRecord, SourceRegistryEntry,
    SOURCE_CONFIRMED, SOURCE_PARTIAL, NEEDS_EXPERT_REVIEW,
    CONFIDENCE_MEDIUM, CONFIDENCE_LOW, PERMISSION_UNKNOWN,
)
from scraper.utils import (
    fetch_with_cache, utc_now, today_iso, log,
    sha256_text, contains_tamil, normalize_tamil, canonical_url,
)
from scraper.config import SCRAPER_VERSION

BASE_URL = "https://bharatshri.asi.gov.in"
INDEX_URL = f"{BASE_URL}/index"

# Known sub-sections of BharatShri to probe
PROBE_PATHS = [
    "/index",
    "/inscriptions",
    "/inscription",
    "/monuments",
    "/epigraphy",
    "/tamil",
    "/south-india",
]


class ASIAdapter(BaseAdapter):
    """Scrapes the ASI BharatShri Epigraphy portal."""

    source_name = "asi_bharatshri"
    organization = "Archaeological Survey of India"
    base_url = BASE_URL

    def source_registry_entry(self) -> SourceRegistryEntry:
        return SourceRegistryEntry(
            organization=self.organization,
            base_url=self.base_url,
            page_title="BharatShri – ASI Epigraphy Portal",
            description=(
                "Archaeological Survey of India BharatShri portal for inscriptions, "
                "epigraphy, and monument data. May require further authentication or "
                "JavaScript for full access."
            ),
            access_date=today_iso(),
            robots_txt_url=f"{BASE_URL}/robots.txt",
            pagination_type=None,
            js_required=None,   # unknown until inspected
            notes="Portal may require JS for dynamic content.",
        )

    def fetch_records(self) -> Iterator[HeritageRecord]:
        visited: set[str] = set()
        pages = [INDEX_URL]

        # Discover from homepage
        home_html = fetch_with_cache(INDEX_URL, session=self.session)
        if home_html:
            soup = BeautifulSoup(home_html, "lxml")
            for a in soup.find_all("a", href=True):
                href = a["href"]
                full = canonical_url(BASE_URL, href)
                if (BASE_URL in full and
                        full not in pages and
                        not any(skip in full for skip in ["#", "mailto:", "tel:", "javascript"])):
                    pages.append(full)

        # Add probe paths
        for path in PROBE_PATHS:
            u = BASE_URL + path
            if u not in pages:
                pages.append(u)

        for url in pages:
            if self._should_stop():
                break
            if url in visited:
                continue
            visited.add(url)

            log.info("[ASI-BharatShri] Fetching %s", url)
            html = fetch_with_cache(url, session=self.session)
            if not html:
                log.warning("[ASI-BharatShri] Could not fetch %s", url)
                continue

            for rec in self._parse_page(html, url):
                yield rec
                self._count += 1
                if self._should_stop():
                    break

    def _parse_page(self, html: str, url: str) -> list[HeritageRecord]:
        soup = BeautifulSoup(html, "lxml")
        records: list[HeritageRecord] = []

        page_title_tag = soup.find("title")
        page_title = page_title_tag.get_text(strip=True) if page_title_tag else url

        # Check for JS-only rendering (very little text)
        body_text = soup.get_text(" ", strip=True)
        if len(body_text) < 200:
            log.warning("[ASI-BharatShri] Very short content at %s – may require JS. Flagging.", url)
            rec = HeritageRecord(
                record_type="portal_index",
                title=page_title,
                description=f"Page rendered minimal content ({len(body_text)} chars). "
                            "JavaScript rendering may be required for full content access.",
                source_url=url,
                source_page_title=page_title,
                source_organization=self.organization,
                source_access_date=today_iso(),
                source_verified="UNVERIFIED",
                review_required=True,
                review_reason="Page may require JavaScript – content not fully accessible via static fetch.",
                confidence_level=CONFIDENCE_LOW,
                reuse_permission_verified=PERMISSION_UNKNOWN,
                scraped_at=utc_now(),
                scraper_version=SCRAPER_VERSION,
                extraction_method="requests+beautifulsoup4",
                content_hash=sha256_text(body_text),
                extra={"page_url": url, "js_rendering_suspected": True},
            )
            records.append(rec)
            return records

        main = (
            soup.select_one("main, article, #content, .content, .container") or
            soup.body
        )
        if not main:
            return records

        # Look for inscription/epigraphy tables
        tables = main.find_all("table")
        for table in tables:
            recs = self._parse_table(table, url, page_title)
            records.extend(recs)

        # If no tables, look for cards / listing items
        if not records:
            items = main.select(".card, .item, li.inscription, .entry")
            for item in items:
                title_el = item.select_one("h2, h3, h4, .title, strong")
                title = title_el.get_text(strip=True) if title_el else None
                body = item.get_text(" ", strip=True)
                if not title and not body:
                    continue
                rec = self._make_record(
                    title=title or body[:80],
                    body=body[:2000],
                    url=url,
                    page_title=page_title,
                )
                records.append(rec)

        # Fallback: whole page as one record
        if not records:
            headings = main.find_all(["h1", "h2", "h3"])
            if headings:
                for h in headings:
                    heading_text = h.get_text(strip=True)
                    body_parts = []
                    for sib in h.find_next_siblings():
                        if sib.name in ("h1", "h2", "h3"):
                            break
                        body_parts.append(sib.get_text(" ", strip=True))
                    body = " ".join(body_parts).strip()
                    if body:
                        records.append(self._make_record(heading_text, body[:2000], url, page_title))
            else:
                records.append(self._make_record(page_title, body_text[:2000], url, page_title))

        return records

    def _parse_table(self, table, url: str, page_title: str) -> list[HeritageRecord]:
        records = []
        headers = [th.get_text(strip=True) for th in table.find_all("th")]
        for row in table.find_all("tr"):
            cells = [td.get_text(strip=True) for td in row.find_all("td")]
            if not cells or len(cells) < 2:
                continue
            # Map columns to headers
            row_data = dict(zip(headers, cells)) if headers else {}
            title = (
                row_data.get("Title") or row_data.get("Name") or
                row_data.get("Inscription") or cells[0]
            )
            body = " | ".join(f"{k}: {v}" for k, v in row_data.items() if v)
            rec = self._make_record(title, body, url, page_title)
            # Populate specific fields from column data
            for h, v in row_data.items():
                h_lower = h.lower()
                if "district" in h_lower:
                    rec.district = v
                elif "state" in h_lower:
                    rec.state = v
                elif "dynasty" in h_lower:
                    rec.dynasty = v
                elif "language" in h_lower:
                    rec.language = v
                elif "date" in h_lower or "period" in h_lower:
                    rec.date_text_as_published = v
                elif "site" in h_lower:
                    rec.site_name = v
            records.append(rec)
        return records

    def _make_record(self, title: str, body: str, url: str, page_title: str) -> HeritageRecord:
        return HeritageRecord(
            record_type="epigraphy_record",
            title=title,
            description=body[:2000],
            language="Tamil" if contains_tamil(body) else None,
            country="India",
            source_url=url,
            source_page_title=page_title,
            source_organization=self.organization,
            source_access_date=today_iso(),
            source_verified=SOURCE_PARTIAL,
            verification_method="direct_html_extraction",
            review_required=True,
            review_reason="ASI portal content needs expert review for historical classification.",
            confidence_level=CONFIDENCE_LOW,
            reuse_permission_verified=PERMISSION_UNKNOWN,
            copyright_status="Archaeological Survey of India – terms not explicitly stated",
            inscription_text_original=normalize_tamil(body[:500]) if contains_tamil(body) else None,
            scraped_at=utc_now(),
            scraper_version=SCRAPER_VERSION,
            extraction_method="requests+beautifulsoup4",
            content_hash=sha256_text(body),
            extra={"page_url": url},
        )
