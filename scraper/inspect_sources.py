"""
inspect_sources.py – Phase 1: Website inspection and feasibility analysis.

Run as:
    python -m scraper.inspect_sources
"""

from __future__ import annotations
import json
from dataclasses import asdict
from pathlib import Path

from bs4 import BeautifulSoup

from scraper.config import SOURCES, INSPECTION_REPORT, REPORTS_DIR, FIXTURES_DIR
from scraper.schema import SourceRegistryEntry
from scraper.utils import (
    check_robots_txt, fetch_with_cache, get_session,
    utc_now, today_iso, log, sha256_text
)

REPORTS_DIR.mkdir(parents=True, exist_ok=True)
FIXTURES_DIR.mkdir(parents=True, exist_ok=True)


# ── Per-source inspection logic ───────────────────────────────────────────────

def _inspect_generic(name: str, url: str, session) -> dict:
    """Generic page inspector – returns a findings dict."""
    html = fetch_with_cache(url, session=session, timeout=6)
    findings = {
        "source_id": name,
        "url": url,
        "reachable": html is not None,
        "page_title": None,
        "has_tables": False,
        "has_pagination": False,
        "pagination_type": None,
        "pagination_param": None,
        "has_links": 0,
        "has_images": 0,
        "has_pdf_links": 0,
        "js_required_hint": False,
        "tamil_text_present": False,
        "content_length": 0,
        "notes": [],
    }
    if not html:
        findings["notes"].append("Page not reachable.")
        return findings

    # Save fixture for tests
    fixture_path = FIXTURES_DIR / f"{name}.html"
    fixture_path.write_text(html, encoding="utf-8")
    findings["content_length"] = len(html)

    soup = BeautifulSoup(html, "lxml")

    title_tag = soup.find("title")
    findings["page_title"] = title_tag.get_text(strip=True) if title_tag else None

    # Tables
    findings["has_tables"] = bool(soup.find("table"))

    # Links
    all_links = soup.find_all("a", href=True)
    findings["has_links"] = len(all_links)
    pdf_links = [a for a in all_links if ".pdf" in a["href"].lower()]
    findings["has_pdf_links"] = len(pdf_links)

    # Images
    findings["has_images"] = len(soup.find_all("img"))

    # Pagination hints
    pager = (
        soup.find(class_=lambda c: c and "pager" in c.lower()) or
        soup.find(class_=lambda c: c and "pagination" in c.lower()) or
        soup.find("nav", attrs={"aria-label": lambda v: v and "page" in v.lower()}) or
        soup.find(rel="next")
    )
    if pager:
        findings["has_pagination"] = True
        # Detect query param vs path
        page_links = [a["href"] for a in soup.find_all("a", href=True)
                      if "page=" in a.get("href", "")]
        if page_links:
            findings["pagination_type"] = "query_param"
            findings["pagination_param"] = "page"
        else:
            path_page_links = [a["href"] for a in soup.find_all("a", href=True)
                               if "/page/" in a.get("href", "")]
            if path_page_links:
                findings["pagination_type"] = "path"
                findings["pagination_param"] = "page"

    # JS hint – look for common SPA markers
    scripts = soup.find_all("script", src=True)
    for sc in scripts:
        src = sc.get("src", "")
        if any(kw in src for kw in ["react", "vue", "angular", "bundle", "chunk"]):
            findings["js_required_hint"] = True
            findings["notes"].append("JavaScript SPA indicators found in page source.")
            break

    # Tamil Unicode check
    from scraper.utils import contains_tamil
    if contains_tamil(html):
        findings["tamil_text_present"] = True

    return findings


def inspect_all(sources_filter: list[str] | None = None) -> list[SourceRegistryEntry]:
    """Inspect configured sources and return registry entries."""
    session = get_session()
    registry: list[SourceRegistryEntry] = []
    inspection_data: list[dict] = []

    target_sources = {
        name: url for name, url in SOURCES.items()
        if not sources_filter or any(f.lower() in name.lower() for f in sources_filter)
    }

    for name, url in target_sources.items():
        log.info("=== Inspecting: %s → %s ===", name, url)

        # robots.txt
        robots = check_robots_txt(url, session=session)
        log.info("robots.txt [%s]: status=%s, crawl_allowed=%s",
                 name, robots["status"], robots["crawl_allowed"])

        # Page inspection
        findings = _inspect_generic(name, url, session)
        log.info("Page [%s]: reachable=%s, title=%r, pagination=%s",
                 name, findings["reachable"], findings["page_title"],
                 findings["has_pagination"])

        entry = SourceRegistryEntry(
            organization=_org_from_name(name),
            base_url=url,
            page_title=findings["page_title"],
            description=f"Inspection of {url}",
            access_date=today_iso(),
            robots_txt_url=robots["url"],
            robots_txt_status=str(robots["status"]),
            crawl_permitted=robots["crawl_allowed"],
            pagination_type=findings["pagination_type"],
            js_required=findings["js_required_hint"],
            notes="; ".join(findings["notes"]) if findings["notes"] else None,
            last_checked=utc_now(),
        )
        registry.append(entry)
        inspection_data.append({**findings, "robots": robots, "registry": asdict(entry)})

    _write_inspection_report(inspection_data)
    return registry


def _org_from_name(name: str) -> str:
    mapping = {
        "tnarch_inscription_books": "Tamil Nadu Department of Archaeology",
        "tnarch_tamil_brahmi":      "Tamil Nadu Department of Archaeology",
        "tnarch_brahmi_inscription":"Tamil Nadu Department of Archaeology",
        "tnarch_node_1257":         "Tamil Nadu Department of Archaeology",
        "keeladi_museum":           "Keeladi Museum, Tamil Nadu",
        "asi_bharatshri":           "Archaeological Survey of India",
    }
    return mapping.get(name, "Unknown")


def _write_inspection_report(data: list[dict]) -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    lines = [
        "# AI Heritage Explorer – Source Inspection Report",
        f"\n**Generated:** {utc_now()}",
        "\n---\n",
    ]
    for d in data:
        r = d.get("robots", {})
        lines += [
            f"## {d['source_id']}",
            f"- **URL:** {d['url']}",
            f"- **Reachable:** {d['reachable']}",
            f"- **Page Title:** {d.get('page_title')}",
            f"- **robots.txt:** {r.get('url')} → HTTP {r.get('status')}, crawl_allowed={r.get('crawl_allowed')}",
            f"- **Pagination:** {d.get('has_pagination')} (type={d.get('pagination_type')})",
            f"- **Tables:** {d.get('has_tables')}",
            f"- **Images:** {d.get('has_images')}",
            f"- **PDF Links:** {d.get('has_pdf_links')}",
            f"- **Tamil Text Present:** {d.get('tamil_text_present')}",
            f"- **JS SPA Hint:** {d.get('js_required_hint')}",
            f"- **Content Length:** {d.get('content_length')} chars",
            f"- **Notes:** {'; '.join(d.get('notes') or []) or 'None'}",
            "",
        ]
    robots_raw_section = []
    for d in data:
        r = d.get("robots", {})
        if r.get("content"):
            robots_raw_section.append(f"### {d['source_id']} – robots.txt\n```\n{r['content'][:2000]}\n```\n")

    lines.append("\n---\n## robots.txt Raw Content\n")
    lines += robots_raw_section

    INSPECTION_REPORT.write_text("\n".join(lines), encoding="utf-8")
    log.info("Inspection report written → %s", INSPECTION_REPORT)


if __name__ == "__main__":
    inspect_all()
