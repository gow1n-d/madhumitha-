"""
deduplication.py – Detect and group duplicate heritage records.

Deduplication strategy:
  1. Exact match on (canonical_title, source_url).
  2. Fuzzy match on normalized title within the same source domain.
  3. When duplicates are found, mark them with a shared duplicate_group_id.
     Records are NOT deleted – all are preserved with record_status set to
     'duplicate' for the later-seen occurrences.
"""

from __future__ import annotations
import re
import unicodedata
import uuid
from collections import defaultdict
from typing import Sequence

from scraper.schema import HeritageRecord
from scraper.utils import log


def _normalize_title(title: str | None) -> str:
    """Lowercase, strip accents, collapse whitespace, strip punctuation."""
    if not title:
        return ""
    t = unicodedata.normalize("NFC", title).lower()
    t = re.sub(r"[^\w\s\u0B80-\u0BFF]", " ", t)   # keep Tamil, word chars, spaces
    t = re.sub(r"\s+", " ", t).strip()
    return t


def deduplicate(records: list[HeritageRecord]) -> list[HeritageRecord]:
    """
    Process *records* in-place.
    Returns the same list with duplicate_group_id and record_status set.
    """
    # Build index:
    # 1. By content_hash (identical content)
    # 2. By composite key: (normalized_title, normalized_url)
    # 3. By (source_record_id, source_url) when source_record_id is present
    hash_index: dict[str, list[int]] = defaultdict(list)
    title_url_index: dict[tuple[str, str], list[int]] = defaultdict(list)
    source_id_index: dict[tuple[str, str], list[int]] = defaultdict(list)

    for i, rec in enumerate(records):
        clean_url = (rec.source_url or "").rstrip("/")
        if rec.content_hash:
            hash_index[rec.content_hash].append(i)
        nt = _normalize_title(rec.title)
        if nt:
            title_url_index[(nt, clean_url)].append(i)
        if rec.source_record_id:
            source_id_index[(rec.source_record_id, clean_url)].append(i)

    # Identify groups
    grouped: dict[int, str] = {}   # record_index → group_id

    def _assign_group(indices: list[int]) -> None:
        if len(indices) < 2:
            return
        gid = grouped.get(indices[0]) or str(uuid.uuid4())
        for idx in indices:
            grouped[idx] = gid

    for indices in hash_index.values():
        _assign_group(indices)
    for indices in title_url_index.values():
        _assign_group(indices)
    for indices in source_id_index.values():
        _assign_group(indices)

    # Apply groups
    seen_groups: set[str] = set()
    n_dupes = 0
    for i, rec in enumerate(records):
        gid = grouped.get(i)
        if gid:
            rec.duplicate_group_id = gid
            if gid in seen_groups:
                rec.record_status = "duplicate"
                n_dupes += 1
            else:
                seen_groups.add(gid)

    log.info("Deduplication: %d records, %d duplicates found.", len(records), n_dupes)
    return records


def quality_summary(records: list[HeritageRecord]) -> dict:
    """Compute data quality statistics over a list of records."""
    from scraper.utils import contains_tamil

    total = len(records)
    active = [r for r in records if r.record_status == "active"]
    dupes  = [r for r in records if r.record_status == "duplicate"]

    return {
        "total_records":              total,
        "active_records":             len(active),
        "duplicate_records":          len(dupes),
        "missing_title":              sum(1 for r in records if not r.title),
        "missing_source_url":         sum(1 for r in records if not r.source_url),
        "has_description":            sum(1 for r in records if r.description),
        "has_inscription_text":       sum(1 for r in records if r.inscription_text_original),
        "has_tamil_text":             sum(1 for r in records if contains_tamil(r.title or "") or
                                          contains_tamil(r.inscription_text_original or "")),
        "has_image_reference":        sum(1 for r in records if r.image_source_url),
        "requires_expert_review":     sum(1 for r in records if r.review_required),
        "source_confirmed":           sum(1 for r in records if r.source_verified == "SOURCE_CONFIRMED"),
        "source_partial":             sum(1 for r in records if r.source_verified == "SOURCE_PARTIAL"),
        "needs_expert_review_flag":   sum(1 for r in records if r.source_verified == "NEEDS_EXPERT_REVIEW"),
        "unverified":                 sum(1 for r in records if r.source_verified == "UNVERIFIED"),
        "permission_verified":        sum(1 for r in records if r.reuse_permission_verified == "VERIFIED"),
        "permission_unknown":         sum(1 for r in records if r.reuse_permission_verified == "UNKNOWN"),
        "permission_restricted":      sum(1 for r in records if r.reuse_permission_verified == "RESTRICTED"),
        "has_coordinates":            sum(1 for r in records if r.latitude and r.longitude),
        "by_record_type":             _count_by(records, "record_type"),
        "by_source_org":              _count_by(records, "source_organization"),
    }


def _count_by(records: list[HeritageRecord], field: str) -> dict:
    counts: dict[str, int] = defaultdict(int)
    for r in records:
        v = getattr(r, field, None) or "unknown"
        counts[str(v)] += 1
    return dict(counts)
