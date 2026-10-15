"""
import_to_sqlite.py – Optional: import validated JSON records into SQLite.

Usage:
    python import_to_sqlite.py                    # import heritage_records.json
    python import_to_sqlite.py --db path/to.db    # custom DB path
    python import_to_sqlite.py --clear            # drop and recreate tables first

Design:
  - Idempotent: will not insert duplicate records (keyed on record_id).
  - Safe repeated runs: uses INSERT OR IGNORE.
  - Preserves Tamil Unicode (SQLite stores UTF-8 natively).
  - Never overwrites a reviewed record without explicit --force flag.
  - Source evidence and image metadata linked by foreign key.
"""

from __future__ import annotations
import argparse
import json
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

HERITAGE_JSON  = BASE_DIR / "data" / "heritage_records.json"
SOURCE_REG_JSON= BASE_DIR / "data" / "source_registry.json"
IMAGE_JSON     = BASE_DIR / "data" / "image_manifest.json"
DEFAULT_DB     = BASE_DIR / "db" / "heritage.db"

DDL = """
CREATE TABLE IF NOT EXISTS heritage_records (
    record_id               TEXT PRIMARY KEY,
    record_type             TEXT,
    title                   TEXT,
    alternate_title         TEXT,
    local_name_ta           TEXT,
    source_record_id        TEXT,
    parent_site_id          TEXT,
    language                TEXT,
    script                  TEXT,
    dynasty                 TEXT,
    ruler_or_person         TEXT,
    historical_period       TEXT,
    date_start              TEXT,
    date_end                TEXT,
    date_text_as_published  TEXT,
    dating_method           TEXT,
    historical_context      TEXT,
    description             TEXT,
    inscription_text_original TEXT,
    transliteration         TEXT,
    translation             TEXT,
    interpretation          TEXT,
    find_context            TEXT,
    country                 TEXT,
    state                   TEXT,
    district                TEXT,
    taluk                   TEXT,
    village_or_town         TEXT,
    site_name               TEXT,
    monument_name           TEXT,
    latitude                REAL,
    longitude               REAL,
    location_source         TEXT,
    material                TEXT,
    object_type             TEXT,
    archaeological_site     TEXT,
    excavation_season       TEXT,
    excavation_year         TEXT,
    excavation_context      TEXT,
    associated_finds        TEXT,
    museum_or_repository    TEXT,
    accession_number        TEXT,
    source_url              TEXT,
    source_page_title       TEXT,
    source_organization     TEXT,
    source_access_date      TEXT,
    source_quote_or_evidence TEXT,
    source_verified         TEXT,
    verification_method     TEXT,
    review_required         INTEGER DEFAULT 0,
    review_reason           TEXT,
    confidence_level        TEXT,
    conflicting_sources     TEXT,
    copyright_status        TEXT,
    license_name            TEXT,
    attribution_text        TEXT,
    reuse_permission_verified TEXT,
    image_source_url        TEXT,
    image_local_path        TEXT,
    image_caption           TEXT,
    image_creator           TEXT,
    image_license           TEXT,
    image_attribution       TEXT,
    image_permission_status TEXT,
    image_download_status   TEXT,
    image_checksum          TEXT,
    scraped_at              TEXT,
    scraper_version         TEXT,
    extraction_method       TEXT,
    content_hash            TEXT,
    duplicate_group_id      TEXT,
    record_status           TEXT DEFAULT 'active',
    extra_json              TEXT
);

CREATE TABLE IF NOT EXISTS source_registry (
    source_id               TEXT PRIMARY KEY,
    organization            TEXT,
    base_url                TEXT,
    page_title              TEXT,
    description             TEXT,
    access_date             TEXT,
    robots_txt_url          TEXT,
    robots_txt_status       TEXT,
    crawl_permitted         INTEGER,
    license_info            TEXT,
    reuse_terms             TEXT,
    pagination_type         TEXT,
    js_required             INTEGER,
    notes                   TEXT,
    records_collected       INTEGER DEFAULT 0,
    pages_crawled           INTEGER DEFAULT 0,
    last_checked            TEXT
);

CREATE TABLE IF NOT EXISTS image_manifest (
    image_id                TEXT PRIMARY KEY,
    record_id               TEXT REFERENCES heritage_records(record_id),
    source_url              TEXT,
    caption                 TEXT,
    creator                 TEXT,
    license                 TEXT,
    attribution             TEXT,
    permission_status       TEXT,
    local_path              TEXT,
    download_status         TEXT,
    checksum                TEXT,
    file_size_bytes         INTEGER,
    mime_type               TEXT,
    width_px                INTEGER,
    height_px               INTEGER,
    discovered_at           TEXT
);

CREATE INDEX IF NOT EXISTS idx_records_title   ON heritage_records(title);
CREATE INDEX IF NOT EXISTS idx_records_dynasty ON heritage_records(dynasty);
CREATE INDEX IF NOT EXISTS idx_records_district ON heritage_records(district);
CREATE INDEX IF NOT EXISTS idx_records_status  ON heritage_records(record_status);

CREATE VIRTUAL TABLE IF NOT EXISTS heritage_records_fts USING fts5(
    record_id UNINDEXED,
    title,
    description,
    dynasty,
    ruler_or_person,
    district,
    state,
    language,
    script,
    historical_period,
    tokenize='unicode61'
);
"""


def _val(row: dict, key: str):
    v = row.get(key)
    if isinstance(v, bool):
        return int(v)
    if isinstance(v, dict):
        return json.dumps(v, ensure_ascii=False)
    return v


def import_records(db_path: Path, clear: bool = False, force: bool = False) -> dict:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(db_path))
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA foreign_keys=ON")
    con.executescript(DDL)

    if clear:
        con.executescript("""
            DELETE FROM image_manifest;
            DELETE FROM heritage_records;
            DELETE FROM heritage_records_fts;
            DELETE FROM source_registry;
        """)
        print("Tables cleared.")

    stats = {"records_inserted": 0, "records_skipped": 0,
             "sources_inserted": 0, "images_inserted": 0}

    # ── Heritage records ──
    if HERITAGE_JSON.exists():
        data = json.loads(HERITAGE_JSON.read_text(encoding="utf-8"))
        for row in data:
            # Check if exists and is reviewed
            existing = con.execute(
                "SELECT review_required FROM heritage_records WHERE record_id=?",
                (row.get("record_id"),)
            ).fetchone()
            if existing and not force:
                stats["records_skipped"] += 1
                continue

            extra = row.pop("extra", {}) or {}
            cols = [
                "record_id", "record_type", "title", "alternate_title", "local_name_ta",
                "source_record_id", "parent_site_id", "language", "script", "dynasty",
                "ruler_or_person", "historical_period", "date_start", "date_end",
                "date_text_as_published", "dating_method", "historical_context",
                "description", "inscription_text_original", "transliteration",
                "translation", "interpretation", "find_context",
                "country", "state", "district", "taluk", "village_or_town",
                "site_name", "monument_name", "latitude", "longitude", "location_source",
                "material", "object_type", "archaeological_site", "excavation_season",
                "excavation_year", "excavation_context", "associated_finds",
                "museum_or_repository", "accession_number",
                "source_url", "source_page_title", "source_organization", "source_access_date",
                "source_quote_or_evidence", "source_verified", "verification_method",
                "review_required", "review_reason", "confidence_level", "conflicting_sources",
                "copyright_status", "license_name", "attribution_text", "reuse_permission_verified",
                "image_source_url", "image_local_path", "image_caption", "image_creator",
                "image_license", "image_attribution", "image_permission_status",
                "image_download_status", "image_checksum",
                "scraped_at", "scraper_version", "extraction_method",
                "content_hash", "duplicate_group_id", "record_status",
            ]
            vals = [_val(row, c) for c in cols]
            vals.append(json.dumps(extra, ensure_ascii=False) if extra else None)
            placeholders = ",".join("?" * (len(cols) + 1))
            con.execute(
                f"INSERT OR IGNORE INTO heritage_records({','.join(cols)},extra_json) "
                f"VALUES({placeholders})",
                vals,
            )
            con.execute(
                "INSERT INTO heritage_records_fts(record_id, title, description, dynasty, ruler_or_person, district, state, language, script, historical_period) "
                "VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    row.get("record_id"),
                    row.get("title"),
                    row.get("description"),
                    row.get("dynasty"),
                    row.get("ruler_or_person"),
                    row.get("district"),
                    row.get("state"),
                    row.get("language"),
                    row.get("script"),
                    row.get("historical_period"),
                )
            )
            stats["records_inserted"] += 1
        con.commit()
        print(f"Heritage records: inserted={stats['records_inserted']}, skipped={stats['records_skipped']}")
    else:
        print(f"WARNING: {HERITAGE_JSON} not found – skipping records import.")

    # ── Source registry ──
    if SOURCE_REG_JSON.exists():
        for row in json.loads(SOURCE_REG_JSON.read_text(encoding="utf-8")):
            con.execute(
                "INSERT OR IGNORE INTO source_registry VALUES "
                "(:source_id,:organization,:base_url,:page_title,:description,"
                ":access_date,:robots_txt_url,:robots_txt_status,:crawl_permitted,"
                ":license_info,:reuse_terms,:pagination_type,:js_required,:notes,"
                ":records_collected,:pages_crawled,:last_checked)",
                {k: _val(row, k) for k in [
                    "source_id","organization","base_url","page_title","description",
                    "access_date","robots_txt_url","robots_txt_status","crawl_permitted",
                    "license_info","reuse_terms","pagination_type","js_required","notes",
                    "records_collected","pages_crawled","last_checked",
                ]},
            )
            stats["sources_inserted"] += 1
        con.commit()

    # ── Image manifest ──
    if IMAGE_JSON.exists():
        for row in json.loads(IMAGE_JSON.read_text(encoding="utf-8")):
            con.execute(
                "INSERT OR IGNORE INTO image_manifest VALUES "
                "(:image_id,:record_id,:source_url,:caption,:creator,:license,"
                ":attribution,:permission_status,:local_path,:download_status,"
                ":checksum,:file_size_bytes,:mime_type,:width_px,:height_px,:discovered_at)",
                {k: _val(row, k) for k in [
                    "image_id","record_id","source_url","caption","creator","license",
                    "attribution","permission_status","local_path","download_status",
                    "checksum","file_size_bytes","mime_type","width_px","height_px","discovered_at",
                ]},
            )
            stats["images_inserted"] += 1
        con.commit()

    con.close()
    return stats


def main():
    parser = argparse.ArgumentParser(description="Import heritage data into SQLite.")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB, help="Path to SQLite database.")
    parser.add_argument("--clear", action="store_true", help="Drop all records before import.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing records.")
    args = parser.parse_args()

    print(f"Importing into: {args.db}")
    stats = import_records(args.db, clear=args.clear, force=args.force)
    print(f"Done: {stats}")


if __name__ == "__main__":
    main()
