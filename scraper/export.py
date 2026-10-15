"""
export.py – Export validated records to CSV, JSON, and XLSX.
            Also exports source registry, field evidence, and image manifest.
"""

from __future__ import annotations
import csv
import json
from dataclasses import asdict
from pathlib import Path
from typing import Sequence

import pandas as pd

from scraper import config as cfg
from scraper.schema import HeritageRecord, SourceRegistryEntry, ImageManifestEntry
from scraper.utils import log, utc_now


# ── Heritage records ──────────────────────────────────────────────────────────

def export_records(records: list[HeritageRecord]) -> dict[str, int]:
    """
    Export records to CSV, JSON, and XLSX.
    Returns dict of {format: row_count}.
    """
    if not records:
        log.warning("[Export] No records to export.")
        return {"csv": 0, "json": 0, "xlsx": 0}

    counts = {}

    # ── JSON ──
    json_data = [r.to_dict() for r in records]
    cfg.HERITAGE_JSON.parent.mkdir(parents=True, exist_ok=True)
    cfg.HERITAGE_JSON.write_text(
        json.dumps(json_data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    counts["json"] = len(json_data)
    log.info("[Export] JSON written → %s (%d records)", cfg.HERITAGE_JSON, len(json_data))

    # ── CSV ──
    flat_rows = [r.to_flat_dict() for r in records]
    all_keys = []
    seen_keys: set[str] = set()
    for row in flat_rows:
        for k in row:
            if k not in seen_keys:
                all_keys.append(k)
                seen_keys.add(k)

    cfg.HERITAGE_CSV.parent.mkdir(parents=True, exist_ok=True)
    with cfg.HERITAGE_CSV.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=all_keys, extrasaction="ignore")
        writer.writeheader()
        for row in flat_rows:
            # Fill missing keys with empty string
            writer.writerow({k: row.get(k, "") for k in all_keys})
    counts["csv"] = len(flat_rows)
    log.info("[Export] CSV written → %s (%d rows)", cfg.HERITAGE_CSV, len(flat_rows))

    # ── XLSX ──
    try:
        df = pd.DataFrame(flat_rows)
        # Convert dicts/lists in any column to strings for Excel compatibility
        for col in df.columns:
            if df[col].apply(lambda x: isinstance(x, (dict, list))).any():
                df[col] = df[col].astype(str)
        cfg.HERITAGE_XLSX.parent.mkdir(parents=True, exist_ok=True)
        df.to_excel(cfg.HERITAGE_XLSX, index=False, engine="openpyxl")
        counts["xlsx"] = len(df)
        log.info("[Export] XLSX written → %s (%d rows)", cfg.HERITAGE_XLSX, len(df))
    except Exception as exc:
        log.error("[Export] XLSX export failed: %s", exc)
        counts["xlsx"] = 0

    return counts


# ── Source registry ───────────────────────────────────────────────────────────

def export_source_registry(entries: list[SourceRegistryEntry]) -> None:
    if not entries:
        return

    rows = [asdict(e) for e in entries]

    cfg.SOURCE_REG_JSON.parent.mkdir(parents=True, exist_ok=True)
    cfg.SOURCE_REG_JSON.write_text(
        json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    df = pd.DataFrame(rows)
    cfg.SOURCE_REG_CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(cfg.SOURCE_REG_CSV, index=False, encoding="utf-8-sig")
    log.info("[Export] Source registry → %s, %s", cfg.SOURCE_REG_JSON, cfg.SOURCE_REG_CSV)


# ── Field evidence ────────────────────────────────────────────────────────────

def export_field_evidence(records: list[HeritageRecord]) -> None:
    """
    Write one JSONL line per record that has source evidence.
    The evidence line records: record_id, field, value, evidence, verification.
    """
    cfg.FIELD_EVIDENCE.parent.mkdir(parents=True, exist_ok=True)
    evidence_fields = [
        "title", "dynasty", "historical_period", "date_text_as_published",
        "district", "site_name", "description", "inscription_text_original",
    ]
    n = 0
    with cfg.FIELD_EVIDENCE.open("w", encoding="utf-8") as f:
        for rec in records:
            for field in evidence_fields:
                value = getattr(rec, field, None)
                if value:
                    entry = {
                        "record_id": rec.record_id,
                        "field": field,
                        "value": str(value)[:500],
                        "source_url": rec.source_url,
                        "source_verified": rec.source_verified,
                        "confidence": rec.confidence_level,
                        "exported_at": utc_now(),
                    }
                    f.write(json.dumps(entry, ensure_ascii=False) + "\n")
                    n += 1
    log.info("[Export] Field evidence → %s (%d entries)", cfg.FIELD_EVIDENCE, n)


# ── Image manifest ────────────────────────────────────────────────────────────

def export_image_manifest(
    images: list[ImageManifestEntry],
    records: list[HeritageRecord],
) -> None:
    # Also include images discovered via record fields
    extra_images: list[ImageManifestEntry] = []
    existing_urls = {img.source_url for img in images}
    for rec in records:
        if rec.image_source_url and rec.image_source_url not in existing_urls:
            extra_images.append(ImageManifestEntry(
                record_id=rec.record_id,
                source_url=rec.image_source_url,
                caption=rec.image_caption,
                permission_status=rec.image_permission_status,
                download_status=rec.image_download_status,
                checksum=rec.image_checksum,
                discovered_at=utc_now(),
            ))
            existing_urls.add(rec.image_source_url)

    all_images = images + extra_images

    if not all_images:
        log.info("[Export] No images to export.")
        return

    rows = [asdict(img) for img in all_images]
    cfg.IMAGE_MANIFEST_JSON.parent.mkdir(parents=True, exist_ok=True)
    cfg.IMAGE_MANIFEST_JSON.write_text(
        json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    df = pd.DataFrame(rows)
    cfg.IMAGE_MANIFEST_CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(cfg.IMAGE_MANIFEST_CSV, index=False, encoding="utf-8-sig")
    log.info("[Export] Image manifest → %s, %s (%d images)",
             cfg.IMAGE_MANIFEST_JSON, cfg.IMAGE_MANIFEST_CSV, len(all_images))


# ── Quality report ────────────────────────────────────────────────────────────

def write_quality_report(
    quality: dict,
    source_registry: list[SourceRegistryEntry],
    failed_urls_count: int,
) -> None:
    from scraper.config import QUALITY_REPORT, DATASET_SUMMARY

    lines = [
        "# AI Heritage Explorer – Data Quality Report",
        f"\n**Generated:** {utc_now()}\n",
        "---\n",
        "## Summary Statistics\n",
        f"| Metric | Count |",
        f"|--------|-------|",
    ]
    for k, v in quality.items():
        if isinstance(v, dict):
            continue
        lines.append(f"| {k.replace('_', ' ').title()} | {v} |")

    lines += ["\n## Records by Type\n", "| Type | Count |", "|------|-------|"]
    for t, c in quality.get("by_record_type", {}).items():
        lines.append(f"| {t} | {c} |")

    lines += ["\n## Records by Source Organisation\n", "| Organisation | Count |", "|---|---|"]
    for org, c in quality.get("by_source_org", {}).items():
        lines.append(f"| {org} | {c} |")

    lines += ["\n## Sources Inspected\n"]
    for entry in source_registry:
        lines.append(f"- **{entry.organization}** – {entry.base_url} "
                     f"(crawl_permitted={entry.crawl_permitted}, "
                     f"records_collected={entry.records_collected})")

    lines += [
        "\n## Failed URL Count\n",
        f"- Failed URLs logged: **{failed_urls_count}**",
        f"\n(See `logs/failed_urls.jsonl` for details.)",
        "\n\n---\n",
        "> [!WARNING]",
        "> All records require expert review before use in publications.",
        "> Confidence levels indicate automated extraction reliability, not historical proof.",
    ]

    QUALITY_REPORT.parent.mkdir(parents=True, exist_ok=True)
    QUALITY_REPORT.write_text("\n".join(lines), encoding="utf-8")
    log.info("[Export] Quality report → %s", QUALITY_REPORT)

    # Dataset summary JSON
    summary = {
        **quality,
        "generated_at": utc_now(),
        "sources_inspected": len(source_registry),
        "failed_urls": failed_urls_count,
        "output_files": {
            "heritage_csv":     str(cfg.HERITAGE_CSV),
            "heritage_json":    str(cfg.HERITAGE_JSON),
            "heritage_xlsx":    str(cfg.HERITAGE_XLSX),
            "source_registry":  str(cfg.SOURCE_REG_JSON),
            "image_manifest":   str(cfg.IMAGE_MANIFEST_JSON),
            "quality_report":   str(QUALITY_REPORT),
        },
    }
    DATASET_SUMMARY.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    log.info("[Export] Dataset summary → %s", DATASET_SUMMARY)
