"""
tnarch_brahmi.py – Adapter for TN Archaeology Tamil-Brahmi script & inscription pages.

Covers:
  - https://www.tnarch.gov.in/tamil-brahmi-script
  - https://www.tnarch.gov.in/brahmi-inscription-0
  - https://www.tnarch.gov.in/node/1257
"""

from __future__ import annotations
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

BRAHMI_URLS = {
    "tnarch_tamil_brahmi":       "https://www.tnarch.gov.in/tamil-brahmi-script",
    "tnarch_brahmi_inscription": "https://www.tnarch.gov.in/brahmi-inscription-0",
    "tnarch_node_1257":          "https://www.tnarch.gov.in/node/1257",
}


class TNArchBrahmiAdapter(BaseAdapter):
    """Scrapes the Tamil-Brahmi editorial pages on tnarch.gov.in."""

    source_name = "tnarch_brahmi"
    organization = "Tamil Nadu Department of Archaeology"
    base_url = "https://www.tnarch.gov.in"

    def source_registry_entry(self) -> SourceRegistryEntry:
        return SourceRegistryEntry(
            organization=self.organization,
            base_url=self.base_url,
            page_title="Tamil-Brahmi Script – Tamil Nadu Archaeology",
            description="Editorial pages on Tamil-Brahmi script, inscriptions, and the Brahmi collection.",
            access_date=today_iso(),
            robots_txt_url="https://www.tnarch.gov.in/robots.txt",
            pagination_type=None,
            js_required=False,
        )

    def fetch_records(self) -> Iterator[HeritageRecord]:
        for page_key, url in BRAHMI_URLS.items():
            if self._should_stop():
                break
            log.info("[TNArch-Brahmi] Fetching %s → %s", page_key, url)
            html = fetch_with_cache(url, session=self.session)
            if not html:
                log.warning("[TNArch-Brahmi] Could not fetch %s", url)
                continue
            records = self._parse_page(html, url, page_key)
            for rec in records:
                yield rec
                self._count += 1
                if self._should_stop():
                    break

    def _parse_page(self, html: str, url: str, page_key: str) -> list[HeritageRecord]:
        soup = BeautifulSoup(html, "lxml")
        records: list[HeritageRecord] = []

        page_title_tag = soup.find("title")
        page_title = page_title_tag.get_text(strip=True) if page_title_tag else url

        # Collect all text sections (headings + paragraphs)
        main = (
            soup.select_one("article, .node__content, main, #content, .region-content") or
            soup.body
        )
        if not main:
            return records

        # Extract coherent text blocks (heading + following body paragraphs)
        sections = self._extract_sections(main)

        # If no sections found, fall back to whole-page text as one record
        if not sections:
            body_text = main.get_text(" ", strip=True)
            if body_text:
                sections = [{"heading": page_title, "body": body_text[:3000]}]

        for sec in sections:
            heading = sec.get("heading") or page_title
            body = sec.get("body", "")
            if not body.strip():
                continue

            # Images in this section
            img_src = None
            img_caption = None
            img_el = sec.get("img")
            if img_el:
                img_src = canonical_url(url, img_el.get("src", ""))
                img_caption = img_el.get("alt") or None

            rec = HeritageRecord(
                record_type="inscription_text" if "inscription" in heading.lower() else "editorial_content",
                title=heading,
                description=body[:2000],
                language="Tamil" if contains_tamil(body) else "English",
                script="Tamil-Brahmi" if "brahmi" in heading.lower() else None,
                country="India",
                state="Tamil Nadu",
                source_url=url,
                source_page_title=page_title,
                source_organization=self.organization,
                source_access_date=today_iso(),
                source_verified=SOURCE_CONFIRMED,
                verification_method="direct_html_extraction",
                review_required=True,
                review_reason="Historical interpretation requires expert review.",
                confidence_level=CONFIDENCE_MEDIUM,
                reuse_permission_verified=PERMISSION_UNKNOWN,
                copyright_status="Government of Tamil Nadu – terms not explicitly stated",
                image_source_url=img_src,
                image_caption=img_caption,
                image_permission_status=PERMISSION_UNKNOWN if img_src else None,
                scraped_at=utc_now(),
                scraper_version=SCRAPER_VERSION,
                extraction_method="requests+beautifulsoup4",
                content_hash=sha256_text(body),
                extra={"page_key": page_key},
            )
            # Tamil text
            if contains_tamil(body):
                rec.inscription_text_original = normalize_tamil(body[:500])
            records.append(rec)

        # Also look for linked sub-pages (same-domain links within article)
        for a in main.find_all("a", href=True):
            href = a["href"]
            if href.startswith("/") and not any(
                skip in href for skip in ["/search", "/login", "/user", "/admin"]
            ):
                full = canonical_url(self.base_url, href)
                if full not in BRAHMI_URLS.values():
                    log.debug("[TNArch-Brahmi] Found sub-link: %s", full)

        return records

    @staticmethod
    def _extract_sections(container) -> list[dict]:
        """
        Walk the container and group content into logical sections
        separated by headings (h1–h4).
        Returns list of dicts: {heading, body, img}.
        """
        sections: list[dict] = []
        current: dict = {"heading": None, "body": "", "img": None}

        for el in container.descendants:
            if not hasattr(el, "name") or el.name is None:
                continue
            if el.name in ("h1", "h2", "h3", "h4"):
                if current["body"].strip() or current["heading"]:
                    sections.append(current)
                current = {"heading": el.get_text(strip=True), "body": "", "img": None}
            elif el.name == "p":
                current["body"] += " " + el.get_text(" ", strip=True)
            elif el.name == "img" and not current["img"]:
                current["img"] = el

        if current["body"].strip() or current["heading"]:
            sections.append(current)

        return [s for s in sections if s["body"].strip()]
