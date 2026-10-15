"""
schema.py – Canonical dataset schema for AI Heritage Explorer.

Every record in the dataset conforms to this dataclass.
Missing values are stored as None (null in JSON, empty in CSV).
"""

from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Optional
import uuid
import datetime


# ---------------------------------------------------------------------------
# Verification / confidence constants
# ---------------------------------------------------------------------------
SOURCE_CONFIRMED = "SOURCE_CONFIRMED"
SOURCE_PARTIAL = "SOURCE_PARTIAL"
NEEDS_EXPERT_REVIEW = "NEEDS_EXPERT_REVIEW"
UNVERIFIED = "UNVERIFIED"

CONFIDENCE_HIGH = "HIGH"
CONFIDENCE_MEDIUM = "MEDIUM"
CONFIDENCE_LOW = "LOW"
CONFIDENCE_UNKNOWN = "UNKNOWN"

PERMISSION_VERIFIED = "VERIFIED"
PERMISSION_RESTRICTED = "RESTRICTED"
PERMISSION_UNKNOWN = "UNKNOWN"
PERMISSION_NOT_APPLICABLE = "NOT_APPLICABLE"


@dataclass
class HeritageRecord:
    """One heritage record.  All fields except record_id are optional."""

    # ── A. Identity ──────────────────────────────────────────────────────────
    record_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    record_type: Optional[str] = None          # inscription, artifact, site, monument …
    title: Optional[str] = None
    alternate_title: Optional[str] = None
    local_name_ta: Optional[str] = None        # Tamil-language name
    source_record_id: Optional[str] = None     # ID as given by the source
    parent_site_id: Optional[str] = None

    # ── B. Historical information ─────────────────────────────────────────────
    language: Optional[str] = None
    script: Optional[str] = None
    dynasty: Optional[str] = None
    ruler_or_person: Optional[str] = None
    historical_period: Optional[str] = None
    date_start: Optional[str] = None           # ISO year or approximate range
    date_end: Optional[str] = None
    date_text_as_published: Optional[str] = None
    dating_method: Optional[str] = None
    historical_context: Optional[str] = None
    description: Optional[str] = None
    inscription_text_original: Optional[str] = None
    transliteration: Optional[str] = None
    translation: Optional[str] = None
    interpretation: Optional[str] = None
    find_context: Optional[str] = None

    # ── C. Geography ─────────────────────────────────────────────────────────
    country: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    taluk: Optional[str] = None
    village_or_town: Optional[str] = None
    site_name: Optional[str] = None
    monument_name: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    location_source: Optional[str] = None      # how coordinates were determined

    # ── D. Archaeological information ─────────────────────────────────────────
    material: Optional[str] = None
    object_type: Optional[str] = None
    archaeological_site: Optional[str] = None
    excavation_season: Optional[str] = None
    excavation_year: Optional[str] = None
    excavation_context: Optional[str] = None
    associated_finds: Optional[str] = None
    museum_or_repository: Optional[str] = None
    accession_number: Optional[str] = None

    # ── E. Provenance and verification ────────────────────────────────────────
    source_url: Optional[str] = None
    source_page_title: Optional[str] = None
    source_organization: Optional[str] = None
    source_access_date: Optional[str] = None
    source_quote_or_evidence: Optional[str] = None
    source_verified: Optional[str] = None      # one of the SOURCE_* constants
    verification_method: Optional[str] = None
    review_required: bool = False
    review_reason: Optional[str] = None
    confidence_level: Optional[str] = None     # one of the CONFIDENCE_* constants
    conflicting_sources: Optional[str] = None
    copyright_status: Optional[str] = None
    license_name: Optional[str] = None
    attribution_text: Optional[str] = None
    reuse_permission_verified: Optional[str] = None  # one of the PERMISSION_* constants

    # ── F. Image metadata ────────────────────────────────────────────────────
    image_source_url: Optional[str] = None
    image_local_path: Optional[str] = None
    image_caption: Optional[str] = None
    image_creator: Optional[str] = None
    image_license: Optional[str] = None
    image_attribution: Optional[str] = None
    image_permission_status: Optional[str] = None
    image_download_status: Optional[str] = None
    image_checksum: Optional[str] = None

    # ── G. Technical metadata ────────────────────────────────────────────────
    scraped_at: Optional[str] = None
    scraper_version: str = "1.0.0"
    extraction_method: Optional[str] = None    # requests+BS4, playwright, manual …
    content_hash: Optional[str] = None         # SHA-256 of the source HTML/text
    duplicate_group_id: Optional[str] = None
    record_status: str = "active"              # active | duplicate | excluded | pending

    # ── Source-specific extras ────────────────────────────────────────────────
    extra: Optional[dict] = field(default_factory=dict)

    def to_dict(self) -> dict:
        d = asdict(self)
        # extra is a nested dict – keep as-is for JSON; flatten for CSV
        return d

    def to_flat_dict(self) -> dict:
        """Flat dict suitable for CSV rows (extra fields stringified)."""
        d = asdict(self)
        extra = d.pop("extra", {}) or {}
        for k, v in extra.items():
            d[f"extra_{k}"] = v
        return d

    @classmethod
    def field_names(cls) -> list[str]:
        import dataclasses
        return [f.name for f in dataclasses.fields(cls)]


@dataclass
class SourceRegistryEntry:
    """One entry in the source registry."""
    source_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    organization: Optional[str] = None
    base_url: Optional[str] = None
    page_title: Optional[str] = None
    description: Optional[str] = None
    access_date: Optional[str] = None
    robots_txt_url: Optional[str] = None
    robots_txt_status: Optional[str] = None   # allowed, disallowed, not_found, error
    crawl_permitted: Optional[bool] = None
    license_info: Optional[str] = None
    reuse_terms: Optional[str] = None
    pagination_type: Optional[str] = None     # query_param, path_param, none
    js_required: Optional[bool] = None
    notes: Optional[str] = None
    records_collected: int = 0
    pages_crawled: int = 0
    last_checked: Optional[str] = None


@dataclass
class ImageManifestEntry:
    """One image candidate."""
    image_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    record_id: Optional[str] = None
    source_url: Optional[str] = None
    caption: Optional[str] = None
    creator: Optional[str] = None
    license: Optional[str] = None
    attribution: Optional[str] = None
    permission_status: Optional[str] = None
    local_path: Optional[str] = None
    download_status: Optional[str] = None     # downloaded, skipped, failed, pending
    checksum: Optional[str] = None
    file_size_bytes: Optional[int] = None
    mime_type: Optional[str] = None
    width_px: Optional[int] = None
    height_px: Optional[int] = None
    discovered_at: Optional[str] = None
